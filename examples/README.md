# Examples

Example implementations of the Semantic Graph library for Neo4j.

## Available Examples

### Data Connectors

#### `csv_connector.py` - CSV File Connector
Load metadata from CSV files into Neo4j.

**Usage:**
```bash
python csv_connector.py
```

This loads all CSV files from `datasets/csv/` including database, schema, table, column metadata, foreign keys, queries, and business glossary.

See [semantic_graph/connectors/csv/README.md](../semantic_graph/connectors/csv/README.md) for CSV file format specifications.

#### `bigquery.py` - BigQuery Schema Extractor
Extract metadata from BigQuery datasets and load into Neo4j.

**Usage:**
```bash
# Load BigQuery metadata with embeddings
python bigquery.py

# Skip embedding generation
python bigquery.py --skip-embeddings
```

#### `dataplex.py` - Google Dataplex Connector
Extract metadata from Google Cloud Dataplex catalog.

#### `bigquery_query_log_db.py` - Query Log from BigQuery
Extract query lineage from BigQuery INFORMATION_SCHEMA.

#### `bigquery_query_log_file.py` - Query Log from File
Load query lineage from exported JSON files.

### Embedding Generation

#### `sync_embeddings.py` - Synchronous Embedding Generation
Generate embeddings for nodes synchronously using OpenAI.

#### `async_embeddings.py` - Asynchronous Embedding Generation
Generate embeddings for nodes asynchronously for better performance.

## Setup

All examples require a `.env` file with the following variables:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j

# OpenAI (for embeddings)
OPENAI_API_KEY=your-api-key

# Google Cloud (for BigQuery/Dataplex examples)
GCP_PROJECT_ID=your-project-id
BIGQUERY_DATASET_ID=your-dataset-id
```