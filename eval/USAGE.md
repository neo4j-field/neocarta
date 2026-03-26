# Semantic Layer Evaluation - Usage Guide

This guide shows how to run the semantic layer evaluation to measure whether MCP-retrieved context produces equivalent SQL generation quality compared to full schema exposure, at reduced token cost.

## Quick Start

### 1. Persist the Schema Baseline

First, persist the full schema from the graph (one-time setup):

```bash
python -m eval.datasets.schema_registry graph \
  mcp_server/src/server.py \
  eval/datasets/schemas/demo_ecommerce_schema.json
```

This creates the `full_schema` baseline by querying the MCP server's `get_full_metadata_schema` tool and saving it to JSON.

### 2. Run the Evaluation

Run the evaluation on the default ecommerce dataset:

```bash
python -m eval.main
```

Or run on the GitHub dataset:

```bash
python -m eval.main --dataset github
```

Run with a random sample of questions (e.g., 20 samples):

```bash
python -m eval.main --dataset github --sample-size 20
```

Run with a specific random seed for reproducibility:

```bash
python -m eval.main --dataset github --sample-size 20 --seed 123
```

This will:
1. Load evaluation samples from the question bank (ecommerce: 10 samples, github: 100 samples)
2. Optionally sample a subset if `--sample-size` is specified
3. Start the MCP server session
4. For each sample:
   - **Semantic condition**: LLM uses MCP tools to retrieve relevant schema, generates SQL
   - **Full schema condition**: LLM gets complete schema, generates SQL
5. Score both conditions (structural, execution, tokens, retrieval)
6. Print comprehensive delta report

### 3. View Results

Results are saved to `eval/results/eval_results_{dataset}.json` (or `eval_results_{dataset}_n{sample_size}.json` if sampling).

## Understanding the Evaluation

### Two Conditions

| Condition | Context provided to LLM |
|---|---|
| `semantic` | MCP-retrieved chunks from semantic layer (dynamic per question) |
| `full_schema` | Complete schema from persisted JSON file (same for all questions) |

### Success Criteria

The evaluation gates on:
1. **Token reduction ≥ 50%**: Semantic layer uses at least 50% fewer tokens
2. **Object recall ≥ 90%**: Semantic layer retrieves 90%+ of required schema objects
3. **Semantic accuracy ≥ Full schema accuracy (within 5% tolerance)**: Semantic layer must be at least as accurate as full schema, allowing up to 5% degradation

All three gates must pass for the semantic layer to be considered successful.

**Note**: For large schemas, semantic context should *outperform* full schema (positive accuracy delta), as the focused context reduces noise and confusion from irrelevant tables.

### Metrics Measured

**SQL Accuracy**:
- Execution match: Do results match gold SQL?
- Structural match: Do tables/columns match?
- Faithfulness: Are generated tables/columns grounded in context?

**Token Efficiency**:
- Token reduction %: How many fewer tokens vs full schema?
- Token counts: Absolute tokens for each condition

**Retrieval Quality**:
- Object recall: What % of required tables/columns were retrieved?
- Object precision: What % of retrieved objects were actually used?

**Performance**:
- Latency: Time to generate SQL for each condition

## Project Structure

```
eval/
├── datasets/
│   ├── models.py              # EvalSample data model
│   ├── question_bank.py       # 10 evaluation queries
│   ├── schema_registry.py     # Schema persistence utilities
│   └── schemas/               # Persisted schema files
│       └── demo_ecommerce_schema.json
├── retrievers/
│   └── bigquery_schema_retriever.py  # Loads persisted full schema
├── sql_parser.py              # Sqlglot utilities for scoring
├── token_metrics.py           # Token counting
├── retrieval_metrics.py       # Recall/precision scoring
├── inference_metrics.py       # SQL execution scoring
├── runner.py                  # Evaluation orchestration
├── report.py                  # Report generation
├── main.py                    # CLI entry point
└── USAGE.md                   # This file
```

## Customization

### Adjust Success Thresholds

Edit `eval/report.py`:

```python
TARGET_TOKEN_REDUCTION = 0.50   # 50% token reduction target
OBJECT_RECALL_FLOOR = 0.90      # 90% object recall minimum
MIN_ACCURACY_TOLERANCE = -0.05  # Allow semantic to be up to 5% worse than full schema
```

The `MIN_ACCURACY_TOLERANCE` is the minimum acceptable delta (semantic - full_schema):
- `0.0` means semantic must be exactly as good or better
- `-0.05` means semantic can be up to 5% worse
- Positive deltas indicate semantic outperforms full schema (ideal for large schemas)

### Add More Questions

Edit `eval/datasets/question_bank.py` and add samples to `get_ecommerce_eval_samples()`.

### Use a Different Dataset

1. Persist the schema:
   ```bash
   python -m eval.datasets.schema_registry graph \
     mcp_server/src/server.py \
     eval/datasets/schemas/your_dataset_schema.json
   ```

2. Create a new question bank function

3. Update `eval/main.py` to use your question bank and schema

## Troubleshooting

### "Schema file not found"

Run the schema persistence step:
```bash
python -m eval.datasets.schema_registry graph \
  mcp_server/src/server.py \
  eval/datasets/schemas/demo_ecommerce_schema.json
```

### "MCP server connection failed"

Ensure:
- Neo4j is running
- Environment variables are set (.env file):
  - `NEO4J_URI`
  - `NEO4J_USERNAME`
  - `NEO4J_PASSWORD`
  - `NEO4J_DATABASE`
  - `OPENAI_API_KEY`
  - `GCP_PROJECT_ID`

### "BigQuery execution failed"

Ensure:
- BigQuery dataset `demo_ecommerce` exists
- GCP credentials are configured
- `GCP_PROJECT_ID` is set in .env

## Next Steps

- Review the [Implementation README](README.md) for architecture details
- Examine failed samples in `eval/results/eval_results.json`
- Tune retrieval parameters in the MCP server
- Add regression tests for production queries
