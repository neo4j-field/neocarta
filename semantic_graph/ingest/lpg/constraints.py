"""
Cypher constraint queries for LPG metadata nodes.
Constraints ensure uniqueness and data integrity in the graph database.
"""

from semantic_graph.ingest.constraints import (
    database_id_key_constraint,
    database_id_unique_constraint,
    schema_id_key_constraint,
    schema_id_unique_constraint,
    value_id_key_constraint,
    value_id_unique_constraint,
)

node_id_unique_constraint = """
CREATE CONSTRAINT node_id_constraint IF NOT EXISTS
FOR (n:Node) REQUIRE n.id IS UNIQUE;
"""

node_id_key_constraint = node_id_unique_constraint.replace("UNIQUE", "NODE KEY")

relationship_id_unique_constraint = """
CREATE CONSTRAINT relationship_id_constraint IF NOT EXISTS
FOR (r:Relationship) REQUIRE r.id IS UNIQUE;
"""

relationship_id_key_constraint = relationship_id_unique_constraint.replace("UNIQUE", "NODE KEY")

property_id_unique_constraint = """
CREATE CONSTRAINT property_id_constraint IF NOT EXISTS
FOR (p:Property) REQUIRE p.id IS UNIQUE;
"""

property_id_key_constraint = property_id_unique_constraint.replace("UNIQUE", "NODE KEY")

UNIQUE_CONSTRAINTS_LOOKUP = {
    "Database": database_id_unique_constraint,
    "Schema": schema_id_unique_constraint,
    "Node": node_id_unique_constraint,
    "Relationship": relationship_id_unique_constraint,
    "Property": property_id_unique_constraint,
    "Value": value_id_unique_constraint,
}

KEY_CONSTRAINTS_LOOKUP = {
    "Database": database_id_key_constraint,
    "Schema": schema_id_key_constraint,
    "Node": node_id_key_constraint,
    "Relationship": relationship_id_key_constraint,
    "Property": property_id_key_constraint,
    "Value": value_id_key_constraint,
}
