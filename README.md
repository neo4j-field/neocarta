# Text2SQL Template

End to end template for generating a RDBMS metadata knowledge graph for Text2SQL workflows.

## Metadata Graph

The metadata graph has the following schema. All connectors must convert their schema information to this graph schema to be compatible with the provided MCP server and ingestion tooling.

```mermaid
---
config:
    layout: elk
---

graph LR
%% Nodes
Database("Database<br/>id: STRING | KEY<br/>name: STRING<br/>description: STRING<br/>embedding: LIST")
Table("Table<br/>id: STRING | KEY<br/>name: STRING<br/>description: STRING<br/>embedding: LIST")
Column("Column<br/>id: STRING | KEY<br/>name: STRING<br/>description: STRING<br/>embedding: LIST<br/>type: STRING<br/>nullable: BOOLEAN<br/>isPrimaryKey: BOOLEAN<br/>isForeignKey: BOOLEAN")

%% Relationships
Database -->|CONTAINS_TABLE| Table
Table -->|HAS_COLUMN| Column
Column -->|REFERENCES| Column


%% Styling 
classDef node_0_color fill:#e3f2fd,stroke:#1976d2,stroke-width:3px,color:#000,font-size:12px
class Database node_0_color

classDef node_1_color fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px,color:#000,font-size:12px
class Table node_1_color

classDef node_2_color fill:#e8f5e8,stroke:#388e3c,stroke-width:3px,color:#000,font-size:12px
class Column node_2_color
```

Nodes
* `Database`
* `Table`
* `Column`
* `Value`

Relationships
* `(:Database)-[:CONTAINS_TABLE]->(:Table)`
* `(:Table)-[:HAS_COLUMN]->(:Column)`
* `(:Column)-[:HAS_VALUE]->(:Value)`
* `(:Column)-[:REFERENCES]->(:Column)`


### Graph Generation

This project provides connectors to 
* Connect to source data
* Read metadata tables 
* Transform metadata into defined Neo4j schema
* Ingest transformed data into Neo4j

#### Connectors

**BigQuery**
* Connector for reading BigQuery Information Schema tables and ingesting metadata into Neo4j

CODE EXAMPLE

#### Embeddings 

Embeddings are generated for the `description` fields of the following nodes:
* `Database`
* `Table`
* `Column`

This project currently supports the following embeddings Providers
* OpenAI

CODE EXAMPLE

## MCP

This project uses two MCP servers for the Text2SQL agent.

### **Local SQL Metadata MCP Server**

This is a custom SQL metadata retrieval MCP server that provides tools to query the Neo4j database for relevant RDBMS schema information using semantic similarity search.

**Tools**
* `get_metadata_schema_by_semantic_similarity` - Retrieves table metadata using vector similarity search on column embeddings and graph traversal. Returns the most relevant tables and column subset with their references, and example values.
* `get_full_metadata_schema` - Retrieves complete metadata schema for all tables in the database. Returns the tables and columns with their references, and example values.


**Environment Variables**
* `NEO4J_URI` - Neo4j database connection URI (e.g., `bolt://localhost:7687`)
* `NEO4J_USERNAME` - Neo4j username (default: `neo4j`)
* `NEO4J_PASSWORD` - Neo4j password
* `NEO4J_DATABASE` - Neo4j database name (default: `neo4j`)
* `OPENAI_API_KEY` - OpenAI API key for generating query embeddings
* `EMBEDDING_MODEL` - OpenAI embedding model to use (default: `text-embedding-3-small`)
* `EMBEDDING_DIMENSIONS` - Embedding vector dimensions (default: `768`)



### **Remote BigQuery MCP Server**

This is the official BigQuery remote MCP server and will be used to execute SQL queries against our database.

Since this is a remote server, we don't need to worry about hosting it locally. We can just connect to the MCP endpoint in our GCP environment.

**Tools** (Filtered subset of total tools the server provides)
* `execute_sql` - Execute a SQL query against BigQuery. Returns the raw results.

#### Set Up

Enable use of the [Bigquery MCP server](https://docs.cloud.google.com/bigquery/docs/reference/mcp) in your project.

Additional information may be found [here](https://docs.cloud.google.com/bigquery/docs/use-bigquery-mcp).

PROJECT_ID=Google Cloud project ID
SERVICE=bigquery.googleapis.com

```bash
gcloud beta services mcp enable SERVICE --project=PROJECT_ID
```

To disable again run

```bash
gcloud beta services mcp disable SERVICE --project=PROJECT_ID
```

You can test the BigQuery server connection with the following curl command

```bash
curl -k \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -d '{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "execute_sql",
    "arguments": {
      "projectId": "<PROJECT_ID>",
      "query": "SELECT table_name FROM `<PROJECT_ID>.<DATASET_ID>.INFORMATION_SCHEMA.TABLES`"
    }
  }
}' \
  https://bigquery.googleapis.com/mcp
```


## Agent

This is the Text2SQL agent that converts natural language questions into SQL queries for BigQuery. The agent uses two MCP servers to:
1. Retrieve relevant database metadata from Neo4j using semantic similarity
2. Execute generated SQL queries against BigQuery

**How it works**
1. User asks a natural language question about the data
2. Agent calls the SQL Metadata MCP server to retrieve relevant table schemas
3. Agent generates a SQL query based on the retrieved metadata context
4. Agent calls `execute_sql` from the BigQuery MCP server to run the query against BigQuery
5. Agent returns formatted results to the user

**Running the Agent**

Use this command to run the agent locally:
```bash
uv run run_agent.py
```

The agent will start an interactive chat session in the terminal where you can ask questions about your data.


**BigQuery MCP Authentication**

The agent uses Google Cloud Application Default Credentials for BigQuery authentication:

```python
class GoogleAuth(httpx.Auth):
    def __init__(self):
        self.credentials, _ = default()

    def auth_flow(self, request):
        self.credentials.refresh(Request())
        request.headers["Authorization"] = f"Bearer {self.credentials.token}"
        yield request
```

Make sure you're authenticated with:
```bash
gcloud auth application-default login
```

**Environment Variables**

Required environment variables (add to `.env` file):

**Neo4j Connection**
* `NEO4J_URI` - Neo4j database URI (e.g., `bolt://localhost:7687`)
* `NEO4J_USERNAME` - Neo4j username (default: `neo4j`)
* `NEO4J_PASSWORD` - Neo4j password
* `NEO4J_DATABASE` - Neo4j database name (default: `neo4j`)

**LLMOpenAI**
* `OPENAI_API_KEY` - OpenAI API key for embeddings and LLM

**Example Usage**

```
> What are the total sales by product category?

Agent: [Calls get_metadata_schema_by_semantic_similarity with query about sales and categories]
Agent: [Generates SQL query using retrieved schema]
Agent: [Calls execute_sql with generated query]
Agent: Here are the total sales by product category:
- Electronics: $15,234.50
- Clothing: $8,912.30
...
```



