"""
Functions for reading metadata graph from Neo4j and creating embeddings from description properties.
"""

from neo4j import Driver, RoutingControl, GraphDatabase
import pandas as pd
from openai import AsyncOpenAI
import asyncio
from math import ceil
from typing import Any
import os
from dotenv import load_dotenv

def get_nodes_to_embed(neo4j_driver: Driver, node_label: str, min_length: int = 20) -> pd.DataFrame:
    """
    Get the nodes to embed.

    Parameters
    ----------
    neo4j_driver: Driver
        The Neo4j driver to use.
    node_label: str
        The label of the node to embed. Must be one of: Database, Table, Column.
    min_length: int
        The minimum length of the description to embed. Must be greater than 0.

    Returns
    -------
    pd.DataFrame
        The nodes to embed.
        - id: The id of the node.
        - node_label: The label of the node.
        - description: The description of the node.
    """

    assert node_label in ["Database", "Table", "Column"], "Node label must be one of: Database, Table, Column"
    assert min_length > 0, "Minimum length must be greater than 0"

    query = f"""
MATCH (n:{node_label})
WHERE n.description IS NOT NULL
    AND n.embedding IS NULL
    AND size(n.description) > 0
RETURN n.id as id, 
    labels(n)[0] as node_label, 
    n.description as description
"""
    results = neo4j_driver.execute_query(query_=query, 
        parameters_={'min_length': min_length}, 
        routing_=RoutingControl.READ, 
        result_transformer_=lambda x: x.data())

    return pd.DataFrame(results)

async def _create_single_embedding(embedding_client: AsyncOpenAI, node_id: str, node_label: str, node_description: str, failed_cache: list[tuple[str, str, str]]) -> list[float]:
    """
    Create embedding for a single node's description.

    Parameters  
    ----------
    embedding_client: AsyncOpenAI
        The embedding client to use.
    node_id : str
        The id of the node.
    node_label : str
        The label of the node.
    node_description : str
        The description of the node.
    failed_cache : list[tuple[str, str, str]]
        A list of tuples, where the first element is the node id, the second element is the node label, and the third element is the node description.
        This is used to log failed embeddings across batches.

    Returns
    -------
    list[float]
        The embedding for the node description.
    """

    try:
        response = await embedding_client.embeddings.create(
            model="text-embedding-3-small",
            input=node_description,
            encoding_format="float",
            dimensions=768, # must be the same dimensions as the vector index
        )
        return response.data[0].embedding
    except Exception as e:
        print(e)
        failed_cache.append((node_id, node_label, node_description))
        return None
    
