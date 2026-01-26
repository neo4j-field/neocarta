from neo4j import Driver, RoutingControl

database_id_unique_constraint = """
CREATE CONSTRAINT database_id_constraint
FOR (d:Database) REQUIRE d.id IS UNIQUE;
"""

database_id_key_constraint = database_id_unique_constraint.replace("UNIQUE", "NODE KEY")

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

def is_enterprise_edition(neo4j_driver: Driver) -> bool:
    try:
        results = neo4j_driver.execute_query(
            query_="""
call dbms.components()
yield name, versions, edition
where name = "Neo4j Kernel"
return name, versions, edition
""",
            routing_=RoutingControl.READ,
            result_transformer_=lambda x: x.data()
        )
        return results[0]['edition'] == 'enterprise'
    except Exception as e:
        print(f"Error checking enterprise edition: {e}")
        return False
    

def write_neo4j_constraints(neo4j_driver: Driver) -> dict:
    """Write constraints to the database according to which edition is being used.

    Parameters
    ----------
    neo4j_driver: Driver
        The Neo4j driver to write constraints to.

    Returns
    -------
    dict
        The summary of the constraints written.
    """
    
    is_enterprise = is_enterprise_edition(neo4j_driver)
    summaries = [{"enterprise_edition": is_enterprise}]

    if is_enterprise:
        # use key constraints for enterprise edition
        for c in [database_id_key_constraint, table_id_key_constraint, column_id_key_constraint]:
            _, summary, _ = neo4j_driver.execute_query(
                query_=c,
                routing_=RoutingControl.WRITE
            )
            summaries.append(summary.counters.__dict__)
    else:
        # use unique constraints for community edition, node keys are not supported
        for c in [database_id_unique_constraint, table_id_unique_constraint, column_id_unique_constraint]:
            _, summary, _ = neo4j_driver.execute_query(
                query_=c,
                routing_=RoutingControl.WRITE
            )
            summaries.append(summary.counters.__dict__)
    return summaries