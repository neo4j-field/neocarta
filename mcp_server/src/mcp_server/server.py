from fastmcp import FastMCP
import asyncio
from neo4j import AsyncDriver, AsyncGraphDatabase, RoutingControl
from .models import TableContext, ListTablesBySchemaRecord, ListSchemaRecord
from dotenv import load_dotenv
from .settings import mcp_server_settings
from .embeddings import create_embedding
from openai import AsyncOpenAI


def create_mcp_server(
    neo4j_driver: AsyncDriver, neo4j_database: str, embedding_client: AsyncOpenAI
) -> FastMCP:
    server = FastMCP("Semantic Layer MCP Server")

    @server.tool()
    async def list_schemas() -> list[ListSchemaRecord]:
        """
        List all schemas and their databases.
        """

        cypher = """
        MATCH (d:Database)-[:HAS_SCHEMA]->(schema:Schema)
        RETURN d.name as database_name, schema.name as schema_name
        """
        results = await neo4j_driver.execute_query(
            query_=cypher,
            database_=neo4j_database,
            routing_=RoutingControl.READ,
            result_transformer_=lambda x: x.data(),
        )
        return results
    

    @server.tool()
    async def list_tables_by_schema(schema_name: str) -> list[ListTablesBySchemaRecord]:
        """
        List all tables for a provided schema name.
        """

        cypher = """
        MATCH (s:Schema {name: $schemaName})-[:HAS_TABLE]->(t:Table)
        RETURN s.name as schema_name, collect(t.name) as table_names
        """
        results = await neo4j_driver.execute_query(
            query_=cypher,
            parameters_={"schemaName": schema_name},
            database_=neo4j_database,
            routing_=RoutingControl.READ,
            result_transformer_=lambda x: x.data(),
        )
        return results

    @server.tool()
    async def get_metadata_schema_by_column_semantic_similarity(
        query: str,
    ) -> list[TableContext]:
        """
        Get the metadata schema by column semantic similarity to the query.
        Uses embedding based column semantic similarity and graph traversal to find the most similar metadata schema.
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
  collect(DISTINCT refTable.name + "." + refCol.name) AS refs,
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
    references: refs
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

          Returns
          -------
          list[TableContext]
              The metadata schema by schema and table semantic similarity to the query.
          """

          embedding = await create_embedding(embedding_client, query)

          cypher = """
// Find similar schemas by embedding
CALL db.index.vector.queryNodes('schema_vector_index', 5, $queryEmbedding)
YIELD node as schema, score as schemaScore
WHERE schemaScore > 0.5

// Get the tables for each schema
// Only get tables that are nearly as similar as the schema
MATCH (schema)-[:HAS_TABLE]->(table:Table)

WITH    schema,
        schemaScore,
        table,
        vector.similarity.cosine(table.embedding, $queryEmbedding) as tableScore
WHERE tableScore > schemaScore - 0.2

// Find all references for this column (both directions)
MATCH (table)-[:HAS_COLUMN]->(col:Column)
OPTIONAL MATCH (col)-[:REFERENCES]-(refCol:Column)<-[:HAS_COLUMN]-(refTable:Table)

// Get example values
OPTIONAL MATCH (col)-[:HAS_VALUE]->(v:Value)

WITH 
  schema,
  table,
  col,
  collect(DISTINCT refTable.name + "." + refCol.name) AS refs,
  collect(DISTINCT v.value)[0..3] AS exampleValues,
  schemaScore,
  tableScore

// Group columns by table and build column objects
WITH 
  schema,
  table,
  collect({
    column_name: col.name,
    column_description: col.description,
    data_type: col.type,
    examples: exampleValues,
    references: refs
  }) AS columns,
  schemaScore,
  tableScore

// Get Schema and Database names for Tables
MATCH (schema:Schema)<-[:HAS_SCHEMA]-(db:Database)

// Group the join columns by target table
WITH
  table,
  columns,
  db.name AS database_name,
  schema.name AS schema_name,
  schemaScore,
  tableScore

WITH
  table,
  columns,
  database_name,
  schema_name,
  schemaScore,
  tableScore

RETURN {
  table_name: table.name,
  table_description: table.description,
  database_name: database_name,
  schema_name: schema_name,
  columns: columns,
  numColumns: size(columns),
  schemaScore: schemaScore,
  tableScore: tableScore
} AS result
ORDER BY schemaScore DESC, tableScore DESC
LIMIT $maxTables
  """
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
  collect(DISTINCT refTable.name + "." + refCol.name) AS refs,
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
    references: refs
  }) AS columns

// Get Schema and Database names for Tables
MATCH (table)<-[:HAS_TABLE]-(schema:Schema)<-[:HAS_SCHEMA]-(db:Database)

WITH
  table,
  columns,
  schema.name as schema_name,
  db.name as database_name

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


def run():
    load_dotenv()
    asyncio.run(main())


if __name__ == "__main__":
    run()
