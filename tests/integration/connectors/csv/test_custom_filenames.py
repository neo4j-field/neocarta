"""Test custom CSV filename functionality."""

import pytest


def test_custom_filename_in_constructor(neo4j_driver, temp_csv_dir):
    """Test that custom filenames can be specified in constructor."""
    from semantic_graph.connectors.csv.workflow import CSVWorkflow

    # Create CSV with custom name
    db_csv = """database_id,name
my-db,My Database
"""
    (temp_csv_dir / "custom_databases.csv").write_text(db_csv)

    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j",
        csv_file_map={"database": "custom_databases.csv"}
    )

    workflow.load_database_nodes()

    with neo4j_driver.session(database="neo4j") as session:
        result = session.run("MATCH (d:Database) RETURN count(d) as count")
        assert result.single()["count"] == 1


def test_custom_filename_in_method(neo4j_driver, temp_csv_dir):
    """Test that custom filenames can be specified per method call."""
    from semantic_graph.connectors.csv.workflow import CSVWorkflow

    # Create CSVs with custom names
    db_csv = """database_id,name
my-db,My Database
"""
    schema_csv = """database_id,schema_id,name
my-db,my-schema,My Schema
"""
    (temp_csv_dir / "alt_databases.csv").write_text(db_csv)
    (temp_csv_dir / "alt_schemas.csv").write_text(schema_csv)

    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j"
    )

    # Use custom filenames per method call
    workflow.load_database_nodes(csv_filename="alt_databases.csv")
    workflow.load_schema_nodes(csv_filename="alt_schemas.csv")

    with neo4j_driver.session(database="neo4j") as session:
        result = session.run("MATCH (d:Database) RETURN count(d) as count")
        assert result.single()["count"] == 1

        result = session.run("MATCH (s:Schema) RETURN count(s) as count")
        assert result.single()["count"] == 1


def test_custom_filename_in_run(neo4j_driver, temp_csv_dir):
    """Test that custom filenames can be specified in run() method."""
    from semantic_graph.connectors.csv.workflow import CSVWorkflow

    # Create minimal CSVs with custom names
    db_csv = """database_id
test-db
"""
    schema_csv = """database_id,schema_id
test-db,test-schema
"""
    (temp_csv_dir / "prod_databases.csv").write_text(db_csv)
    (temp_csv_dir / "prod_schemas.csv").write_text(schema_csv)

    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j"
    )

    # Override filenames for this run
    workflow.run(csv_file_map={
        "database": "prod_databases.csv",
        "schema": "prod_schemas.csv"
    })

    with neo4j_driver.session(database="neo4j") as session:
        result = session.run("MATCH (d:Database) RETURN count(d) as count")
        assert result.single()["count"] == 1

        result = session.run("MATCH (s:Schema) RETURN count(s) as count")
        assert result.single()["count"] == 1
