"""Integration tests for the MCP server tools."""

import asyncio
import json

from fastmcp import Client
from neo4j import AsyncGraphDatabase

from neocarta._mcp.server import create_mcp_server
from tests.integration._mcp.conftest import MockEmbeddingsConnector

DATABASE_NAME = "neo4j"


async def _call_tool(
    neo4j_connection: dict, tool_name: str, args: dict | None = None
) -> list[dict]:
    """Create async MCP resources, call a tool, and return the parsed result.

    A fresh async driver and mock embedder are created within each call so
    they share the same event loop created by asyncio.run().
    """
    driver = AsyncGraphDatabase.driver(
        neo4j_connection["uri"],
        auth=(neo4j_connection["username"], neo4j_connection["password"]),
    )
    try:
        embedder = MockEmbeddingsConnector(neo4j_driver=driver, database_name=DATABASE_NAME)
        server = create_mcp_server(driver, DATABASE_NAME, embedder)
        async with Client(server) as client:
            result = await client.call_tool(tool_name, args or {})
            if not result.content:
                return []
            return json.loads(result.content[0].text)
    finally:
        await driver.close()


def test_list_schemas_returns_all_schemas(neo4j_connection, loaded_graph):
    """list_schemas returns one record per schema with the correct database name."""
    data = asyncio.run(_call_tool(neo4j_connection, "list_schemas"))

    assert len(data) == 2
    schema_names = {r["schema_name"] for r in data}
    assert schema_names == {"sales", "analytics"}
    for record in data:
        assert record["database_name"] == "my-project"


def test_list_tables_by_schema_returns_tables(neo4j_connection, loaded_graph):
    """list_tables_by_schema returns the correct tables for a given schema."""
    data = asyncio.run(
        _call_tool(neo4j_connection, "list_tables_by_schema", {"schema_name": "sales"})
    )

    assert len(data) == 1
    record = data[0]
    assert record["schema_name"] == "sales"
    assert set(record["table_names"]) == {"orders", "customers"}


def test_list_tables_by_schema_unknown_returns_empty(neo4j_connection, loaded_graph):
    """list_tables_by_schema returns an empty list for an unknown schema."""
    data = asyncio.run(
        _call_tool(neo4j_connection, "list_tables_by_schema", {"schema_name": "unknown"})
    )

    assert data == []


def test_get_metadata_schema_by_column_semantic_similarity(neo4j_connection, loaded_graph):
    """Column similarity search returns tables with their columns populated."""
    data = asyncio.run(
        _call_tool(
            neo4j_connection,
            "get_metadata_schema_by_column_semantic_similarity",
            {"text_content": "customer name"},
        )
    )

    assert len(data) > 0
    for record in data:
        assert record["database_name"] == "my-project"
        assert len(record["columns"]) > 0
        assert record["num_columns"] == len(record["columns"])
        assert record["column_avg_score"] is not None
        assert record["column_avg_score"] > 0.5


def test_get_metadata_schema_by_table_semantic_similarity(neo4j_connection, loaded_graph):
    """Table similarity search returns tables with columns, scores, and column count."""
    data = asyncio.run(
        _call_tool(
            neo4j_connection,
            "get_metadata_schema_by_table_semantic_similarity",
            {"text_content": "sales orders customers", "max_tables": 5},
        )
    )

    assert len(data) > 0
    for record in data:
        assert record["database_name"] == "my-project"
        assert len(record["columns"]) > 0
        assert record["num_columns"] == len(record["columns"])
        assert record["table_score"] is not None
        assert record["table_score"] > 0.5


def test_get_metadata_schema_by_schema_and_table_semantic_similarity(
    neo4j_connection, loaded_graph
):
    """Schema/table similarity search returns tables with their columns populated."""
    data = asyncio.run(
        _call_tool(
            neo4j_connection,
            "get_metadata_schema_by_schema_and_table_semantic_similarity",
            {"text_content": "sales orders customers", "max_tables": 5},
        )
    )

    assert len(data) > 0
    for record in data:
        assert record["database_name"] == "my-project"
        assert len(record["columns"]) > 0
        assert record["num_columns"] == len(record["columns"])
        assert record["table_score"] is not None
        assert record["table_score"] > 0.5
        assert record["schema_score"] is not None
        assert record["schema_score"] > 0.5


def test_get_full_metadata_schema_returns_all_tables(neo4j_connection, loaded_graph):
    """get_full_metadata_schema returns every table with all columns populated."""
    data = asyncio.run(_call_tool(neo4j_connection, "get_full_metadata_schema"))

    assert len(data) == 3
    table_names = {r["table_name"] for r in data}
    assert table_names == {"orders", "customers", "summary"}

    for record in data:
        assert record["database_name"] == "my-project"
        assert len(record["columns"]) > 0

    orders = next(r for r in data if r["table_name"] == "orders")
    assert {c["column_name"] for c in orders["columns"]} == {"order_id", "customer_id", "total"}

    customer_id_col = next(c for c in orders["columns"] if c["column_name"] == "customer_id")
    assert "customers.customer_id" in customer_id_col["references"]
