from semantic_graph.ingest.constraints import (
    database_id_unique_constraint,
    database_id_key_constraint,
    schema_id_unique_constraint,
    schema_id_key_constraint,
    value_id_unique_constraint,
    value_id_key_constraint,
)

table_id_unique_constraint = """
CREATE CONSTRAINT table_id_constraint IF NOT EXISTS
FOR (t:Table) REQUIRE t.id IS UNIQUE;
"""

table_id_key_constraint = table_id_unique_constraint.replace("UNIQUE", "NODE KEY")

column_id_unique_constraint = """
CREATE CONSTRAINT column_id_constraint IF NOT EXISTS
FOR (c:Column) REQUIRE c.id IS UNIQUE;
"""

column_id_key_constraint = column_id_unique_constraint.replace("UNIQUE", "NODE KEY")

glossary_id_unique_constraint = """
CREATE CONSTRAINT glossary_id_constraint IF NOT EXISTS
FOR (g:Glossary) REQUIRE g.id IS UNIQUE;
"""

glossary_id_key_constraint = glossary_id_unique_constraint.replace("UNIQUE", "NODE KEY")

business_term_id_unique_constraint = """
CREATE CONSTRAINT business_term_id_constraint IF NOT EXISTS
FOR (b:BusinessTerm) REQUIRE b.id IS UNIQUE;
"""

business_term_id_key_constraint = business_term_id_unique_constraint.replace("UNIQUE", "NODE KEY")


category_id_unique_constraint = """
CREATE CONSTRAINT category_id_constraint IF NOT EXISTS
FOR (c:Category) REQUIRE c.id IS UNIQUE;
"""

category_id_key_constraint = category_id_unique_constraint.replace("UNIQUE", "NODE KEY")

query_id_unique_constraint = """
CREATE CONSTRAINT query_id_constraint IF NOT EXISTS
FOR (q:Query) REQUIRE q.id IS UNIQUE;
"""

query_id_key_constraint = query_id_unique_constraint.replace("UNIQUE", "NODE KEY")

UNIQUE_CONSTRAINTS_LOOKUP = {
    "Database": database_id_unique_constraint,
    "Schema": schema_id_unique_constraint,
    "Table": table_id_unique_constraint,
    "Column": column_id_unique_constraint,
    "Value": value_id_unique_constraint,
    "Glossary": glossary_id_unique_constraint,
    "Category": category_id_unique_constraint,
    "BusinessTerm": business_term_id_unique_constraint,
    "Query": query_id_unique_constraint,
}

KEY_CONSTRAINTS_LOOKUP = {
    "Database": database_id_key_constraint,
    "Schema": schema_id_key_constraint,
    "Table": table_id_key_constraint,
    "Column": column_id_key_constraint,
    "Value": value_id_key_constraint,
    "Glossary": glossary_id_key_constraint,
    "Category": category_id_key_constraint,
    "BusinessTerm": business_term_id_key_constraint,
    "Query": query_id_key_constraint,
}

