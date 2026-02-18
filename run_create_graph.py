import argparse
import asyncio
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import AsyncOpenAI
from embeddings.openai_embeddings import OpenAIEmbeddingWorkflow
from google.cloud import bigquery
from connectors.bigquery.workflow import BigQueryWorkflow


async def main(with_embeddings: bool = True):
    load_dotenv()
    print("Starting workflow...")
    print("Creating drivers and clients...")
    neo4j_driver = GraphDatabase.driver(
        uri=os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
    )
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
    embedding_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    bigquery_client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"))

    node_labels = ["Database", "Schema", "Table", "Column"]

    print("Extracting, transforming, and loading BigQuery data into Neo4j...")
    # extract, transform, and load BigQuery data into Neo4j
    bigquery_workflow = BigQueryWorkflow(
        client=bigquery_client,
        project_id=os.getenv("GCP_PROJECT_ID"),
        dataset_id=os.getenv("BIGQUERY_DATASET_ID"),
        neo4j_driver=neo4j_driver,
        database_name=neo4j_database,
    )
    bigquery_workflow.run()

    if with_embeddings:
        print("Generating embeddings for nodes...")
        # create embeddings for the nodes
        openai_embedding_workflow = OpenAIEmbeddingWorkflow(
            async_embedding_client=embedding_client,
            embedding_model="text-embedding-3-small",
            dimensions=768,
            neo4j_driver=neo4j_driver,
            database_name=neo4j_database,
        )
        await openai_embedding_workflow.arun(node_labels=node_labels)

    print("Workflow completed successfully!")


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

    asyncio.run(main(with_embeddings=not args.skip_embeddings))
