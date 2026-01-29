# Text2SQL Template

End to end template for generating a RDBMS metadata knowledge graph for Text2SQL workflows.

## Metadata Graph

The metadata graph has the following schema. All connectors must convert their schema information to this graph schema to be compatible with the provided MCP server and ingestion tooling.

<IMAGE OF SCHEMA>

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

<CODE EXAMPLE>

#### Embeddings 

Embeddings are generated for the `description` fields of the following nodes:
* `Database`
* `Table`
* `Column`

This project currently supports the following embeddings Providers
* OpenAI

<CODE EXAMPLE>

## MCP

This project uses two MCP servers for the Text2SQL agent. 

### **Local SQL Metadata MCP Server**

This is a custom SQL metadata retrieval MCP server that has tools to query the Neo4j database for relevant RDBMS schema information.

Tools
* get_metadata_schema_by_semantic_similarity
* get_full_metadata_schema

Environment Variables 
* 

### **Remote BigQuery MCP Server**

This is the official BigQuery remote MCP server and will be used to execute SQL queries against our database.

Since this is a remote server, we don't need to worry about hosting it locally. We can just connect to the MCP endpoint in our GCP environment.

Tools (Fitlered subset of total tools the server provides)
* execute_sql

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





