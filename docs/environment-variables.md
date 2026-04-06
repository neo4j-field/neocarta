# Environment Variables

Copy `.env.example` to `.env` and fill in the values before running any example scripts, the MCP server, or the agent.

```bash
cp .env.example .env
```

---

## Neo4j

| Variable | Required | Default | Description |
|---|---|---|---|
| `NEO4J_URI` | Yes | — | Bolt/HTTP URI for the Neo4j instance (e.g. `bolt://localhost:7687`) |
| `NEO4J_USERNAME` | Yes | — | Neo4j username |
| `NEO4J_PASSWORD` | Yes | — | Neo4j password |
| `NEO4J_DATABASE` | No | `neo4j` | Target database name |

Used by: all example scripts, MCP server, agent, workflows, integration tests.

---

## OpenAI

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | OpenAI API key used for embedding generation and the LLM agent |

Used by: embeddings workflow, MCP server, agent, eval.

The MCP server also exposes two optional overrides (set via environment or `.env`):

| Variable | Required | Default | Description |
|---|---|---|---|
| `EMBEDDING_MODEL` | No | `text-embedding-3-small` | OpenAI embedding model name |
| `EMBEDDING_DIMENSIONS` | No | `768` | Embedding vector dimensions — must match the Neo4j vector index |

> If you change `EMBEDDING_DIMENSIONS`, re-run the embeddings workflow against a fresh Neo4j database. Existing vector indexes are not updated automatically.

---

## Google Cloud Platform

| Variable | Required | Default | Description |
|---|---|---|---|
| `GCP_PROJECT_ID` | Yes (GCP workflows) | — | GCP project ID (string, e.g. `my-project`) |
| `GCP_PROJECT_NUMBER` | Yes (Dataplex) | — | Numeric GCP project number |

Used by: BigQuery schema connector, BigQuery logs connector, Dataplex connector, eval.

Authentication uses [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials). Run `gcloud auth application-default login` before using any GCP connector.

---

## BigQuery

| Variable | Required | Default | Description |
|---|---|---|---|
| `BIGQUERY_DATASET_ID` | Yes (BigQuery workflows) | — | Dataset ID to extract metadata from (e.g. `demo_ecommerce`) |
| `BIGQUERY_LOCATION` | No | — | BigQuery dataset location (e.g. `us`, `eu`) |
| `BIGQUERY_REGION` | No | `region-us` | Region string used when querying `INFORMATION_SCHEMA` job logs (e.g. `region-us`, `region-eu`) |

Used by: BigQuery schema connector, BigQuery logs connector, eval.

---

## Dataplex

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATAPLEX_LOCATION` | Yes (Dataplex workflows) | — | Location of the Dataplex glossary (e.g. `us`, `us-central1`) |
| `DATAPLEX_GLOSSARY_ID` | Yes (Dataplex workflows) | — | ID of the Dataplex Business Glossary to import terms from |

Used by: Dataplex connector, dataset setup scripts.

---

## Quick reference by component

| Component | Required variables |
|---|---|
| CSV connector | `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` |
| BigQuery schema connector | + `GCP_PROJECT_ID`, `BIGQUERY_DATASET_ID` |
| BigQuery logs connector | + `GCP_PROJECT_ID`, `BIGQUERY_DATASET_ID`, `BIGQUERY_REGION` |
| Dataplex connector | + `GCP_PROJECT_ID`, `GCP_PROJECT_NUMBER`, `DATAPLEX_LOCATION`, `DATAPLEX_GLOSSARY_ID` |
| Embeddings workflow | + `OPENAI_API_KEY` |
| MCP server | `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `OPENAI_API_KEY` |
| Agent (`run_agent.py`) | `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`, `OPENAI_API_KEY` |
| Eval | `GCP_PROJECT_ID`, `OPENAI_API_KEY` |