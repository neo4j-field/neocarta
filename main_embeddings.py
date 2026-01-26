import asyncio
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import AsyncOpenAI
from embeddings.openai_embeddings import openai_embeddings_workflow


async def main():
    load_dotenv()
    neo4j_driver = GraphDatabase.driver(
        uri=os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
    )
    embedding_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    node_labels = ["Database", "Table", "Column"]
    await openai_embeddings_workflow(
        neo4j_driver, embedding_client, "text-embedding-3-small", 768, node_labels
    )


if __name__ == "__main__":
    asyncio.run(main())
