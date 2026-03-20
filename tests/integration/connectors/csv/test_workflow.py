"""Integration tests for CSV connector workflow."""

import pytest
from semantic_graph.connectors.csv import CSVWorkflow


def test_load_database_nodes(neo4j_driver, temp_csv_dir, sample_database_csv):
    """Test that database nodes are loaded correctly."""
    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j"
    )

    workflow.load_database_nodes()

    with neo4j_driver.session(database="neo4j") as session:
        result = session.run("MATCH (d:Database) RETURN d.id as id, d.name as name, d.platform as platform")
        records = list(result)

        assert len(records) == 1
        assert records[0]["id"] == "my-project"
        assert records[0]["name"] == "My Project"
        assert records[0]["platform"] == "GCP"


def test_database_only_loads_provided_columns(neo4j_driver, temp_csv_dir):
    """Test that only CSV columns are loaded as properties, not all possible fields."""
    # Create CSV with only required and some optional fields (no description)
    csv_content = """database_id,name,platform
test-db,Test Database,AWS
"""
    csv_path = temp_csv_dir / "database_info.csv"
    csv_path.write_text(csv_content)

    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j"
    )

    workflow.load_database_nodes()

    with neo4j_driver.session(database="neo4j") as session:
        result = session.run("MATCH (d:Database) RETURN properties(d) as props")
        record = result.single()
        props = record["props"]

        # Should have: id, name, platform
        assert "id" in props
        assert "name" in props
        assert "platform" in props
        # Should NOT have: description, service (not in CSV)
        assert "description" not in props
        assert "service" not in props


def test_load_schema_nodes(neo4j_driver, temp_csv_dir, sample_database_csv, sample_schema_csv):
    """Test that schema nodes are loaded correctly."""
    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j"
    )

    # Load databases first (required for referential integrity)
    workflow.load_database_nodes()
    workflow.load_schema_nodes()

    with neo4j_driver.session(database="neo4j") as session:
        result = session.run("MATCH (s:Schema) RETURN s.id as id, s.name as name ORDER BY s.name")
        records = list(result)

        assert len(records) == 2
        assert records[0]["name"] == "Analytics"
        assert records[1]["name"] == "Sales"


def test_schema_only_loads_provided_columns(neo4j_driver, temp_csv_dir):
    """Test that only CSV columns are loaded for schemas."""
    # First create database CSV
    db_csv = """database_id,name
my-project,My Project
"""
    (temp_csv_dir / "database_info.csv").write_text(db_csv)

    # Create schema CSV without description field
    csv_content = """database_id,schema_id,name
my-project,sales,Sales
"""
    csv_path = temp_csv_dir / "schema_info.csv"
    csv_path.write_text(csv_content)

    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j"
    )

    workflow.load_database_nodes()
    workflow.load_schema_nodes()

    with neo4j_driver.session(database="neo4j") as session:
        result = session.run("MATCH (s:Schema) RETURN properties(s) as props")
        record = result.single()
        props = record["props"]

        # Should have: id, name
        assert "id" in props
        assert "name" in props
        # Should NOT have: description (not in CSV)
        assert "description" not in props


def test_load_has_schema_relationships(neo4j_driver, temp_csv_dir, sample_database_csv, sample_schema_csv):
    """Test that HAS_SCHEMA relationships are created."""
    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j"
    )

    workflow.load_database_nodes()
    workflow.load_schema_nodes()
    workflow.load_has_schema_relationships()

    with neo4j_driver.session(database="neo4j") as session:
        result = session.run(
            "MATCH (d:Database)-[:HAS_SCHEMA]->(s:Schema) "
            "RETURN d.id as db_id, s.name as schema_name ORDER BY s.name"
        )
        records = list(result)

        assert len(records) == 2
        assert records[0]["db_id"] == "my-project"
        assert records[0]["schema_name"] == "Analytics"


def test_load_table_nodes(neo4j_driver, temp_csv_dir, sample_database_csv, sample_schema_csv, sample_table_csv):
    """Test that table nodes are loaded correctly."""
    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j"
    )

    workflow.load_database_nodes()
    workflow.load_schema_nodes()
    workflow.load_table_nodes()

    with neo4j_driver.session(database="neo4j") as session:
        result = session.run("MATCH (t:Table) RETURN t.name as name ORDER BY t.name")
        records = list(result)

        assert len(records) == 3
        assert records[0]["name"] == "customers"
        assert records[1]["name"] == "orders"
        assert records[2]["name"] == "summary"