async def create_embeddings(embedding_client: AsyncOpenAI, node_to_embed_dataframe: pd.DataFrame, batch_size: int = 100) -> list[tuple[str, list[Any]]]:
    """
    Create embeddings for a Pandas DataFrame of nodes to embed.

    Parameters
    ----------
    embedding_client: AsyncOpenAI
        The embedding client to use.
    node_to_embed_dataframe : pd.DataFrame
        A Pandas DataFrame where each row represents a node to embed.
        Has columns `id`, `node_label`, and `description`.
    batch_size : int
        The number of nodes to process in each batch.

    Returns
    -------
    list[tuple[str, list[float]]]
        A list of tuples, where the first element is the node id and the second element is the embedding for the node description.
    """

    
    async def _create_embeddings_for_batch(batch: pd.DataFrame, failed_cache: list[tuple[str, str]]) -> list[tuple[str, list[dict[str, Any]]]]:
        """
        Create embeddings for a batch of node descriptions to embed.
        Failed extractions are maintained in the `failed_cache` list that is passed to the embedding creation function.

        Parameters
        ----------
        batch : pd.DataFrame
            A Pandas DataFrame where each row represents a node to embed.
            Has columns `id`, `node_label`, and `description`.
        failed_cache : list[tuple[str, str]]
            A list of tuples, where the first element is the node id, the second element is the node label, and the third element is the node description.
            This is used to log failed embeddings across batches.

        Returns
        -------
        list[tuple[str, list[dict[str, Any]]]]
            A list of tuples, where the first element is the node id and the second element is the embedding for the node description.
        """
        
        # Create tasks for all nodes in the batch
        # order is maintained
        tasks = [_create_single_embedding(embedding_client, row["id"], row['node_label'], row['description'], failed_cache) for _, row in batch.iterrows()]
        # Execute all tasks concurrently
        embedding_results = await asyncio.gather(*tasks)

        # filter results to only include non-None values
        embedding_results = [(id, embedding) for id, embedding in zip(batch["id"], embedding_results) if embedding is not None]

        return embedding_results

    
    async def _create_embeddings_in_batches(nodes_dataframe: pd.DataFrame, batch_size: int) -> tuple[list[tuple[str, list[Any]]], list[tuple[str, str, str]]]:
        """
        Create embeddings for a Pandas DataFrame of text chunks in batches.

        Parameters
        ----------
        nodes_dataframe : pd.DataFrame
            A Pandas DataFrame where each row represents a node.
            Has columns `id`, `node_label`, and `description`.
        batch_size : int
            The number of nodes to process in each batch.

        Returns
        -------
        tuple[list[tuple[str, list[Any]]], list[tuple[str, str, str]]]
            A tuple of two lists. The first list contains tuples of node id and description embedding for the node description.
            The second list contains tuples of node id and node label and node description that failed to be processed.
        """

        results = list()
        failed_cache: list[tuple[str, str, str]] = list() # [(node_id, node_label, node_description), ...]
        for batch_idx, i in enumerate(range(0, len(nodes_dataframe), batch_size)):
            print(f"Processing batch {batch_idx+1} of {ceil(len(nodes_dataframe)/(batch_size))}  \n", end="\r") 
            if i + batch_size >= len(nodes_dataframe):
                batch = nodes_dataframe.iloc[i:]
            else:
                batch = nodes_dataframe.iloc[i:i+batch_size]
            batch_results = await _create_embeddings_for_batch(batch, failed_cache)

            # Add extracted records to the results list
            results.extend(batch_results)

        return results, failed_cache

    # first pass through chunks
    results, failed = await _create_embeddings_in_batches(node_to_embed_dataframe, batch_size)
    print(f"Successful chunks : {len(results)}")
    print(f"Failed chunks     : {len(failed)}")
    print("--------------------------------")
    print("Retrying failed nodes...")

    # retry failed chunks once
    retry_df = pd.DataFrame(failed, columns=["id", "node_label", "node_description"])
    retry_results, failed = await _create_embeddings_in_batches(retry_df, batch_size)
    print(f"Successful retries : {len(retry_results)}")
    print(f"Failed retries     : {len(failed)}")

    print("--------------------------------")
    print(f"Overall Success Rate : {round(len(results + retry_results) / (len(node_to_embed_dataframe) or 1) * 100, 2)}%")

    return results + retry_results


def write_embeddings_to_nodes(df: pd.DataFrame, node_label: str, neo4j_driver: Driver) -> None:
    """
    Write embeddings to nodes.

    Parameters
    ----------
    df : pd.DataFrame
        A Pandas DataFrame where each row represents a node.
        Has columns `id`, `node_label`, and `embedding`.
    node_label: str
        The label of the node to write embeddings to. Must be one of: Database, Table, Column.
    neo4j_driver: Driver
        The Neo4j driver to use.
    """

    assert node_label in ["Database", "Table", "Column"], "Node label must be one of: Database, Table, Column"

    query = f"""
    UNWIND $rows as row
    MERGE (n:{node_label} {{id: row.id}})
    SET n.embedding = row.embedding
    """

    _, summary, _ = neo4j_driver.execute_query(
        query_=query, 
        parameters_={
            "rows": df.to_dict(orient="records")
        },
        routing_=RoutingControl.WRITE)

    return summary.counters.__dict__

async def main():
    load_dotenv()
    # create neo4j driver
    neo4j_driver = GraphDatabase.driver(
        uri=os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
    )

    # create embedding client
    embedding_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # get nodes to embed
    database_nodes = get_nodes_to_embed(neo4j_driver, "Database", 20)
    table_nodes = get_nodes_to_embed(neo4j_driver, "Table", 20)
    column_nodes = get_nodes_to_embed(neo4j_driver, "Column", 20)

    # create embeddings asyncronously
    database_embeddings = await create_embeddings(embedding_client, database_nodes, 100)
    table_embeddings = await create_embeddings(embedding_client, table_nodes, 100)
    column_embeddings = await create_embeddings(embedding_client, column_nodes, 100)

    # write embeddings to nodes
    print(write_embeddings_to_nodes(pd.DataFrame(database_embeddings, columns=["id", "embedding"]), "Database", neo4j_driver))
    print(write_embeddings_to_nodes(pd.DataFrame(table_embeddings, columns=["id", "embedding"]), "Table", neo4j_driver))
    print(write_embeddings_to_nodes(pd.DataFrame(column_embeddings, columns=["id", "embedding"]), "Column", neo4j_driver))

    neo4j_driver.close()

if __name__ == "__main__":
    asyncio.run(main())