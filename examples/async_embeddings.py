"""
Async Embeddings Example.

This example demonstrates how to generate embeddings asynchronously
using the OpenAI Embeddings API on an existing Neo4j graph.

This is useful when you want to parallelize embedding generation for
better performance on large datasets.

Usage:
    # Generate embeddings asynchronously for all node types
    python examples/async_embeddings.py

    # Generate embeddings for specific node types
    python examples/async_embeddings.py --node-labels Table Column

    # Use custom batch size
    python examples/async_embeddings.py --batch-size 200

Environment Variables Required:
    - NEO4J_URI: Neo4j connection URI
    - NEO4J_USERNAME: Neo4j username
    - NEO4J_PASSWORD: Neo4j password
    - NEO4J_DATABASE: Neo4j database name (optional, defaults to 'neo4j')
    - OPENAI_API_KEY: OpenAI API key for embeddings
"""

import argparse
import asyncio
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import AsyncOpenAI

from semantic_graph.embeddings.openai_embeddings import OpenAIEmbeddingsConnector


async def main(
    node_labels: list[str] = ["Table", "Column"],
    batch_size: int = 100,
) -> None:
    load_dotenv()
    print("Starting async embeddings process...")
    print("Creating drivers and clients...")

    neo4j_driver = GraphDatabase.driver(
        uri=os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
    )
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
    embedding_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    print(f"Generating embeddings asynchronously for: {', '.join(node_labels)}")
    print(f"Batch size: {batch_size}")

    # Create embeddings for the nodes using async client
    openai_embeddings_connector = OpenAIEmbeddingsConnector(
        neo4j_driver=neo4j_driver,
        async_client=embedding_client,
        embedding_model="text-embedding-3-small",
        dimensions=768,
        database_name=neo4j_database,
    )
    await openai_embeddings_connector.arun(
        node_labels=node_labels,
        batch_size=batch_size,
    )

    print("Async embeddings process completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate embeddings asynchronously for existing Neo4j graph nodes"
    )
    parser.add_argument(
        "--node-labels",
        nargs="+",
        default=["Table", "Column"],
        help="Node labels to generate embeddings for (default: Database Schema Table Column)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of nodes to process in each batch (default: 100)",
    )
    args = parser.parse_args()

    asyncio.run(
        main(
            node_labels=args.node_labels,
            batch_size=args.batch_size,
        )
    )
