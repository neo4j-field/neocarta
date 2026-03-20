"""
Shared Cypher constraint queries for metadata nodes common across data models.
These constraints are used by both RDBMS and LPG data models.
"""

database_id_unique_constraint = """
CREATE CONSTRAINT database_id_constraint IF NOT EXISTS
FOR (d:Database) REQUIRE d.id IS UNIQUE;
"""

database_id_key_constraint = database_id_unique_constraint.replace("UNIQUE", "NODE KEY")

schema_id_unique_constraint = """
CREATE CONSTRAINT schema_id_constraint IF NOT EXISTS
FOR (s:Schema) REQUIRE s.id IS UNIQUE;
"""

schema_id_key_constraint = schema_id_unique_constraint.replace("UNIQUE", "NODE KEY")

value_id_unique_constraint = """
CREATE CONSTRAINT value_id_constraint IF NOT EXISTS
FOR (v:Value) REQUIRE v.id IS UNIQUE;
"""

value_id_key_constraint = value_id_unique_constraint.replace("UNIQUE", "NODE KEY")
