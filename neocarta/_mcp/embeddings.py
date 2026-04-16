"""Embedding utilities for the MCP server."""

from neo4j import AsyncDriver
from openai import AsyncOpenAI

from ..enrichment.embeddings import OpenAIEmbeddingsConnector
from .settings import mcp_server_settings


def create_openai_embedder(
    async_client: AsyncOpenAI,
    neo4j_driver: AsyncDriver,
    database_name: str = "neo4j",
) -> OpenAIEmbeddingsConnector:
    """Create an OpenAIEmbeddingsConnector configured for the MCP server.

    Parameters
    ----------
    async_client: AsyncOpenAI
        The async OpenAI client to use for embedding creation.
    neo4j_driver: AsyncDriver
        The Neo4j async driver (stored on the connector but not used for
        single-embedding calls like _create_embedding_async).
    database_name: str
        The Neo4j database name.

    Returns:
    -------
    OpenAIEmbeddingsConnector
        Connector configured with the MCP server's embedding model and dimensions.
    """
    return OpenAIEmbeddingsConnector(
        neo4j_driver=neo4j_driver,  # type: ignore[arg-type]
        async_client=async_client,
        embedding_model=mcp_server_settings.embedding_model,
        dimensions=mcp_server_settings.embedding_dimensions,
        database_name=database_name,
    )