def test_load_column_nodes(neo4j_driver, temp_csv_dir, sample_database_csv, sample_schema_csv, sample_table_csv, sample_column_csv):
    """Test that column nodes are loaded correctly."""
    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j"
    )

    workflow.load_database_nodes()
    workflow.load_schema_nodes()
    workflow.load_table_nodes()
    workflow.load_column_nodes()

    with neo4j_driver.session(database="neo4j") as session:
        result = session.run(
            "MATCH (c:Column) "
            "RETURN c.name as name, c.type as type, c.is_primary_key as is_pk "
            "ORDER BY c.name"
        )
        records = list(result)

        assert len(records) == 5

        # Check customer_id column exists in both tables
        customer_id_cols = [r for r in records if r["name"] == "customer_id"]
        assert len(customer_id_cols) == 2


def test_column_only_loads_provided_columns(neo4j_driver, temp_csv_dir):
    """Test that only CSV columns are loaded for columns."""
    # Create required CSVs for hierarchy
    db_csv = """database_id,name
my-project,My Project
"""
    schema_csv = """database_id,schema_id
my-project,sales
"""
    table_csv = """database_id,schema_id,table_name
my-project,sales,orders
"""
    (temp_csv_dir / "database_info.csv").write_text(db_csv)
    (temp_csv_dir / "schema_info.csv").write_text(schema_csv)
    (temp_csv_dir / "table_info.csv").write_text(table_csv)

    # Create column CSV without data_type and description fields
    csv_content = """database_id,schema_id,table_name,column_name,is_nullable,is_primary_key
my-project,sales,orders,order_id,false,true
"""
    csv_path = temp_csv_dir / "column_info.csv"
    csv_path.write_text(csv_content)

    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j"
    )

    workflow.load_database_nodes()
    workflow.load_schema_nodes()
    workflow.load_table_nodes()
    workflow.load_column_nodes()

    with neo4j_driver.session(database="neo4j") as session:
        result = session.run("MATCH (c:Column) RETURN properties(c) as props")
        record = result.single()
        props = record["props"]

        # Should have: id, name, nullable, is_primary_key
        assert "id" in props
        assert "name" in props
        assert "nullable" in props
        assert "is_primary_key" in props
        # Should NOT have: type, description, is_foreign_key (not in CSV)
        assert "type" not in props
        assert "description" not in props
        assert "is_foreign_key" not in props


def test_column_properties_correct_values(neo4j_driver, temp_csv_dir):
    """Test that column properties are set with correct values."""
    # Create required CSVs
    db_csv = """database_id,name
my-project,My Project
"""
    schema_csv = """database_id,schema_id
my-project,sales
"""
    table_csv = """database_id,schema_id,table_name
my-project,sales,orders
"""
    column_csv = """database_id,schema_id,table_name,column_name,data_type,is_nullable,is_primary_key,is_foreign_key
my-project,sales,orders,order_id,STRING,false,true,false
"""
    (temp_csv_dir / "database_info.csv").write_text(db_csv)
    (temp_csv_dir / "schema_info.csv").write_text(schema_csv)
    (temp_csv_dir / "table_info.csv").write_text(table_csv)
    (temp_csv_dir / "column_info.csv").write_text(column_csv)

    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j"
    )

    workflow.load_database_nodes()
    workflow.load_schema_nodes()
    workflow.load_table_nodes()
    workflow.load_column_nodes()

    with neo4j_driver.session(database="neo4j") as session:
        result = session.run(
            "MATCH (c:Column {name: 'order_id'}) "
            "RETURN c.is_primary_key as is_pk, c.is_foreign_key as is_fk, c.nullable as nullable"
        )
        record = result.single()

        assert record["is_pk"] == True
        assert record["is_fk"] == False
        assert record["nullable"] == False


