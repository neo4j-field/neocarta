# BigQuery Logs Extractor Unit Tests

This directory contains unit tests for the BigQuery Logs Extractor that don't require a database connection.

## Running Tests

```bash
# Run all logs extractor tests
pytest tests/unit/connectors/bigquery/logs/

# Run with verbose output
pytest tests/unit/connectors/bigquery/logs/ -v

# Run specific test
pytest tests/unit/connectors/bigquery/logs/test_extract.py::test_extract_query_logs_filters_failed_queries

# Run with coverage
pytest tests/unit/connectors/bigquery/logs/ --cov=semantic_graph.connectors.bigquery.logs
```

## Test Structure

### Fixtures (`conftest.py`)

1. **`mock_bigquery_client`** - Mock BigQuery client with project_id set
2. **`mock_query_logs_response`** - Sample query log data that simulates JOBS_BY_PROJECT response
3. **`mock_bq_logs_extractor`** - Extractor instance with mocked client
4. **`bq_logs_extractor_with_cache`** - Extractor with pre-populated cache after extraction

### Test Cases (`test_extract.py`)

- **Initialization tests** - Verify extractor setup
- **Query construction tests** - Verify SQL query building with timestamps
- **Filtering tests** - Test failed query filtering
- **Caching tests** - Verify data is cached correctly
- **Property tests** - Test all derived properties (database_info, schema_info, etc.)
- **Edge case tests** - Default timestamps, missing project_id

## Key Mocking Pattern

The tests mock the BigQuery client's query execution:

```python
# In conftest.py
mock_query_result = MagicMock()
mock_query_result.to_dataframe.return_value = mock_query_logs_response
mock_bigquery_client.query.return_value = mock_query_result
```

This allows testing without actual BigQuery API calls.

## Adding New Tests

To add new test cases:

1. **Add test data** to `mock_query_logs_response` fixture if needed
2. **Create test function** in `test_extract.py`
3. **Use fixtures** to get pre-configured extractor instances

Example:

```python
def test_custom_behavior(bq_logs_extractor_with_cache):
    """Test description."""
    result = bq_logs_extractor_with_cache.some_property
    assert result is not None
```

## Integration Tests

For tests that require actual BigQuery connection, create a separate `tests/integration/` directory.
