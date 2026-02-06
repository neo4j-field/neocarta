from neo4j import Driver, RoutingControl


def create_vector_index(
    neo4j_driver: Driver,
    node_label: str,
    dimensions: int = 768,
    database_name: str = "neo4j",
) -> None:
    """
    Create a vector index according to the provided configuration.

    Parameters
    ----------
    neo4j_driver: Driver
        The Neo4j driver to use.
    node_label: str
        The label of the node to create a vector index for. Must be one of: Database, Schema, Table, Column.
    dimensions: int
        The dimensions of the vector index. Must be an integer greater than 0.
    database_name: str
        The name of the database to create a vector index for.

    Returns
    -------
    dict
        The summary of the vector index created.
    """

    assert node_label in ["Database", "Schema", "Table", "Column"], (
        "Node label must be one of: Database, Schema, Table, Column"
    )
    assert dimensions > 0, "Dimensions must be an integer greater than 0"

    vector_index_query = f"""
CREATE VECTOR INDEX {node_label.lower() + "_vector_index"} IF NOT EXISTS
    FOR (n:{node_label})
    ON n.embedding
    OPTIONS {{ 
        indexConfig: {{
            `vector.dimensions`: {dimensions},
            `vector.similarity_function`: 'cosine'
        }}
    }}
"""
    _, summary, _ = neo4j_driver.execute_query(
        query_=vector_index_query,
        routing_=RoutingControl.WRITE,
        database_=database_name,
    )
    return summary.counters.__dict__
