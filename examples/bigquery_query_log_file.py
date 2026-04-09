"""Example: load BigQuery query log data from a local file into the semantic graph."""

import asyncio
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

from semantic_graph.connectors.query_log import QueryLogConnector


async def main() -> None:
    """Run the query log connector to load query log data from a local file."""
    load_dotenv()
    print("Starting connector...")
    print("Creating drivers and clients...")

    neo4j_driver = GraphDatabase.driver(
        uri=os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
    )
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")

    print("Extracting, transforming, and loading query logs into Neo4j...")
    connector = QueryLogConnector(
        neo4j_driver=neo4j_driver,
        database_name=neo4j_database,
    )
    connector.run(query_log_file="datasets/bigquery_query_logs.json", source="bigquery")


if __name__ == "__main__":
    asyncio.run(main())
