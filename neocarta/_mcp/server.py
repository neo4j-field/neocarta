"""FastMCP server exposing semantic layer metadata tools."""

import asyncio

from dotenv import load_dotenv
from fastmcp import FastMCP
from neo4j import AsyncDriver, AsyncGraphDatabase, RoutingControl
from openai import AsyncOpenAI

from ..enrichment.embeddings import OpenAIEmbeddingsConnector
from .cypher import (
    get_full_metadata_schema_cypher,
    get_metadata_schema_by_column_semantic_similarity_cypher,
    get_metadata_schema_by_schema_and_table_semantic_similarity_cypher,
    get_metadata_schema_by_table_semantic_similarity_cypher,
    list_schemas_cypher,
    list_tables_by_schema_cypher,
)
from .embeddings import create_openai_embedder
from .models import ListSchemaRecord, ListTablesBySchemaRecord, TableContext
from .settings import mcp_server_settings


def create_mcp_server(
    neo4j_driver: AsyncDriver, neo4j_database: str, embedder: OpenAIEmbeddingsConnector
) -> FastMCP:
    """Create and configure the FastMCP server with all semantic layer tools."""
    name = "Neocarta MCP Server"
    instructions = """
This is an MCP server that facilitates context retrieval from a Neo4j semantic layer.
The retrieved context may be used for query generation, query routing or data discovery.
"""
    server = FastMCP(name=name, instructions=instructions)

    @server.tool()
    async def list_schemas() -> list[ListSchemaRecord]:
        """
        List all schemas and their databases.

        Use this as the first step when exploring an unfamiliar database or when
        you need a valid schema name to pass to other tools. Returns every schema
        alongside the database it belongs to.
        """
        cypher = list_schemas_cypher()
        return await neo4j_driver.execute_query(
            query_=cypher,
            database_=neo4j_database,
            routing_=RoutingControl.READ,
            result_transformer_=lambda x: x.data(),
        )

    @server.tool()
    async def list_tables_by_schema(schema_name: str) -> list[ListTablesBySchemaRecord]:
        """
        List all tables for a given schema.

        Use this when you already know the schema name and want to enumerate its
        tables. Call list_schemas first to obtain valid schema names.

        Parameters
        ----------
        schema_name: str
            The name of the schema to list tables for. Use list_schemas to get
            valid schema names.
        """
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
        text_content: str,
        max_tables: int = 5,
    ) -> list[TableContext]:
        """
        Find tables whose columns are semantically similar to the provided text.

        Prefer this tool when the query references specific field or column names
        (e.g. "customer email", "order total"). Matches are ranked by average
        column embedding similarity and traversed up to the parent table.
        Note: requires that Column nodes have the embedding property set.

        Parameters
        ----------
        text_content: str
            Natural-language description or query to search for semantically
            similar columns.
        max_tables: int
            Maximum number of tables to return
        """
        embedding = await embedder._create_embedding_async(text_content)

        cypher = get_metadata_schema_by_column_semantic_similarity_cypher()

        results = await neo4j_driver.execute_query(
            query_=cypher,
            parameters_={"queryEmbedding": embedding, "maxTables": max_tables},
            database_=neo4j_database,
            routing_=RoutingControl.READ,
            result_transformer_=lambda x: x.data(),
        )
        return [TableContext.model_validate(r["result"]) for r in results]

    @server.tool()
    async def get_metadata_schema_by_table_semantic_similarity(
        text_content: str,
        max_tables: int = 10,
    ) -> list[TableContext]:
        """
        Find tables that are semantically similar to the provided text.

        Prefer this tool when the query describes a general concept or entity
        (e.g. "customers", "sales transactions"). Matches are ranked by table
        embedding similarity.
        Note: requires that Table nodes have the embedding property set.

        Parameters
        ----------
        text_content: str
            Natural-language description or query to search for semantically
            similar tables.
        max_tables: int
            Maximum number of tables to return
        """
        embedding = await embedder._create_embedding_async(text_content)

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
        text_content: str,
        max_tables: int = 5,
    ) -> list[TableContext]:
        """
        Find tables by matching both schema and table embeddings to the provided text.

        Prefer this tool when the query is broad and may span multiple schemas and tables
        (e.g. "everything related to billing").
        First finds similar schemas, then filters to tables within those schemas whose embeddings are near or better than the schema score.
        Note: requires that `Schema` and `Table` nodes have the `embedding` property set.

        Parameters
        ----------
        text_content: str
            Natural-language description or query to search for semantically
            similar schemas and tables.
        max_tables: int
            Maximum number of tables to return, ordered by descending schema
            then table similarity score.
        """
        embedding = await embedder._create_embedding_async(text_content)

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
        Return the complete metadata schema for every table in the database.

        WARNING: This fetches all tables and all columns without any filtering.
        On databases with many tables this will return a very large payload and
        should only be used for debugging or on small databases. Prefer the
        semantic similarity tools for targeted lookups.
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
