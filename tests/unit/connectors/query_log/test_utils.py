from semantic_graph.connectors.query_log.utils import parse_bigquery_query_log_json, parse_sql_query

def test_parse_bigquery_query_log_json():
    query_log_file = "tests/unit/connectors/query_log/test_bigquery_query_log.json"
    parsed = parse_bigquery_query_log_json(query_log_file)
    assert parsed["query_info"].shape[0] == 1
    assert parsed["table_info"].shape[0] == 3

def test_parse_sql_query_bigquery_simple():
    query = "SELECT * FROM `example-project-id.demo_ecommerce.orders`"
    query_id = "1234567890"
    parsed = parse_sql_query(query, query_id, "bigquery")
    assert len(parsed["table_info"]) == 1
    assert len(parsed["column_info"]) == 0 # no columns named
    assert len(parsed["references_info"]) == 0

def test_parse_sql_query_bigquery():
    query = """SELECT o.order_id, oi.order_item_id, p.product_name, oi.quantity, oi.price
    FROM `example-project-id.demo_ecommerce.orders` AS o
    JOIN `example-project-id.demo_ecommerce.order_items` AS oi ON o.order_id = oi.order_id
    JOIN `example-project-id.demo_ecommerce.products` AS p ON oi.product_id = p.product_id;"""
    query_id = "1234567890"
    parsed = parse_sql_query(query, query_id, "bigquery")
    assert len(parsed["table_info"]) == 3
    assert len(parsed["column_info"]) == 9
    assert len(parsed["references_info"]) == 2


def test_parse_sql_query_filters_invalid_references_with_unnest():
    """Test that queries with UNNEST that create malformed references are filtered out"""
    query = """
    SELECT
      child.name,
      child.id AS child_id,
      child.author_name AS child_author,
      parent_hash AS parent_id_hash,
      parent.author_name AS parent_author
    FROM `example-project.example_dataset.commits` child,
      UNNEST(child.parent_ids) AS parent_hash
    JOIN `example-project.example_dataset.commits` parent
      ON parent_hash = parent.id
      AND child.name = parent.name
    WHERE child.name = 'example-name'
    ORDER BY child.created_date DESC
    LIMIT 15
    """
    query_id = "test123"
    parsed = parse_sql_query(query, query_id, "bigquery")

    # Should not fail with NoneType error
    assert parsed is not None

    # Check that references_info only contains valid references (with both column IDs)
    for ref in parsed["references_info"]:
        assert ref["left_column_id"] is not None, "left_column_id should not be None"
        assert ref["right_column_id"] is not None, "right_column_id should not be None"
        assert ref["left_column_id"] != "", "left_column_id should not be empty string"
        assert ref["right_column_id"] != "", "right_column_id should not be empty string"


def test_parse_sql_query_only_returns_complete_references():
    """Test that only references with both column IDs are returned"""
    # This query has a simple join that should parse correctly
    query = """
    SELECT a.id, b.id
    FROM `project.dataset.table_a` AS a
    JOIN `project.dataset.table_b` AS b ON a.id = b.id
    """
    query_id = "test456"
    parsed = parse_sql_query(query, query_id, "bigquery")

    # Should have 1 valid reference
    assert len(parsed["references_info"]) == 1

    # Verify the reference has both IDs
    ref = parsed["references_info"][0]
    assert ref["left_column_id"] is not None
    assert ref["right_column_id"] is not None
    assert ref["left_column_id"] != ""
    assert ref["right_column_id"] != ""


def test_parse_sql_query_uses_default_project_id():
    """Test that default_project_id is used when table references don't include project"""
    query = """
    SELECT repo_name, license
    FROM `github.licenses`
    JOIN `github.sample_repos` ON licenses.repo_name = sample_repos.repo_name
    """
    query_id = "test789"
    parsed = parse_sql_query(
        query,
        query_id,
        "bigquery",
        default_project_id="my-gcp-project"
    )

    assert len(parsed["table_info"]) == 2

    for table in parsed["table_info"]:
        assert table["project_id"] == "my-gcp-project"
        assert table["table_id"].startswith("my-gcp-project.")
        assert not table["table_id"].startswith(".")

    for col in parsed["column_info"]:
        assert col["column_id"].startswith("my-gcp-project.")
        assert not col["column_id"].startswith(".")


def test_parse_sql_query_explicit_project_overrides_default():
    """Test that explicit project IDs in queries override the default"""
    query = """
    SELECT o.order_id
    FROM `example-project-id.demo_ecommerce.orders` AS o
    """
    query_id = "test101112"
    parsed = parse_sql_query(
        query,
        query_id,
        "bigquery",
        default_project_id="different-project"
    )

    assert len(parsed["table_info"]) == 1
    table = parsed["table_info"][0]
    assert table["project_id"] == "example-project-id"
    assert table["table_id"] == "example-project-id.demo_ecommerce.orders"