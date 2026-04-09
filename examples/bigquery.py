"""Example: load BigQuery schema metadata into the semantic graph."""

import argparse
import os

from dotenv import load_dotenv
from google.cloud import bigquery
from neo4j import GraphDatabase
from openai import OpenAI

from semantic_graph.connectors.bigquery import BigQuerySchemaConnector
from semantic_graph.embeddings.openai_embeddings import OpenAIEmbeddingsConnector


def main(with_embeddings: bool = True) -> None:
    """Run the BigQuery schema connector and optionally compute embeddings."""
    load_dotenv()
    print("Starting connector...")
    print("Creating drivers and clients...")
    neo4j_driver = GraphDatabase.driver(
        uri=os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
    )
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
    embedding_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    bigquery_client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"))

    node_labels = ["Database", "Schema", "Table", "Column"]

    print("Extracting, transforming, and loading BigQuery data into Neo4j...")
    # extract, transform, and load BigQuery data into Neo4j
    bigquery_connector = BigQuerySchemaConnector(
        client=bigquery_client,
        project_id=os.getenv("GCP_PROJECT_ID"),
        dataset_id=os.getenv("BIGQUERY_DATASET_ID"),
        neo4j_driver=neo4j_driver,
        database_name=neo4j_database,
    )
    bigquery_connector.run()

    if with_embeddings:
        print("Generating embeddings for nodes...")
        # create embeddings for the nodes
        openai_embedding_connector = OpenAIEmbeddingsConnector(
            neo4j_driver=neo4j_driver,
            client=embedding_client,
            embedding_model="text-embedding-3-small",
            dimensions=768,
            database_name=neo4j_database,
        )
        openai_embedding_connector.run(node_labels=node_labels)

    print("Connector completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract BigQuery metadata and load into Neo4j (embeddings enabled by default)"
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip embedding generation (only load metadata into Neo4j)",
    )
    args = parser.parse_args()

    main(with_embeddings=not args.skip_embeddings)
