# Embeddings

Generates and stores vector embeddings for nodes in the semantic graph, enabling similarity-based retrieval by the MCP server tools.

## Overview

The embeddings module embeds the `description` field of graph nodes using OpenAI's embeddings API and writes the resulting vectors back to Neo4j. Vector indexes are created automatically per node label, and only nodes without an existing `embedding` property are processed — making reruns safe and incremental.

## Workflow

```
Neo4j (nodes missing embeddings)
        ↓  get_nodes_to_embed()
   DataFrame [id, node_label, description]
        ↓  create_embeddings_in_batches_{sync|async}()
   DataFrame [id, embedding]
        ↓  write_embeddings_to_graph()
Neo4j (embedding property set on each node)
```

1. **Fetch** — queries Neo4j for nodes of a given label where `description IS NOT NULL` and `embedding IS NULL`
2. **Embed** — calls the OpenAI embeddings API for each description, in batches
3. **Write** — sets the `embedding` vector property on each matched node using `db.create.setNodeVectorProperty`

A cosine-similarity vector index (e.g. `table_vector_index`) is created for each node label before embedding begins, if one does not already exist.

## Usage

### Sync

Use `OpenAI` (sync client) and call `run()`:

```python
from openai import OpenAI
from neo4j import GraphDatabase
from semantic_graph.embeddings.openai_embeddings import OpenAIEmbeddingWorkflow

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
client = OpenAI(api_key=OPENAI_API_KEY)

workflow = OpenAIEmbeddingWorkflow(
    neo4j_driver=driver,
    client=client,
    embedding_model="text-embedding-3-small",
    dimensions=768,
    database_name="neo4j",
)
workflow.run(node_labels=["Table", "Column"], batch_size=100)
```

### Async

Use `AsyncOpenAI` and call `arun()`. Within each batch, all embedding API calls are issued concurrently via `asyncio.gather`, making this significantly faster for large graphs:

```python
from openai import AsyncOpenAI
from neo4j import GraphDatabase
from semantic_graph.embeddings.openai_embeddings import OpenAIEmbeddingWorkflow

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
async_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

workflow = OpenAIEmbeddingWorkflow(
    neo4j_driver=driver,
    async_client=async_client,
    embedding_model="text-embedding-3-small",
    dimensions=768,
)
await workflow.arun(node_labels=["Table", "Column"], batch_size=100)
```

See [examples/sync_embeddings.py](../../examples/sync_embeddings.py) and [examples/async_embeddings.py](../../examples/async_embeddings.py) for runnable scripts with CLI argument support.

## Configuration

| Parameter | Default | Description |
|---|---|---|
| `embedding_model` | `"text-embedding-3-small"` | OpenAI model to use |
| `dimensions` | `768` | Vector dimensions (must match the vector index) |
| `database_name` | `"neo4j"` | Target Neo4j database |
| `node_labels` | `["Table", "Column"]` | Node labels to embed |
| `batch_size` | `100` | Nodes processed per batch |

**Required environment variable:** `OPENAI_API_KEY`

## Batch Processing

Nodes are processed in sequential batches of `batch_size`. Within each batch:

- **Sync**: descriptions are embedded one at a time
- **Async**: all descriptions in the batch are embedded concurrently

Failed individual embeddings (e.g. API errors) return `None` and are silently skipped — the node is left without an `embedding` property and will be picked up on the next run.

## Vector Index

`create_vector_index` (from `semantic_graph.ingest.indexes`) is called once per node label before embedding. It creates a Neo4j vector index using cosine similarity:

```
{node_label.lower()}_vector_index  →  ON (n:{NodeLabel}).embedding
    vector.dimensions: <dimensions>
    vector.similarity_function: cosine
```

The index creation is idempotent (`IF NOT EXISTS`), so it is safe to call on every run.

## Module Contents

| File | Purpose |
|---|---|
| `openai_embeddings.py` | `OpenAIEmbeddingWorkflow` class — orchestrates fetch, embed, and write |
| `utils.py` | `get_nodes_to_embed`, batch embedding helpers, `write_embeddings_to_graph` |
