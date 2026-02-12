from neo4j import Driver, RoutingControl

database_id_unique_constraint = """
CREATE CONSTRAINT database_id_constraint
FOR (d:Database) REQUIRE d.id IS UNIQUE;
"""

database_id_key_constraint = database_id_unique_constraint.replace("UNIQUE", "NODE KEY")

schema_id_unique_constraint = """
CREATE CONSTRAINT schema_id_constraint
FOR (s:Schema) REQUIRE s.id IS UNIQUE;
"""

schema_id_key_constraint = schema_id_unique_constraint.replace("UNIQUE", "NODE KEY")

table_id_unique_constraint = """
CREATE CONSTRAINT table_id_constraint
FOR (t:Table) REQUIRE t.id IS UNIQUE;
"""

table_id_key_constraint = table_id_unique_constraint.replace("UNIQUE", "NODE KEY")

column_id_unique_constraint = """
CREATE CONSTRAINT column_id_constraint
FOR (c:Column) REQUIRE c.id IS UNIQUE;
"""

column_id_key_constraint = column_id_unique_constraint.replace("UNIQUE", "NODE KEY")


glossary_id_unique_constraint = """
CREATE CONSTRAINT glossary_id_constraint
FOR (g:Glossary) REQUIRE g.id IS UNIQUE;
"""

glossary_id_key_constraint = glossary_id_unique_constraint.replace("UNIQUE", "NODE KEY")

business_term_id_unique_constraint = """
CREATE CONSTRAINT business_term_id_constraint
FOR (b:BusinessTerm) REQUIRE b.id IS UNIQUE;
"""

business_term_id_key_constraint = business_term_id_unique_constraint.replace("UNIQUE", "NODE KEY")


category_id_unique_constraint = """
CREATE CONSTRAINT category_id_constraint
FOR (c:Category) REQUIRE c.id IS UNIQUE;
"""

category_id_key_constraint = category_id_unique_constraint.replace("UNIQUE", "NODE KEY")    

def is_enterprise_edition(neo4j_driver: Driver, database_name: str = "neo4j") -> bool:
    """
    Check if using enterprise edition of Neo4j.

    Parameters
    ----------
    neo4j_driver: Driver
        The Neo4j driver to use.
    database_name: str
        The name of the database to check the edition of.

    Returns
    -------
    bool
        True if the Neo4j database is running in enterprise edition, False otherwise.
    """
    try:
        results = neo4j_driver.execute_query(
            query_="""
call dbms.components()
yield name, versions, edition
where name = "Neo4j Kernel"
return name, versions, edition
""",
            routing_=RoutingControl.READ,
            result_transformer_=lambda x: x.data(),
            database_=database_name,
        )
        return results[0]["edition"] == "enterprise"
    except Exception as e:
        print(f"Error checking enterprise edition: {e}")
        return False


def write_neo4j_constraints(neo4j_driver: Driver, database_name: str = "neo4j") -> dict:
    """
    Write constraints to the database according to which edition is being used.

    Parameters
    ----------
    neo4j_driver: Driver
        The Neo4j driver to write constraints to.
    database_name: str
        The name of the database to write constraints to.

    Returns
    -------
    dict
        The summary of the constraints written.
    """

    is_enterprise = is_enterprise_edition(neo4j_driver, database_name)
    summaries = [{"enterprise_edition": is_enterprise}]

    if is_enterprise:
        # use key constraints for enterprise edition
        for c in [
            database_id_key_constraint,
            schema_id_key_constraint,
            table_id_key_constraint,
            column_id_key_constraint,
        ]:
            _, summary, _ = neo4j_driver.execute_query(
                query_=c, routing_=RoutingControl.WRITE, database_=database_name
            )
            summaries.append(summary.counters.__dict__)
    else:
        # use unique constraints for community edition, node keys are not supported
        for c in [
            database_id_unique_constraint,
            schema_id_unique_constraint,
            table_id_unique_constraint,
            column_id_unique_constraint,
        ]:
            _, summary, _ = neo4j_driver.execute_query(
                query_=c, routing_=RoutingControl.WRITE, database_=database_name
            )
            summaries.append(summary.counters.__dict__)
    return summaries
