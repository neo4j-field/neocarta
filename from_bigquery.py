
from google.cloud import bigquery
from data_model.core import Database, Table, Column, ContainsTable, HasColumn, References
import pandas as pd
from neo4j import GraphDatabase, Driver, RoutingControl
from dotenv import load_dotenv
import os



# read information schema tables 

def get_database_info(client: bigquery.Client, project_id: str, dataset_id: str) -> pd.DataFrame:
    return client.query(f"""
SELECT 
    DISTINCT table_catalog,
    table_schema,
    option_value as description
FROM `{project_id}`.`{dataset_id}`.INFORMATION_SCHEMA.TABLES tables
    LEFT JOIN `{project_id}`.INFORMATION_SCHEMA.SCHEMATA_OPTIONS schemata_options
        ON tables.table_schema = schemata_options.schema_name
WHERE option_name = 'description'
""").to_dataframe()

def get_table_info(client: bigquery.Client, project_id: str, dataset_id: str) -> pd.DataFrame:
    return client.query(f"""
SELECT 
    tables.table_catalog,
    tables.table_schema,
    tables.table_name,
    tables.table_type,
    tables.creation_time,
    tables.ddl,
    table_options.option_value as description
FROM `{project_id}`.`{dataset_id}`.INFORMATION_SCHEMA.TABLES as tables
    LEFT JOIN `{project_id}`.`{dataset_id}`.INFORMATION_SCHEMA.TABLE_OPTIONS as table_options
        ON tables.table_catalog = table_options.table_catalog
        AND tables.table_schema = table_options.table_schema
        AND tables.table_name = table_options.table_name
WHERE table_type = 'BASE TABLE'
ORDER BY table_name
""").to_dataframe()

def get_column_info(client: bigquery.Client, project_id: str, dataset_id: str) -> pd.DataFrame:

    def _is_pk(row: pd.Series) -> bool:
        return isinstance(row['constraint_name'], str) and row['constraint_name'].endswith('pk$')
    
    def _is_fk(row: pd.Series) -> bool:
        return isinstance(row['constraint_name'], str) and '.fk_' in row['constraint_name']

    df = client.query(f"""
SELECT 
    columns.table_catalog,
    columns.table_schema,
    columns.table_name,
    columns.column_name,
    columns.is_nullable,
    columns.data_type,
    column_field_paths.description,
    key_column_usage.constraint_name

FROM `{project_id}`.`{dataset_id}`.INFORMATION_SCHEMA.COLUMNS as columns
    LEFT JOIN `{project_id}`.`{dataset_id}`.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS column_field_paths
        ON columns.table_schema = column_field_paths.table_schema
        AND columns.table_name = column_field_paths.table_name
        AND columns.column_name = column_field_paths.column_name

    LEFT JOIN `{project_id}`.`{dataset_id}`.INFORMATION_SCHEMA.KEY_COLUMN_USAGE key_column_usage
        ON columns.table_schema = key_column_usage.table_schema
        AND columns.table_name = key_column_usage.table_name
        AND columns.column_name = key_column_usage.column_name
""").to_dataframe()

    df['is_primary_key'] = df.apply(_is_pk, axis=1)
    df['is_foreign_key'] = df.apply(_is_fk, axis=1)
    return df

def get_column_references_info(client: bigquery.Client, project_id: str, dataset_id: str) -> pd.DataFrame:
    return client.query(f"""
SELECT 
    tc.constraint_catalog,
    tc.constraint_schema,
    tc.constraint_name,
    tc.constraint_type,
    tc.table_name,
    kcu.column_name,
    kcu.ordinal_position,
    ccu.table_name AS referenced_table,
    ccu.column_name AS referenced_column
FROM `{project_id}`.`{dataset_id}`.INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
    LEFT JOIN `{project_id}`.`{dataset_id}`.INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
        ON tc.constraint_name = kcu.constraint_name
    LEFT JOIN `{project_id}`.`{dataset_id}`.INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu
        ON tc.constraint_name = ccu.constraint_name
ORDER BY tc.table_name, tc.constraint_type, kcu.ordinal_position
""").to_dataframe()

# convert to core data model

def get_database_nodes(database_info: pd.DataFrame) -> list[Database]:
    return [Database(
        id=row.table_catalog + "." + row.table_schema,
        name=row.table_catalog + "." + row.table_schema,
        description=row.description
    ) for _, row in database_info.iterrows()]

def get_table_nodes(table_info: pd.DataFrame) -> list[Table]:
    return [Table(
        id=info_row.table_catalog + "." + info_row.table_schema + "." + info_row.table_name,
        name=info_row.table_name,
        description=info_row.description
    ) for _, info_row in table_info.iterrows()]

def get_column_nodes(column_info: pd.DataFrame) -> list[Column]:
    return [Column(
        id=row.table_catalog + "." + row.table_schema + "." + row.table_name + "." + row.column_name,
        name=row.column_name,
        description=row.description,
        type=row.data_type,
        nullable=row.is_nullable,
        is_primary_key=row.is_primary_key,
        is_foreign_key=row.is_foreign_key
    ) for _, row in column_info.iterrows()]

def get_contains_table_relationships(table_info: pd.DataFrame) -> list[ContainsTable]:
    return [ContainsTable(
        database_id=row.table_catalog + "." + row.table_schema,
        table_id=row.table_catalog + "." + row.table_schema + "." + row.table_name
    ) for _, row in table_info.iterrows()]

