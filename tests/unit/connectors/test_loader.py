import pytest

from semantic_graph.data_model.rdbms import Database
from semantic_graph.ingest.utils import (
    _build_node_ingest_query,
    _build_relationship_ingest_query,
    _validate_properties_list,
)


def test_validate_properties_list_valid():
    _validate_properties_list(Database, ["name", "description", "service", "platform"])
    assert True


def test_validate_properties_list_invalid():
    with pytest.raises(ValueError, match="invalid"):
        _validate_properties_list(Database, ["name", "description", "platform", "invalid"])


def test_build_node_ingest_query_no_overwrite():
    query = _build_node_ingest_query(
        "Database", False, ["name", "description", "service", "platform"]
    )
    assert (
        query
        == """
UNWIND $rows as row
MERGE (n:Database {id: row.id})
ON CREATE
    SET n.name = row.name,
        n.description = row.description,
        n.service = row.service,
        n.platform = row.platform"""
    )


def test_build_node_ingest_query_overwrite():
    query = _build_node_ingest_query(
        "Database", True, ["name", "description", "service", "platform"]
    )
    assert (
        query
        == """
UNWIND $rows as row
MERGE (n:Database {id: row.id})
SET n.name = row.name,
    n.description = row.description,
    n.service = row.service,
    n.platform = row.platform"""
    )


def test_build_node_ingest_query_no_properties():
    query = _build_node_ingest_query("Database", False, [])
    assert (
        query
        == """
UNWIND $rows as row
MERGE (n:Database {id: row.id})"""
    )


def test_build_node_ingest_query_overwrite_one_property():
    query = _build_node_ingest_query("Database", True, ["name"])
    assert (
        query
        == """
UNWIND $rows as row
MERGE (n:Database {id: row.id})
SET n.name = row.name"""
    )


def test_build_relationship_ingest_query_no_overwrite():
    query = _build_relationship_ingest_query(
        "HAS_SCHEMA",
        "Database",
        "Schema",
        "database_id",
        "schema_id",
        False,
        ["name", "description"],
    )
    assert (
        query
        == """
UNWIND $rows as row
MATCH (n1:Database {id: row.database_id})
MATCH (n2:Schema {id: row.schema_id})
MERGE (n1)-[r:HAS_SCHEMA]->(n2)
ON CREATE
    SET r.name = row.name,
        r.description = row.description"""
    )


def test_build_relationship_ingest_query_overwrite():
    query = _build_relationship_ingest_query(
        "HAS_SCHEMA",
        "Database",
        "Schema",
        "database_id",
        "schema_id",
        True,
        ["name", "description"],
    )
    assert (
        query
        == """
UNWIND $rows as row
MATCH (n1:Database {id: row.database_id})
MATCH (n2:Schema {id: row.schema_id})
MERGE (n1)-[r:HAS_SCHEMA]->(n2)
SET r.name = row.name,
    r.description = row.description"""
    )


def test_build_relationship_ingest_query_no_properties():
    query = _build_relationship_ingest_query(
        "HAS_SCHEMA", "Database", "Schema", "database_id", "schema_id", False, []
    )
    assert (
        query
        == """
UNWIND $rows as row
MATCH (n1:Database {id: row.database_id})
MATCH (n2:Schema {id: row.schema_id})
MERGE (n1)-[r:HAS_SCHEMA]->(n2)"""
    )
