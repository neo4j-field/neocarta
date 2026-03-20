"""
CSV Connector Example

Load metadata from CSV files into Neo4j using the CSVWorkflow connector.

The example dataset is located in datasets/csv/ and contains a complete
e-commerce schema with tables, columns, foreign keys, queries, and business glossary.
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from semantic_graph.connectors.csv import CSVWorkflow


def main():
    """Load metadata from CSV files into Neo4j."""
    # Load environment variables
    load_dotenv()

    # Setup Neo4j connection
    neo4j_driver = GraphDatabase.driver(
        uri=os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")

    # Initialize CSV workflow
    workflow = CSVWorkflow(
        csv_directory="datasets/csv",
        neo4j_driver=neo4j_driver,
        database_name=neo4j_database
    )

    # if using non-default CSV file map, pass it to the workflow
    file_map = {
        "database": "database_info.csv",
        "schema": "schema_info.csv",
        "table": "table_info.csv",
        "column": "column_info.csv",
        "value": "value_info.csv",
        # ...
    }

    # by default, load all nodes and relationships
    # * structural nodes and relationships
    # * sql query nodes and relationships
    # * terminology nodes and relationships

    # Here we define which nodes and relationships to load
    include_nodes = ["database", "schema", "table", "column", "value"]
    include_relationships = ["has_schema", "has_table", "has_column", "has_value", "references"]
    # Run the workflow to load all CSV files
    workflow.run(
        csv_file_map=file_map,
        include_nodes=include_nodes,
        include_relationships=include_relationships
    )

    # Cleanup
    neo4j_driver.close()
    print("\nWorkflow completed successfully!")


if __name__ == "__main__":
    main()
