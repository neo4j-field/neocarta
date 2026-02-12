"""Dataplex ETL workflow for extracting, transforming, and loading metadata into Neo4j."""

from typing import Optional

import pandas as pd
from google.cloud import dataplex_v1
from neo4j import Driver

from connectors.dataplex.extract import (
    extract_dataset_table_ids,
    extract_bigquery_metadata_info,
    extract_glossary_info,
)
from connectors.dataplex.transform import (
    transform_to_database_nodes,
    transform_to_schema_nodes,
    transform_to_table_nodes,
    transform_to_column_nodes,
    transform_to_glossary_nodes,
    transform_to_category_nodes,
    transform_to_business_term_nodes,
    transform_to_has_schema_relationships,
    transform_to_has_table_relationships,
    transform_to_has_column_relationships,
    transform_to_has_category_relationships,
    transform_to_has_business_term_relationships,
)
from connectors.load import (
    load_database_nodes,
    load_schema_nodes,
    load_table_nodes,
    load_column_nodes,
    load_glossary_nodes,
    load_category_nodes,
    load_business_term_nodes,
    load_has_schema_relationships,
    load_has_table_relationships,
    load_has_column_relationships,
    load_has_category_relationships,
    load_has_business_term_relationships,
)


def dataplex_workflow(
    catalog_client: dataplex_v1.CatalogServiceClient,
    glossary_client: dataplex_v1.BusinessGlossaryServiceClient,
    project_id: str,
    project_number: str,
    dataplex_location: str,
    dataset_id: str,
    neo4j_driver: Driver,
    table_ids: Optional[list[str]] = None,
    database_name: str = "neo4j",
    include_schema: bool = True,
    include_glossary: bool = True,
) -> None:
    """
    A workflow for extracting, transforming, and loading Dataplex metadata into Neo4j.

    Parameters
    ----------
    catalog_client: dataplex_v1.CatalogServiceClient
        The Dataplex Catalog client used to look up BigQuery table entries.
    glossary_client: dataplex_v1.BusinessGlossaryServiceClient
        The Dataplex Business Glossary client used to extract glossary terms.
    project_id: str
        The GCP project ID.
    project_number: str
        The GCP project number.
    dataplex_location: str
        The Dataplex location (e.g. 'us-central1').
    dataset_id: str
        The BigQuery dataset ID to ingest.
    neo4j_driver: Driver
        The Neo4j driver used to load data into Neo4j.
    table_ids: Optional[list[str]]
        Specific table IDs to ingest. If None, all tables in the dataset are
        discovered automatically via Dataplex search_entries.
    database_name: str
        The name of the Neo4j database to write data to.
    include_schema: bool
        Whether to extract and load the BigQuery schema subgraph
        (Database, Schema, Table, Column nodes and their relationships).
    include_glossary: bool
        Whether to extract and load the business glossary subgraph
        (Glossary, Category, BusinessTerm nodes and their relationships).

    Returns
    -------
    None
        The workflow runs and loads the data into Neo4j.
    """
    if include_schema:
        # Discover table IDs if not supplied explicitly
        if table_ids is None:
            table_ids = extract_dataset_table_ids(
                catalog_client, project_id, project_number, dataplex_location, dataset_id
            )

        print(f"Found {len(table_ids)} tables: {table_ids}")

        if not table_ids:
            print(f"No tables found in dataset '{dataset_id}', skipping schema ingestion.")
        else:
            # Extract one DataFrame per table then concatenate into a single column-level DataFrame
            bigquery_metadata_info = pd.concat(
                [
                    extract_bigquery_metadata_info(
                        catalog_client,
                        project_id,
                        project_number,
                        dataplex_location,
                        dataset_id,
                        table_id,
                    )
                    for table_id in table_ids
                ],
                ignore_index=True,
            )
            print(f"Extracted {len(bigquery_metadata_info)} column records")

            # Pre-process into deduplicated DataFrames for each hierarchy level
            database_metadata_info = bigquery_metadata_info.drop_duplicates(
                subset=["project_id"]
            )
            schema_metadata_info = bigquery_metadata_info.drop_duplicates(
                subset=["project_id", "dataset_id"]
            )
            table_metadata_info = bigquery_metadata_info.drop_duplicates(
                subset=["project_id", "dataset_id", "table_id"]
            )
            column_metadata_info = bigquery_metadata_info  # already one row per column

            # Transform into graph nodes and relationships
            database_nodes = transform_to_database_nodes(database_metadata_info)
            schema_nodes = transform_to_schema_nodes(schema_metadata_info)
            table_nodes = transform_to_table_nodes(table_metadata_info)
            column_nodes = transform_to_column_nodes(column_metadata_info)

            has_schema_relationships = transform_to_has_schema_relationships(
                schema_metadata_info
            )
            has_table_relationships = transform_to_has_table_relationships(
                table_metadata_info
            )
            has_column_relationships = transform_to_has_column_relationships(
                column_metadata_info
            )

            # Load into Neo4j
            print(load_database_nodes(database_nodes, neo4j_driver, database_name))
            print(load_schema_nodes(schema_nodes, neo4j_driver, database_name))
            print(load_table_nodes(table_nodes, neo4j_driver, database_name))
            print(load_column_nodes(column_nodes, neo4j_driver, database_name))
            print(
                load_has_schema_relationships(
                    has_schema_relationships, neo4j_driver, database_name
                )
            )
            print(
                load_has_table_relationships(
                    has_table_relationships, neo4j_driver, database_name
                )
            )
            print(
                load_has_column_relationships(
                    has_column_relationships, neo4j_driver, database_name
                )
            )

    if include_glossary:
        # Extract all glossary terms across all glossaries in the location
        glossary_info = extract_glossary_info(
            glossary_client, project_id, dataplex_location
        )

        if not isinstance(glossary_info, pd.DataFrame) or glossary_info.empty:
            print("No glossary terms found, skipping glossary ingestion.")
        else:
            # Pre-process into deduplicated DataFrames for each node type
            glossary_metadata_info = glossary_info.drop_duplicates(subset=["glossary_id"])
            category_info = glossary_info[
                glossary_info["category_id"].notna()
            ].drop_duplicates(subset=["glossary_id", "category_id"])
            # Terms without a category fall back to the glossary as their parent
            business_term_info = glossary_info

            print(f"Found {len(glossary_metadata_info)} glossaries, {len(category_info)} categories, {len(business_term_info)} terms")

            # Transform into graph nodes and relationships
            glossary_nodes = transform_to_glossary_nodes(glossary_metadata_info)
            category_nodes = transform_to_category_nodes(category_info)
            business_term_nodes = transform_to_business_term_nodes(business_term_info)

            has_category_relationships = transform_to_has_category_relationships(
                category_info
            )
            has_business_term_relationships = transform_to_has_business_term_relationships(
                business_term_info
            )

            # Load into Neo4j
            print(load_glossary_nodes(glossary_nodes, neo4j_driver, database_name))
            print(load_category_nodes(category_nodes, neo4j_driver, database_name))
            print(load_business_term_nodes(business_term_nodes, neo4j_driver, database_name))
            print(
                load_has_category_relationships(
                    has_category_relationships, neo4j_driver, database_name
                )
            )
            print(
                load_has_business_term_relationships(
                    has_business_term_relationships, neo4j_driver, database_name
                )
            )