def test_load_references_relationships(neo4j_driver, temp_csv_dir):
    """Test that REFERENCES relationships are created."""
    # Create required CSVs
    db_csv = """database_id,name
my-project,My Project
"""
    schema_csv = """database_id,schema_id
my-project,sales
"""
    table_csv = """database_id,schema_id,table_name
my-project,sales,orders
my-project,sales,customers
"""
    column_csv = """database_id,schema_id,table_name,column_name
my-project,sales,orders,customer_id
my-project,sales,customers,customer_id
"""
    references_csv = """source_database_id,source_schema_id,source_table_name,source_column_name,target_database_id,target_schema_id,target_table_name,target_column_name,criteria
my-project,sales,orders,customer_id,my-project,sales,customers,customer_id,orders.customer_id = customers.customer_id
"""
    (temp_csv_dir / "database_info.csv").write_text(db_csv)
    (temp_csv_dir / "schema_info.csv").write_text(schema_csv)
    (temp_csv_dir / "table_info.csv").write_text(table_csv)
    (temp_csv_dir / "column_info.csv").write_text(column_csv)
    (temp_csv_dir / "column_references_info.csv").write_text(references_csv)

    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j"
    )

    # Load only what's needed
    workflow.load_database_nodes()
    workflow.load_schema_nodes()
    workflow.load_table_nodes()
    workflow.load_column_nodes()
    workflow.load_has_schema_relationships()
    workflow.load_has_table_relationships()
    workflow.load_has_column_relationships()
    workflow.load_references_relationships()

    with neo4j_driver.session(database="neo4j") as session:
        result = session.run(
            "MATCH (c1:Column)-[r:REFERENCES]->(c2:Column) "
            "RETURN c1.name as source, c2.name as target, r.criteria as criteria"
        )
        records = list(result)

        assert len(records) == 1
        assert records[0]["source"] == "customer_id"
        assert records[0]["target"] == "customer_id"
        assert "customers" in records[0]["criteria"]


def test_load_value_nodes(neo4j_driver, temp_csv_dir):
    """Test that value nodes are loaded correctly."""
    # Create required CSVs
    db_csv = """database_id,name
my-project,My Project
"""
    schema_csv = """database_id,schema_id
my-project,sales
"""
    table_csv = """database_id,schema_id,table_name
my-project,sales,orders
"""
    column_csv = """database_id,schema_id,table_name,column_name
my-project,sales,orders,status
"""
    value_csv = """database_id,schema_id,table_name,column_name,value
my-project,sales,orders,status,pending
my-project,sales,orders,status,completed
my-project,sales,orders,status,cancelled
"""
    (temp_csv_dir / "database_info.csv").write_text(db_csv)
    (temp_csv_dir / "schema_info.csv").write_text(schema_csv)
    (temp_csv_dir / "table_info.csv").write_text(table_csv)
    (temp_csv_dir / "column_info.csv").write_text(column_csv)
    (temp_csv_dir / "value_info.csv").write_text(value_csv)

    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j"
    )

    # Load required nodes for value relationships
    workflow.load_database_nodes()
    workflow.load_schema_nodes()
    workflow.load_table_nodes()
    workflow.load_column_nodes()
    workflow.load_value_nodes()

    with neo4j_driver.session(database="neo4j") as session:
        result = session.run("MATCH (v:Value) RETURN v.value as value ORDER BY v.value")
        records = list(result)

        assert len(records) == 3
        values = [r["value"] for r in records]
        assert "pending" in values
        assert "completed" in values
        assert "cancelled" in values


def test_load_query_nodes(neo4j_driver, temp_csv_dir, sample_query_csv):
    """Test that query nodes are loaded correctly."""
    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j"
    )

    workflow.load_query_nodes()

    with neo4j_driver.session(database="neo4j") as session:
        result = session.run("MATCH (q:Query) RETURN q.id as id, q.content as content ORDER BY q.id")
        records = list(result)

        assert len(records) == 2
        assert records[0]["id"] == "q001"
        assert "order_id" in records[0]["content"]


def test_query_only_loads_provided_columns(neo4j_driver, temp_csv_dir):
    """Test that only CSV columns are loaded for queries."""
    # Create CSV without description field
    csv_content = """query_id,content
q001,SELECT * FROM table
"""
    csv_path = temp_csv_dir / "query_info.csv"
    csv_path.write_text(csv_content)

    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j"
    )

    workflow.load_query_nodes()

    with neo4j_driver.session(database="neo4j") as session:
        result = session.run("MATCH (q:Query) RETURN properties(q) as props")
        record = result.single()
        props = record["props"]

        # Should have: id, content
        assert "id" in props
        assert "content" in props
        # Should NOT have: description (not in CSV)
        assert "description" not in props


