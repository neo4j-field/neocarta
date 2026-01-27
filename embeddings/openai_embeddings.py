"""
Functions for creating OpenAI embeddings.
"""

from openai import AsyncOpenAI
import pandas as pd
from embeddings.utils import (
    create_embeddings_in_batches,
    get_nodes_to_embed,
    write_embeddings_to_graph,
)
from neo4j import Driver
from data_model.indexes import create_vector_index
from functools import partial
from typing import Optional


async def _create_openai_embedding(
    embedding_client: AsyncOpenAI,
    embedding_model: str,
    dimensions: int,
    description: str,
) -> Optional[list[float]]:
    """
    Create embedding for a single node's description.
    If embedding creation fails, return None.

    Parameters
    ----------
    embedding_client: AsyncOpenAI
        The embedding client to use.
    embedding_model: str
        The embedding model name to use. For example: text-embedding-3-small.
    dimensions: int
        The dimensions of the vector index. Must be an integer greater than 0.
    description: str
        The description of the node.

    Returns
    -------
    Optional[list[float]]
        The embedding for the node description.
        If embedding creation fails, return None.
    """

    try:
        response = await embedding_client.embeddings.create(
            model=embedding_model,
            input=description,
            encoding_format="float",
            dimensions=dimensions,
        )
        return response.data[0].embedding
    except Exception as e:
        print(e)
        return None


async def create_embeddings(
    embedding_client: AsyncOpenAI,
    embedding_model: str,
    dimensions: int,
    node_to_embed_dataframe: pd.DataFrame,
    batch_size: int = 100,
) -> pd.DataFrame:
    """
    Create embeddings for a Pandas DataFrame of nodes to embed.

    Parameters
    ----------
    embedding_client: AsyncOpenAI
        The embedding client to use.
    embedding_model: str
        The embedding model name to use. For example: text-embedding-3-small.
    dimensions: int
        The dimensions of the vector index. Must be an integer greater than 0.
    node_to_embed_dataframe : pd.DataFrame
        A Pandas DataFrame where each row represents a node to embed.
        Has columns `id`, `node_label`, and `description`.
    batch_size : int
        The number of nodes to process in each batch.

    Returns
    -------
    pd.DataFrame
        A Pandas DataFrame where each row represents a node.
        Has columns `id`, and `embedding`.
    """

    embedding_fn = partial(
        _create_openai_embedding,
        embedding_client=embedding_client,
        embedding_model=embedding_model,
        dimensions=dimensions,
    )
    results = await create_embeddings_in_batches(
        embedding_fn, node_to_embed_dataframe, batch_size
    )
    print(f"Successful Embeddings : {len(results)}")
    return pd.DataFrame(results, columns=["id", "embedding"])


async def openai_embeddings_workflow(
    neo4j_driver: Driver,
    embedding_client: AsyncOpenAI,
    embedding_model: str = "text-embedding-3-small",
    dimensions: int = 768,
    node_labels: list[str] = ["Database", "Table", "Column"],
    database_name: str = "neo4j",
) -> None:
    """
    This workflow
    * Gathers nodes from the Neo4j database that are missing embeddings
    * Creates embeddings of the description fields on found nodes
    * Ingests embeddings into the Neo4j database

    Parameters
    ----------
    neo4j_driver: Driver
        The Neo4j driver to use.
    embedding_client: AsyncOpenAI
        The embedding client to use.
    embedding_model: str
        The embedding model name to use. For example: text-embedding-3-small.
    dimensions: int
        The dimensions of the vector index. Must be an integer greater than 0.
    node_labels: list[str]
        The labels of the nodes to embed. Labels must be one of: Database, Table, Column.
    database_name: str
        The name of the database to write embeddings to.
    """
    assert all(label in ["Database", "Table", "Column"] for label in node_labels), (
        "Node labels must be one of: Database, Table, Column"
    )

    for label in node_labels:
        print(f"Processing {label} nodes...")
        print("--------------------------------")
        # create vector index, if it doesn't exist
        create_vector_index(neo4j_driver, label, dimensions, database_name)
        # get nodes to embed
        nodes_to_embed = get_nodes_to_embed(neo4j_driver, label, 20, database_name)
        # create embeddings
        embeddings = await create_embeddings(
            embedding_client, embedding_model, dimensions, nodes_to_embed, 100
        )
        if len(embeddings) > 0:
            # ingest embeddings into the Neo4j database
            print(
                write_embeddings_to_graph(
                    embeddings, label, neo4j_driver, database_name
                )
            )
        else:
            print(f"No embeddings found for {label} nodes")

    neo4j_driver.close()
