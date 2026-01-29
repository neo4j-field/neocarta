# Text2SQL Template
End to end template for generating a RDBMS metadata knowledge graph for Text2SQL workflows.


## Agent

### Set Up MCP

Local SQL Metadata MCP Server
* ...

Remote BigQuery MCP Server 

Enable use of the [Bigquery MCP server](https://docs.cloud.google.com/bigquery/docs/reference/mcp) in your project.

PROJECT_ID=Google Cloud project ID
SERVICE=bigquery.googleapis.com

```bash
gcloud beta services mcp enable SERVICE --project=PROJECT_ID
```

To disable again run

```bash
gcloud beta services mcp disable SERVICE --project=PROJECT_ID
```


