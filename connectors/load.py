"""Common ingest functions for Neo4j."""

from neo4j import Driver, RoutingControl
from data_model.core import (
    Database,
    Table,
    Column,
    ContainsTable,
    HasColumn,
    References,
)
from data_model.expanded import Value, HasValue


def load_database_nodes(
    database_nodes: list[Database], neo4j_driver: Driver, database_name: str = "neo4j"
) -> dict:
    _, summary, _ = neo4j_driver.execute_query(
        query_="""
    UNWIND $rows as row
    MERGE (d:Database {id: row.id})
    ON CREATE
        SET d.name = row.name, 
            d.description = row.description
    """,
        parameters_={"rows": [n.model_dump() for n in database_nodes]},
        routing_=RoutingControl.WRITE,
        database_=database_name,
    )

    return summary.counters.__dict__


def load_table_nodes(
    table_nodes: list[Table], neo4j_driver: Driver, database_name: str = "neo4j"
) -> dict:
    _, summary, _ = neo4j_driver.execute_query(
        query_="""
    UNWIND $rows as row
    MERGE (t:Table {id: row.id})
    ON CREATE
        SET t.name = row.name, 
            t.description = row.description
    """,
        parameters_={"rows": [n.model_dump() for n in table_nodes]},
        routing_=RoutingControl.WRITE,
        database_=database_name,
    )
    return summary.counters.__dict__


def load_column_nodes(
    column_nodes: list[Column], neo4j_driver: Driver, database_name: str = "neo4j"
) -> dict:
    _, summary, _ = neo4j_driver.execute_query(
        query_="""
    UNWIND $rows as row
    MERGE (c:Column {id: row.id})
    ON CREATE
        SET c.name = row.name, 
            c.description = row.description, 
            c.type = row.type, 
            c.nullable = row.nullable, 
            c.is_primary_key = row.is_primary_key, 
            c.is_foreign_key = row.is_foreign_key
    """,
        parameters_={"rows": [n.model_dump() for n in column_nodes]},
        routing_=RoutingControl.WRITE,
        database_=database_name,
    )
    return summary.counters.__dict__


def load_value_nodes(
    value_nodes: list[Value],
    neo4j_driver: Driver,
    database_name: str = "neo4j",
) -> dict:
    """
    Load Value nodes into Neo4j.
    """

    _, summary, _ = neo4j_driver.execute_query(
        query_="""
    UNWIND $rows as row
    MERGE (v:Value {id: row.id})
    ON CREATE
        SET v.value = row.value
    """,
        parameters_={"rows": [n.model_dump() for n in value_nodes]},
        routing_=RoutingControl.WRITE,
        database_=database_name,
    )
    return summary.counters.__dict__


def load_contains_table_relationships(
    contains_table_relationships: list[ContainsTable],
    neo4j_driver: Driver,
    database_name: str = "neo4j",
) -> dict:
    _, summary, _ = neo4j_driver.execute_query(
        query_="""
    UNWIND $rows as row
    MATCH (d:Database {id: row.database_id})
    MATCH (t:Table {id: row.table_id})
    MERGE (d)-[:CONTAINS_TABLE]->(t)
    """,
        parameters_={"rows": [n.model_dump() for n in contains_table_relationships]},
        routing_=RoutingControl.WRITE,
        database_=database_name,
    )
    return summary.counters.__dict__


def load_has_column_relationships(
    has_column_relationships: list[HasColumn],
    neo4j_driver: Driver,
    database_name: str = "neo4j",
) -> dict:
    _, summary, _ = neo4j_driver.execute_query(
        query_="""
    UNWIND $rows as row
    MATCH (t:Table {id: row.table_id})
    MATCH (c:Column {id: row.column_id})
    MERGE (t)-[:HAS_COLUMN]->(c)
    """,
        parameters_={"rows": [n.model_dump() for n in has_column_relationships]},
        routing_=RoutingControl.WRITE,
        database_=database_name,
    )
    return summary.counters.__dict__


def load_references_relationships(
    references_relationships: list[References],
    neo4j_driver: Driver,
    database_name: str = "neo4j",
) -> dict:
    _, summary, _ = neo4j_driver.execute_query(
        query_="""
    UNWIND $rows as row
    MATCH (c1:Column {id: row.source_column_id})
    MATCH (c2:Column {id: row.target_column_id})
    MERGE (c1)-[:REFERENCES]->(c2)
    """,
        parameters_={"rows": [n.model_dump() for n in references_relationships]},
        routing_=RoutingControl.WRITE,
        database_=database_name,
    )
    return summary.counters.__dict__


def load_has_value_relationships(
    has_value_relationships: list[HasValue],
    neo4j_driver: Driver,
    database_name: str = "neo4j",
) -> dict:
    _, summary, _ = neo4j_driver.execute_query(
        query_="""
    UNWIND $rows as row
    MATCH (c:Column {id: row.column_id})
    MATCH (v:Value {id: row.value_id})
    MERGE (c)-[:HAS_VALUE]->(v)
    """,
        parameters_={"rows": [n.model_dump() for n in has_value_relationships]},
        routing_=RoutingControl.WRITE,
        database_=database_name,
    )
    return summary.counters.__dict__