def get_has_column_relationships(column_info: pd.DataFrame) -> list[HasColumn]:
    return [HasColumn(
        table_id=row.table_catalog + "." + row.table_schema + "." + row.table_name,
        column_id=row.table_catalog + "." + row.table_schema + "." + row.table_name + "." + row.column_name
    ) for _, row in column_info.iterrows()]

def get_references_relationships(column_references_info: pd.DataFrame) -> list[References]:
    return [References(
        source_column_id=row.constraint_catalog + "." + row.constraint_schema + "." + row.table_name + "." + row.column_name,
        target_column_id=row.constraint_catalog + "." + row.constraint_schema + "." + row.referenced_table + "." + row.referenced_column
    ) for _, row in column_references_info[column_references_info['constraint_type'] == 'FOREIGN KEY'].iterrows()]

# load into neo4j

def load_database_nodes(database_nodes: list[Database], neo4j_driver: Driver) -> dict:

    _, summary, _ = neo4j_driver.execute_query(
        query_="""
    UNWIND $rows as row
    MERGE (d:Database {id: row.id, name: row.name, description: row.description})
    """, 
        parameters_={
            "rows": [n.model_dump() for n in database_nodes]
        },
        routing_=RoutingControl.WRITE)
    
    return summary.counters.__dict__

def load_table_nodes(table_nodes: list[Table], neo4j_driver: Driver) -> dict:
    _, summary, _ = neo4j_driver.execute_query(
        query_="""
    UNWIND $rows as row
    MERGE (t:Table {id: row.id, name: row.name, description: row.description})
    """, 
        parameters_={
            "rows": [n.model_dump() for n in table_nodes]
        },
        routing_=RoutingControl.WRITE)
    return summary.counters.__dict__

def load_column_nodes(column_nodes: list[Column], neo4j_driver: Driver) -> dict:
    _, summary, _ = neo4j_driver.execute_query(
        query_="""
    UNWIND $rows as row
    MERGE (c:Column {id: row.id, name: row.name, description: row.description, type: row.type, nullable: row.nullable, is_primary_key: row.is_primary_key, is_foreign_key: row.is_foreign_key})
    """, 
        parameters_={
            "rows": [n.model_dump() for n in column_nodes]
        },
        routing_=RoutingControl.WRITE)
    return summary.counters.__dict__

def load_contains_table_relationships(contains_table_relationships: list[ContainsTable], neo4j_driver: Driver) -> dict:
    _, summary, _ = neo4j_driver.execute_query(
        query_="""
    UNWIND $rows as row
    MATCH (d:Database {id: row.database_id})
    MERGE (t:Table {id: row.table_id})
    MERGE (d)-[:CONTAINS]->(t)
    """, 
        parameters_={
            "rows": [n.model_dump() for n in contains_table_relationships]
        },
        routing_=RoutingControl.WRITE)
    return summary.counters.__dict__

def load_has_column_relationships(has_column_relationships: list[HasColumn], neo4j_driver: Driver) -> dict:
    _, summary, _ = neo4j_driver.execute_query(
        query_="""
    UNWIND $rows as row
    MATCH (t:Table {id: row.table_id})
    MERGE (c:Column {id: row.column_id})
    MERGE (t)-[:HAS]->(c)
    """, 
        parameters_={
            "rows": [n.model_dump() for n in has_column_relationships]
        },
        routing_=RoutingControl.WRITE)
    return summary.counters.__dict__

def load_references_relationships(references_relationships: list[References], neo4j_driver: Driver) -> dict:
    _, summary, _ = neo4j_driver.execute_query(
        query_="""
    UNWIND $rows as row
    MATCH (c1:Column {id: row.source_column_id})
    MERGE (c2:Column {id: row.target_column_id})
    MERGE (c1)-[:REFERENCES]->(c2)
    """, 
        parameters_={
            "rows": [n.model_dump() for n in references_relationships]
        },
        routing_=RoutingControl.WRITE)
    return summary.counters.__dict__

if __name__ == "__main__":
    load_dotenv()

    neo4j_driver = GraphDatabase.driver(
        uri=os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )

    # connect to bigquery 
    project_id = os.getenv("BIGQUERY_PROJECT_ID")
    dataset_id = os.getenv("BIGQUERY_DATASET_ID")

    # this works since google app default credentials are set
    bq_client = bigquery.Client(project=project_id)

    database_info = get_database_info(bq_client, project_id, dataset_id)
    table_info = get_table_info(bq_client, project_id, dataset_id)
    column_info = get_column_info(bq_client, project_id, dataset_id)
    column_references_info = get_column_references_info(bq_client, project_id, dataset_id)

    database_nodes = get_database_nodes(database_info)
    table_nodes = get_table_nodes(table_info)
    column_nodes = get_column_nodes(column_info)

    contains_table_relationships = get_contains_table_relationships(table_info)
    has_column_relationships = get_has_column_relationships(column_info)
    references_relationships = get_references_relationships(column_references_info)

    print(load_database_nodes(database_nodes, neo4j_driver))
    print(load_table_nodes(table_nodes, neo4j_driver))
    print(load_column_nodes(column_nodes, neo4j_driver))
    print(load_contains_table_relationships(contains_table_relationships, neo4j_driver))
    print(load_has_column_relationships(has_column_relationships, neo4j_driver))
    print(load_references_relationships(references_relationships, neo4j_driver))    