def test_load_glossary_entities(neo4j_driver, temp_csv_dir):
    """Test that glossary entities are loaded correctly."""
    # Create glossary CSVs
    glossary_csv = """glossary_id,name,description
sales_glossary,Sales Glossary,Sales business terms
"""
    category_csv = """glossary_id,category_id,name,description
sales_glossary,metrics,Metrics,Sales metrics
"""
    term_csv = """category_id,term_id,name,description
metrics,arr,Annual Recurring Revenue,Yearly revenue
"""
    (temp_csv_dir / "glossary_info.csv").write_text(glossary_csv)
    (temp_csv_dir / "category_info.csv").write_text(category_csv)
    (temp_csv_dir / "business_term_info.csv").write_text(term_csv)

    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j"
    )

    workflow.load_glossary_nodes()
    workflow.load_category_nodes()
    workflow.load_business_term_nodes()
    workflow.load_has_category_relationships()
    workflow.load_has_business_term_relationships()

    with neo4j_driver.session(database="neo4j") as session:
        result = session.run(
            "MATCH (g:Glossary)-[:HAS_CATEGORY]->(c:Category)-[:HAS_BUSINESS_TERM]->(t:BusinessTerm) "
            "RETURN g.name as glossary, c.name as category, t.name as term"
        )
        record = result.single()

        assert record["glossary"] == "Sales Glossary"
        assert record["category"] == "Metrics"
        assert record["term"] == "Annual Recurring Revenue"


def test_run_complete_workflow(neo4j_driver, temp_csv_dir, all_sample_csvs):
    """Test that the complete workflow runs successfully."""
    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j"
    )

    workflow.run()

    with neo4j_driver.session(database="neo4j") as session:
        # Count nodes
        node_counts = {}
        for label in ["Database", "Schema", "Table", "Column", "Value", "Query", "Glossary", "Category", "BusinessTerm"]:
            result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
            node_counts[label] = result.single()["count"]

        assert node_counts["Database"] == 1
        assert node_counts["Schema"] == 2
        assert node_counts["Table"] == 3
        assert node_counts["Column"] == 5
        assert node_counts["Value"] == 3
        assert node_counts["Query"] == 2
        assert node_counts["Glossary"] == 1
        assert node_counts["Category"] == 1
        assert node_counts["BusinessTerm"] == 1

        # Count relationships
        rel_counts = {}
        for rel_type in ["HAS_SCHEMA", "HAS_TABLE", "HAS_COLUMN", "REFERENCES", "HAS_VALUE", "USES_TABLE"]:
            result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
            rel_counts[rel_type] = result.single()["count"]

        assert rel_counts["HAS_SCHEMA"] == 2
        assert rel_counts["HAS_TABLE"] == 3
        assert rel_counts["HAS_COLUMN"] == 5
        assert rel_counts["REFERENCES"] == 1
        assert rel_counts["HAS_VALUE"] == 3
        assert rel_counts["USES_TABLE"] == 2


def test_minimal_csv_with_only_required_fields(neo4j_driver, temp_csv_dir):
    """Test that CSV with only required fields works correctly."""
    # Create minimal CSVs
    db_csv = """database_id
minimal-db
"""
    schema_csv = """database_id,schema_id
minimal-db,schema1
"""
    table_csv = """database_id,schema_id,table_name
minimal-db,schema1,table1
"""
    column_csv = """database_id,schema_id,table_name,column_name
minimal-db,schema1,table1,col1
"""

    (temp_csv_dir / "database_info.csv").write_text(db_csv)
    (temp_csv_dir / "schema_info.csv").write_text(schema_csv)
    (temp_csv_dir / "table_info.csv").write_text(table_csv)
    (temp_csv_dir / "column_info.csv").write_text(column_csv)

    workflow = CSVWorkflow(
        csv_directory=str(temp_csv_dir),
        neo4j_driver=neo4j_driver,
        database_name="neo4j"
    )

    workflow.run()

    # Verify minimal data was loaded
    with neo4j_driver.session(database="neo4j") as session:
        # Check that nodes were created with minimal properties
        db_result = session.run("MATCH (d:Database) RETURN properties(d) as props")
        db_props = db_result.single()["props"]
        # Should only have id and name (name defaults to id)
        assert "id" in db_props
        assert "name" in db_props
        assert len([k for k in db_props.keys() if not k.startswith("_")]) == 2  # Only id and name

        # Verify relationships were created
        rel_count = session.run("MATCH ()-[r:HAS_SCHEMA]->() RETURN count(r) as count").single()["count"]
        assert rel_count == 1
