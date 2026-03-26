from fastmcp import FastMCP
import asyncio
from neo4j import AsyncDriver, AsyncGraphDatabase, RoutingControl
from models import TableContext
from dotenv import load_dotenv
from settings import mcp_server_settings
from embeddings import create_embedding
from openai import AsyncOpenAI


def create_mcp_server(
    neo4j_driver: AsyncDriver, neo4j_database: str, embedding_client: AsyncOpenAI
) -> FastMCP:
    server = FastMCP("Text2SQL Metadata MCP Server")

    @server.tool()
    async def get_metadata_schema_by_semantic_similarity(
        query: str,
    ) -> list[TableContext]:
        """
        Get the metadata schema by semantic similarity to the query.
        Uses embedding based semantic similarity and graph traversal to find the most similar metadata schema.
        """

        embedding = await create_embedding(embedding_client, query)

        cypher = """
// Find similar columns by embedding
CALL db.index.vector.queryNodes('column_vector_index', 10, $queryEmbedding)
YIELD node as col, score
WHERE score > 0.5

// Get the columns for each table
MATCH (col)<-[:HAS_COLUMN]-(table:Table)

// Find all references for this column (both directions)
OPTIONAL MATCH (col)-[:REFERENCES]-(refCol:Column)<-[:HAS_COLUMN]-(refTable:Table)

// Get example values
OPTIONAL MATCH (col)-[:HAS_VALUE]->(v:Value)

WITH 
  table,
  col,
  collect(DISTINCT {
    table_name: refTable.name,
    column_name: refCol.name
  }) AS refs,
  collect(DISTINCT v.value)[0..5] AS exampleValues

// Group columns by table and build column objects
WITH 
  table,
  collect({
    column_name: col.name,
    column_description: col.description,
    data_type: col.type,
    examples: exampleValues,
    nullable: col.nullable,
    references: [ref IN refs WHERE ref.table_name IS NOT NULL | ref]
  }) AS columns


// Get Schema and Database names for Tables
MATCH (table)<-[:HAS_TABLE]-(schema:Schema)<-[:HAS_SCHEMA]-(db:Database)

// Group the join columns by target table
WITH
  table,
  columns,
  db.name AS database_name,
  schema.name AS schema_name

WITH
  table,
  columns,
  database_name,
  schema_name

RETURN {
  table_name: table.name,
  table_description: table.description,
  database_name: database_name,
  schema_name: schema_name,
  columns: columns
} AS result
ORDER BY table.name
"""
        results = await neo4j_driver.execute_query(
            query_=cypher,
            parameters_={"queryEmbedding": embedding},
            database_=neo4j_database,
            routing_=RoutingControl.READ,
            result_transformer_=lambda x: x.data(),
        )
        return [TableContext.model_validate(r["result"]) for r in results]

    @server.tool()
    async def get_full_metadata_schema() -> list[TableContext]:
        """
        Get the full metadata schema for the database.
        """

        cypher = """
// Get the columns for each table
MATCH (col:Column)<-[:HAS_COLUMN]-(table:Table)

// Find all references for this column (both directions)
OPTIONAL MATCH (col)-[:REFERENCES]-(refCol:Column)<-[:HAS_COLUMN]-(refTable:Table)

// Get example values
OPTIONAL MATCH (col)-[:HAS_VALUE]->(v:Value)

WITH 
  table,
  col,
  collect(DISTINCT {
    table_name: refTable.name,
    column_name: refCol.name
  }) AS refs,
  collect(DISTINCT v.value)[0..5] AS exampleValues

// Group columns by table and build column objects
WITH 
  table,
  collect({
    column_name: col.name,
    column_description: col.description,
    data_type: col.type,
    examples: exampleValues,
    key_type: CASE 
      WHEN col.is_primary_key THEN "primary"
      WHEN col.is_foreign_key THEN "foreign"
      ELSE null
    END,
    nullable: col.nullable,
    references: [ref IN refs WHERE ref.table_name IS NOT NULL | ref]
  }) AS columns

// Get all joins for this table by finding all foreign key relationships
OPTIONAL MATCH (table)-[:HAS_COLUMN]->(fkCol:Column)-[:REFERENCES]-(otherCol:Column)<-[:HAS_COLUMN]-(otherTable:Table)

// Get Schema and Database names for Tables
MATCH (table)<-[:HAS_TABLE]-(schema:Schema)<-[:HAS_SCHEMA]-(db:Database)

// Group the join columns by target table
WITH
  table,
  columns,
  db.name AS database_name,
  schema.name AS schema_name,
  otherTable.name AS join_table_name,
  collect(DISTINCT otherCol.name) AS join_column_names
WHERE join_table_name IS NOT NULL

WITH
  table,
  columns,
  database_name,
  schema_name,
  collect({
    table_name: join_table_name,
    column_names: join_column_names
  }) AS joins

RETURN {
  table_name: table.name,
  table_description: table.description,
  database_name: database_name,
  schema_name: schema_name,
  columns: columns,
  joins: joins
} AS result
ORDER BY table.name
"""
        results = await neo4j_driver.execute_query(
            query_=cypher,
            database_=neo4j_database,
            routing_=RoutingControl.READ,
            result_transformer_=lambda x: x.data(),
        )
        return [TableContext.model_validate(r["result"]) for r in results]

    return server


async def main():
    neo4j_driver = AsyncGraphDatabase.driver(
        uri=mcp_server_settings.neo4j_uri,
        auth=(mcp_server_settings.neo4j_username, mcp_server_settings.neo4j_password),
    )
    neo4j_database = mcp_server_settings.neo4j_database
    embedding_client = AsyncOpenAI(api_key=mcp_server_settings.openai_api_key)
    server = create_mcp_server(neo4j_driver, neo4j_database, embedding_client)

    await server.run_stdio_async()


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
