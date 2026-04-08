"""Pytest fixtures for CSV connector integration tests."""

import os
import shutil
import tempfile
from pathlib import Path

import pytest
from neo4j import GraphDatabase
from testcontainers.neo4j import Neo4jContainer

# Use community edition (more stable, faster startup)
neo4j_container = Neo4jContainer("neo4j:5.26.23")


@pytest.fixture(scope="module", autouse=True)
def setup(request):
    """Start Neo4j container once per test module."""
    print("\nStarting Neo4j container...")
    neo4j_container.start()
    print(f"Neo4j container started at {neo4j_container.get_connection_url()}")

    def remove_container():
        print("\nStopping Neo4j container...")
        try:
            if hasattr(neo4j_container, "_container") and neo4j_container._container:
                neo4j_container.stop()
        except Exception as e:
            print(f"Error stopping container: {e}")

    request.addfinalizer(remove_container)

    # Set environment variables
    os.environ["NEO4J_URI"] = neo4j_container.get_connection_url()
    os.environ["NEO4J_HOST"] = neo4j_container.get_container_host_ip()
    os.environ["NEO4J_PORT"] = str(neo4j_container.get_exposed_port(7687))

    return neo4j_container


@pytest.fixture
def neo4j_driver(setup: Neo4jContainer):
    """Provide a Neo4j driver for each test, with database cleanup."""
    driver = GraphDatabase.driver(setup.get_connection_url(), auth=(setup.username, setup.password))

    # Clean up database before test
    with driver.session(database="neo4j") as session:
        session.run("MATCH (n) DETACH DELETE n")

    try:
        yield driver
    finally:
        # Clean up database after test
        with driver.session(database="neo4j") as session:
            session.run("MATCH (n) DETACH DELETE n")
        driver.close()


@pytest.fixture
def temp_csv_dir():
    """
    Provide a temporary directory for CSV files.

    Yields:
    ------
    Path
        Path to temporary directory
    """
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_database_csv(temp_csv_dir):
    """Create sample database_info.csv file."""
    csv_content = """database_id,name,platform,service,description
my-project,My Project,GCP,BIGQUERY,Test database
"""
    csv_path = temp_csv_dir / "database_info.csv"
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def sample_schema_csv(temp_csv_dir):
    """Create sample schema_info.csv file."""
    csv_content = """database_id,schema_id,name,description
my-project,sales,Sales,Sales schema
my-project,analytics,Analytics,Analytics schema
"""
    csv_path = temp_csv_dir / "schema_info.csv"
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def sample_table_csv(temp_csv_dir):
    """Create sample table_info.csv file."""
    csv_content = """database_id,schema_id,table_name,description
my-project,sales,orders,Orders table
my-project,sales,customers,Customers table
my-project,analytics,summary,Summary table
"""
    csv_path = temp_csv_dir / "table_info.csv"
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def sample_column_csv(temp_csv_dir):
    """Create sample column_info.csv file."""
    csv_content = """database_id,schema_id,table_name,column_name,data_type,is_nullable,is_primary_key,is_foreign_key,description
my-project,sales,orders,order_id,STRING,false,true,false,Order ID
my-project,sales,orders,customer_id,STRING,false,false,true,Customer ID
my-project,sales,orders,total,FLOAT64,true,false,false,Order total
my-project,sales,customers,customer_id,STRING,false,true,false,Customer ID
my-project,sales,customers,name,STRING,false,false,false,Customer name
"""
    csv_path = temp_csv_dir / "column_info.csv"
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def sample_references_csv(temp_csv_dir):
    """Create sample column_references_info.csv file."""
    csv_content = """source_database_id,source_schema_id,source_table_name,source_column_name,target_database_id,target_schema_id,target_table_name,target_column_name,criteria
my-project,sales,orders,customer_id,my-project,sales,customers,customer_id,orders.customer_id = customers.customer_id
"""
    csv_path = temp_csv_dir / "column_references_info.csv"
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def sample_value_csv(temp_csv_dir):
    """Create sample value_info.csv file."""
    csv_content = """database_id,schema_id,table_name,column_name,value
my-project,sales,customers,name,John Doe
my-project,sales,customers,name,Jane Smith
my-project,sales,customers,name,Bob Johnson
"""
    csv_path = temp_csv_dir / "value_info.csv"
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def sample_query_csv(temp_csv_dir):
    """Create sample query_info.csv file."""
    csv_content = """query_id,content,description
q001,SELECT * FROM sales.orders WHERE order_id = '123',Get order by ID
q002,SELECT customer_id FROM sales.orders,Get customer IDs
"""
    csv_path = temp_csv_dir / "query_info.csv"
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def sample_query_table_csv(temp_csv_dir):
    """Create sample query_table_info.csv file."""
    csv_content = """query_id,table_id
q001,my-project.sales.orders
q002,my-project.sales.orders
"""
    csv_path = temp_csv_dir / "query_table_info.csv"
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def sample_query_column_csv(temp_csv_dir):
    """Create sample query_column_info.csv file."""
    csv_content = """query_id,column_id
q001,my-project.sales.orders.order_id
q002,my-project.sales.orders.customer_id
"""
    csv_path = temp_csv_dir / "query_column_info.csv"
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def sample_glossary_csv(temp_csv_dir):
    """Create sample glossary_info.csv file."""
    csv_content = """glossary_id,name,description
sales_glossary,Sales Glossary,Sales business terms
"""
    csv_path = temp_csv_dir / "glossary_info.csv"
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def sample_category_csv(temp_csv_dir):
    """Create sample category_info.csv file."""
    csv_content = """glossary_id,category_id,name,description
sales_glossary,metrics,Metrics,Sales metrics
"""
    csv_path = temp_csv_dir / "category_info.csv"
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def sample_business_term_csv(temp_csv_dir):
    """Create sample business_term_info.csv file."""
    csv_content = """category_id,term_id,name,description
metrics,arr,Annual Recurring Revenue,Yearly revenue
"""
    csv_path = temp_csv_dir / "business_term_info.csv"
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def all_sample_csvs(
    sample_database_csv,
    sample_schema_csv,
    sample_table_csv,
    sample_column_csv,
    sample_references_csv,
    sample_value_csv,
    sample_query_csv,
    sample_query_table_csv,
    sample_query_column_csv,
    sample_glossary_csv,
    sample_category_csv,
    sample_business_term_csv,
):
    """Fixture that ensures all sample CSV files are created."""
    return {
        "database": sample_database_csv,
        "schema": sample_schema_csv,
        "table": sample_table_csv,
        "column": sample_column_csv,
        "references": sample_references_csv,
        "value": sample_value_csv,
        "query": sample_query_csv,
        "query_table": sample_query_table_csv,
        "query_column": sample_query_column_csv,
        "glossary": sample_glossary_csv,
        "category": sample_category_csv,
        "business_term": sample_business_term_csv,
    }
