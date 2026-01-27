from connectors.bigquery.extract import (
    extract_database_info,
    extract_table_info,
    extract_column_info,
    extract_column_references_info,
    extract_column_unique_values,
)
from connectors.bigquery.transform import (
    transform_to_database_nodes,
    transform_to_table_nodes,
    transform_to_column_nodes,
    transform_to_contains_table_relationships,
    transform_to_has_column_relationships,
    transform_to_references_relationships,
    transform_to_value_nodes,
    transform_to_has_value_relationships,
)
from connectors.load import (
    load_database_nodes,
    load_table_nodes,
    load_column_nodes,
    load_value_nodes,
    load_contains_table_relationships,
    load_has_column_relationships,
    load_references_relationships,
    load_has_value_relationships,
)
from neo4j import Driver
from google.cloud import bigquery
import pandas as pd


def bigquery_workflow(
    client: bigquery.Client,
    project_id: str,
    dataset_id: str,
    neo4j_driver: Driver,
    database_name: str = "neo4j",
) -> None:
    """
    A workflow for extracting, transforming, and loading BigQuery data into Neo4j.

    Parameters
    ----------
    client: bigquery.Client
        The BigQuery client.
    project_id: str
        The project ID.
    dataset_id: str
        The dataset ID.
    neo4j_driver: Driver
        The Neo4j driver used to load the data into Neo4j.
    database_name: str
        The name of the database to write data to.

    Returns
    -------
    None
        The workflow runs and loads the data into Neo4j.
    """

    database_info = extract_database_info(client, project_id, dataset_id)
    table_info = extract_table_info(client, project_id, dataset_id)
    column_info = extract_column_info(client, project_id, dataset_id)
    column_references_info = extract_column_references_info(
        client, project_id, dataset_id
    )

    # iterate over each table and batch of columns to extract unique values
    # TODO: make column batch size configurable
    value_info = pd.DataFrame()
    for table_name in table_info["table_name"].unique():
        column_names = column_info[column_info["table_name"] == table_name][
            "column_name"
        ].unique()
        value_info = pd.concat(
            [
                value_info,
                extract_column_unique_values(
                    client, project_id, dataset_id, table_name, column_names
                ),
            ]
        )

    # format metadata into core data model
    database_nodes = transform_to_database_nodes(database_info)
    table_nodes = transform_to_table_nodes(table_info)
    column_nodes = transform_to_column_nodes(column_info)
    value_nodes = transform_to_value_nodes(value_info)

    contains_table_relationships = transform_to_contains_table_relationships(table_info)
    has_column_relationships = transform_to_has_column_relationships(column_info)
    references_relationships = transform_to_references_relationships(
        column_references_info
    )
    has_value_relationships = transform_to_has_value_relationships(value_info)

    # load metadata into neo4j
    print(load_database_nodes(database_nodes, neo4j_driver, database_name))
    print(load_table_nodes(table_nodes, neo4j_driver, database_name))
    print(load_column_nodes(column_nodes, neo4j_driver, database_name))
    print(load_value_nodes(value_nodes, neo4j_driver, database_name))
    print(
        load_contains_table_relationships(
            contains_table_relationships, neo4j_driver, database_name
        )
    )
    print(
        load_has_column_relationships(
            has_column_relationships, neo4j_driver, database_name
        )
    )
    print(
        load_references_relationships(
            references_relationships, neo4j_driver, database_name
        )
    )
    print(
        load_has_value_relationships(
            has_value_relationships, neo4j_driver, database_name
        )
    )
