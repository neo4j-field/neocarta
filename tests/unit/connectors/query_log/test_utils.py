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