"""FastMCP server exposing semantic layer metadata tools."""

import asyncio

from dotenv import load_dotenv
from fastmcp import FastMCP
from neo4j import AsyncDriver, AsyncGraphDatabase, RoutingControl
from openai import AsyncOpenAI

from ..enrichment.embeddings import OpenAIEmbeddingsConnector
from .embeddings import create_openai_embedder
from .models import ListSchemaRecord, ListTablesBySchemaRecord, TableContext
from .settings import mcp_server_settings
from .cypher import (
    list_schemas_cypher,
    list_tables_by_schema_cypher,
    get_metadata_schema_by_column_semantic_similarity_cypher,
    get_metadata_schema_by_schema_and_table_semantic_similarity_cypher,
    get_full_metadata_schema_cypher,
    get_metadata_schema_by_table_semantic_similarity_cypher,
)


def create_mcp_server(
    neo4j_driver: AsyncDriver, neo4j_database: str, embedder: OpenAIEmbeddingsConnector
) -> FastMCP:
    """Create and configure the FastMCP server with all semantic layer tools."""
    server = FastMCP("Neocarta MCP Server")

    @server.tool()
    async def list_schemas() -> list[ListSchemaRecord]:
        """List all schemas and their databases."""
        cypher = list_schemas_cypher()
        return await neo4j_driver.execute_query(
            query_=cypher,
            database_=neo4j_database,
            routing_=RoutingControl.READ,
            result_transformer_=lambda x: x.data(),
        )

    @server.tool()
    async def list_tables_by_schema(schema_name: str) -> list[ListTablesBySchemaRecord]:
        """List all tables for a provided schema name."""
        cypher = list_tables_by_schema_cypher()
        return await neo4j_driver.execute_query(
            query_=cypher,
            parameters_={"schemaName": schema_name},
            database_=neo4j_database,
            routing_=RoutingControl.READ,
            result_transformer_=lambda x: x.data(),
        )

    @server.tool()
    async def get_metadata_schema_by_column_semantic_similarity(
        query: str,
    ) -> list[TableContext]:
        """
        Get the metadata schema by column semantic similarity to the query.
        Uses embedding based column semantic similarity and graph traversal to find the most similar metadata schema.
        """
        embedding = await embedder._create_embedding_async(query)

        cypher = get_metadata_schema_by_column_semantic_similarity_cypher()

        results = await neo4j_driver.execute_query(
            query_=cypher,
            parameters_={"queryEmbedding": embedding},
            database_=neo4j_database,
            routing_=RoutingControl.READ,
            result_transformer_=lambda x: x.data(),
        )
        return [TableContext.model_validate(r["result"]) for r in results]

    @server.tool()
    async def get_metadata_schema_by_table_semantic_similarity(
        query: str,
        max_tables: int = 10,
    ) -> list[TableContext]:
        """
        Get the metadata schema by table semantic similarity to the query.
        Uses embedding based table semantic similarity and graph traversal to find the most similar metadata schema.
        """

        embedding = await embedder._create_embedding_async(query)

        cypher = get_metadata_schema_by_table_semantic_similarity_cypher()

        results = await neo4j_driver.execute_query(
            query_=cypher,
            parameters_={"queryEmbedding": embedding, "maxTables": max_tables},
            database_=neo4j_database,
            routing_=RoutingControl.READ,
            result_transformer_=lambda x: x.data(),
        )
        return [TableContext.model_validate(r["result"]) for r in results]

    @server.tool()
    async def get_metadata_schema_by_schema_and_table_semantic_similarity(
        query: str,
        max_tables: int = 5,
    ) -> list[TableContext]:
        """
        Get the metadata schema by schema and table semantic similarity to the query.
        Uses embedding based semantic similarity and graph traversal to find the most similar metadata schema.

        Parameters
        ----------
        query: str
            The query to search for.
        max_tables: int
            The maximum number of tables to return.

        Returns:
        -------
        list[TableContext]
            The metadata schema by schema and table semantic similarity to the query.
        """
        embedding = await embedder._create_embedding_async(query)

        cypher = get_metadata_schema_by_schema_and_table_semantic_similarity_cypher()

        results = await neo4j_driver.execute_query(
            query_=cypher,
            parameters_={"queryEmbedding": embedding, "maxTables": max_tables},
            database_=neo4j_database,
            routing_=RoutingControl.READ,
            result_transformer_=lambda x: x.data(),
        )
        return [TableContext.model_validate(r["result"]) for r in results]

    @server.tool()
    async def get_full_metadata_schema() -> list[TableContext]:
        """
        Get the full metadata schema for the database.
        WARNING: This is an expensive query and should only be used for debugging.
        """
        cypher = get_full_metadata_schema_cypher()

        results = await neo4j_driver.execute_query(
            query_=cypher,
            database_=neo4j_database,
            routing_=RoutingControl.READ,
            result_transformer_=lambda x: x.data(),
        )
        return [TableContext.model_validate(r["result"]) for r in results]

    return server


async def main() -> None:
    """Initialize drivers, create the MCP server, and run it over stdio."""
    neo4j_driver = AsyncGraphDatabase.driver(
        uri=mcp_server_settings.neo4j_uri,
        auth=(mcp_server_settings.neo4j_username, mcp_server_settings.neo4j_password),
    )
    neo4j_database = mcp_server_settings.neo4j_database
    embedder = create_openai_embedder(
        async_client=AsyncOpenAI(api_key=mcp_server_settings.openai_api_key),
        neo4j_driver=neo4j_driver,
        database_name=neo4j_database,
    )
    server = create_mcp_server(neo4j_driver, neo4j_database, embedder)

    await server.run_stdio_async()


def run() -> None:
    """Load environment variables and run the MCP server."""
    load_dotenv()
    asyncio.run(main())


if __name__ == "__main__":
    run()
