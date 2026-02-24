import pytest
from connectors.query_log.transform import QueryLogTransformer
from connectors.query_log.extract import QueryLogExtractor
from connectors.query_log.utils import parse_bigquery_query_log_json
import pandas as pd

@pytest.fixture(scope="function")
def query_log_extractor() -> QueryLogExtractor:
    return QueryLogExtractor()

@pytest.fixture(scope="function")
def query_log_extractor_with_cache() -> QueryLogExtractor:
    e = QueryLogExtractor()

    query_info_records = [
        {
            'project_id': 'example-project-id',
            'query': 'SELECT o.order_id, oi.order_item_id, p.product_name, oi.quantity, oi.price\nFROM `example-project-id.demo_ecommerce.orders` AS o\nJOIN `example-project-id.demo_ecommerce.order_items` AS oi ON o.order_id = oi.order_id\nJOIN `example-project-id.demo_ecommerce.products` AS p ON oi.product_id = p.product_id;',
            'query_id': 'e45079ee36de11097b070f3e0b6dbc5d365827af3c19a3737cf3331daca26e76'
        },
    ]

    table_info_records = [
        {
            'platform': 'GCP',
            'service': 'BIGQUERY',
            'table_id': 'example-project-id.demo_ecommerce.orders',
            'table_name': 'orders',
            'dataset_id': 'example-project-id.demo_ecommerce',
            'dataset_name': 'demo_ecommerce',
            'project_name': 'example-project-id',
            'project_id': 'example-project-id',
            'table_alias': 'o',
            'query_id': 'e45079ee36de11097b070f3e0b6dbc5d365827af3c19a3737cf3331daca26e76'
        },
        {
            'platform': 'GCP',
            'service': 'BIGQUERY',
            'table_id': 'example-project-id.demo_ecommerce.order_items',
            'table_name': 'order_items',
            'dataset_id': 'example-project-id.demo_ecommerce',
            'dataset_name': 'demo_ecommerce',
            'project_name': 'example-project-id',
            'project_id': 'example-project-id',
            'table_alias': 'oi',
            'query_id': 'e45079ee36de11097b070f3e0b6dbc5d365827af3c19a3737cf3331daca26e76'
        },
        {
            'platform': 'GCP',
            'service': 'BIGQUERY',
            'table_id': 'example-project-id.demo_ecommerce.products',
            'table_name': 'products',
            'dataset_id': 'example-project-id.demo_ecommerce',
            'dataset_name': 'demo_ecommerce',
            'project_name': 'example-project-id',
            'project_id': 'example-project-id',
            'table_alias': 'p',
            'query_id': 'e45079ee36de11097b070f3e0b6dbc5d365827af3c19a3737cf3331daca26e76'
        },
    ]

    column_info_records = [
        {
            'query_id': 'e45079ee36de11097b070f3e0b6dbc5d365827af3c19a3737cf3331daca26e76',
            'table_id': 'example-project-id.demo_ecommerce.orders',
            'table_name': 'orders',
            'table_alias': 'o',
            'column_id': 'example-project-id.demo_ecommerce.orders.order_id',
            'column_name': 'order_id'
        },
        {
            'query_id': 'e45079ee36de11097b070f3e0b6dbc5d365827af3c19a3737cf3331daca26e76',
            'table_id': 'example-project-id.demo_ecommerce.orders',
            'table_name': 'orders',
            'table_alias': 'o',
            'column_id': 'example-project-id.demo_ecommerce.orders.order_date',
            'column_name': 'order_date'
        },
        {
            'query_id': 'e45079ee36de11097b070f3e0b6dbc5d365827af3c19a3737cf3331daca26e76',
            'table_id': 'example-project-id.demo_ecommerce.orders',
            'table_name': 'orders',
            'table_alias': 'o',
            'column_id': 'example-project-id.demo_ecommerce.orders.customer_id',
            'column_name': 'customer_id'
        },
        {
            'query_id': 'e45079ee36de11097b070f3e0b6dbc5d365827af3c19a3737cf3331daca26e76',
            'table_id': 'example-project-id.demo_ecommerce.orders',
            'table_name': 'orders',
            'table_alias': 'o',
            'column_id': 'example-project-id.demo_ecommerce.orders.total_amount',
            'column_name': 'total_amount'
        },
        {
            'query_id': 'e45079ee36de11097b070f3e0b6dbc5d365827af3c19a3737cf3331daca26e76',
            'table_id': 'example-project-id.demo_ecommerce.order_items',
            'table_name': 'order_items',
            'table_alias': 'oi',
            'column_id': 'example-project-id.demo_ecommerce.order_items.order_item_id',
            'column_name': 'order_item_id'
        },
        {
            'query_id': 'e45079ee36de11097b070f3e0b6dbc5d365827af3c19a3737cf3331daca26e76',
            'table_id': 'example-project-id.demo_ecommerce.order_items',
            'table_name': 'order_items',
            'table_alias': 'oi',
            'column_id': 'example-project-id.demo_ecommerce.order_items.order_id',
            'column_name': 'order_id'
        },
        {
            'query_id': 'e45079ee36de11097b070f3e0b6dbc5d365827af3c19a3737cf3331daca26e76',
            'table_id': 'example-project-id.demo_ecommerce.order_items',
            'table_name': 'order_items',
            'table_alias': 'oi',
            'column_id': 'example-project-id.demo_ecommerce.order_items.product_id',
            'column_name': 'product_id'
        },
        {
            'query_id': 'e45079ee36de11097b070f3e0b6dbc5d365827af3c19a3737cf3331daca26e76',
            'table_id': 'example-project-id.demo_ecommerce.order_items',
            'table_name': 'order_items',
            'table_alias': 'oi',
            'column_id': 'example-project-id.demo_ecommerce.order_items.quantity',
            'column_name': 'quantity'
        },
    ]
    
    column_references_info_records = [
        {
            'left_table_name': 'orders',
            'left_table_id': 'example-project-id.demo_ecommerce.orders',
            'left_table_alias': 'o',
            'left_column_name': 'order_id',
            'left_column_id': 'example-project-id.demo_ecommerce.orders.order_id',
            'right_table_name': 'order_items',
            'right_table_id': 'example-project-id.demo_ecommerce.order_items',
            'right_table_alias': 'oi',
            'right_column_name': 'order_id',
            'right_column_id': 'example-project-id.demo_ecommerce.order_items.order_id',
            'criteria': 'o.order_id = oi.order_id'
        },
        {
            'left_table_name': 'order_items',
            'left_table_id': 'example-project-id.demo_ecommerce.order_items',
            'left_table_alias': 'oi',
            'left_column_name': 'product_id',
            'left_column_id': 'example-project-id.demo_ecommerce.order_items.product_id',
            'right_table_name': 'products',
            'right_table_id': 'example-project-id.demo_ecommerce.products',
            'right_table_alias': 'p',
            'right_column_name': 'product_id',
            'right_column_id': 'example-project-id.demo_ecommerce.products.product_id',
            'criteria': 'oi.product_id = p.product_id'
        },
    ]

    e._cache["query_info"] = pd.DataFrame(query_info_records)
    e._cache["table_info"] = pd.DataFrame(table_info_records)
    e._cache["column_info"] = pd.DataFrame(column_info_records)
    e._cache["column_references_info"] = pd.DataFrame(column_references_info_records)
    
    return e

@pytest.fixture(scope="function")
def query_log_transformer() -> QueryLogTransformer:
    return QueryLogTransformer()