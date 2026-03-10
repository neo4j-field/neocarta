import os
import asyncio
from dotenv import load_dotenv
from neo4j import GraphDatabase
from semantic_graph.connectors.query_log import QueryLogWorkflow

async def main():
    load_dotenv()
    print("Starting workflow...")
    print("Creating drivers and clients...")

    neo4j_driver = GraphDatabase.driver(
        uri=os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
    )
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")

    print("Extracting, transforming, and loading query logs into Neo4j...")
    workflow = QueryLogWorkflow(
        neo4j_driver=neo4j_driver,
        database_name=neo4j_database,
    )
    workflow.run(query_log_file="datasets/bigquery_query_logs.json", source="bigquery")

if __name__ == "__main__":
    asyncio.run(main())