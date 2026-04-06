# CSV Connector

This document describes the required CSV file formats for ingesting metadata into the semantic graph using the CSV connector.

## Overview

The CSV connector accepts normalized CSV files representing database metadata entities and their relationships. Files can be provided for core database entities (databases, schemas, tables, columns), extended entities (values, glossaries, business terms, queries), and their relationships.

## Terminology Note

**Database and Schema:**
- Column names use generic terminology (`database_id`, `schema_id`) for compatibility across different database systems
- For BigQuery users: **database = GCP project** and **schema = dataset**
- The graph data model uses generic terminology (Database, Schema nodes) to support multiple database platforms

## ID Construction

**IDs are automatically constructed by the connector.** You do not need to provide pre-formatted IDs in your CSV files.

The connector builds hierarchical, dot-separated IDs:
- Database ID: `{database_id}`
- Schema ID: `{database_id}.{schema_id}`
- Table ID: `{database_id}.{schema_id}.{table_name}`
- Column ID: `{database_id}.{schema_id}.{table_name}.{column_name}`

**Important:** Relationships between entities are NOT derived by parsing IDs. All relationships must be explicitly defined either through parent identifier columns (e.g., `database_id` in `schema_info.csv`) or through dedicated relationship CSV files (e.g., `column_references_info.csv`).

## CSV File Formats

### Core Entity Files

#### 1. `database_info.csv` (Database nodes)

Creates `:Database` nodes in the graph.

**Required columns:**
- `database_id` (string): Unique identifier for the database

**Optional columns:**
- `name` (string): Display name for the database (defaults to `database_id`)
- `service` (string): Database service (e.g., "BIGQUERY", "POSTGRES")
- `platform` (string): Cloud platform (e.g., "GCP", "AWS", "AZURE")
- `description` (string): Database description

**Example:**
```csv
database_id,name,platform,service,description
my-project,My Project,GCP,BIGQUERY,Production data warehouse
```

---

#### 2. `schema_info.csv` (Schema nodes)

Creates `:Schema` nodes and `(:Database)-[:HAS_SCHEMA]->(:Schema)` relationships.

**Required columns:**
- `database_id` (string): Parent database identifier
- `schema_id` (string): Schema identifier

**Optional columns:**
- `name` (string): Display name (defaults to `schema_id`)
- `description` (string): Schema description

**Derived by connector:**
- Full Schema ID: `{database_id}.{schema_id}`
- HAS_SCHEMA relationship: `(database_id)-[:HAS_SCHEMA]->(database_id.schema_id)`

**Example:**
```csv
database_id,schema_id,name,description
my-project,analytics,Analytics,Analytics dataset for reporting
my-project,sales,Sales,Sales transaction data
```

---

#### 3. `table_info.csv` (Table nodes)

Creates `:Table` nodes and `(:Schema)-[:HAS_TABLE]->(:Table)` relationships.

**Required columns:**
- `database_id` (string): Database identifier
- `schema_id` (string): Schema identifier
- `table_name` (string): Table name

**Optional columns:**
- `name` (string): Display name (defaults to `table_name`)
- `description` (string): Table description

**Derived by connector:**
- Table ID: `{database_id}.{schema_id}.{table_name}`
- HAS_TABLE relationship: `(database_id.schema_id)-[:HAS_TABLE]->(database_id.schema_id.table_name)`

**Example:**
```csv
database_id,schema_id,table_name,description
my-project,analytics,customer_summary,Aggregated customer metrics
my-project,sales,orders,Order transactions
```

---

#### 4. `column_info.csv` (Column nodes)

Creates `:Column` nodes and `(:Table)-[:HAS_COLUMN]->(:Column)` relationships.

**Required columns:**
- `database_id` (string): Database identifier
- `schema_id` (string): Schema identifier
- `table_name` (string): Table name
- `column_name` (string): Column name

**Optional columns:**
- `name` (string): Display name (defaults to `column_name`)
- `description` (string): Column description
- `data_type` (string): Data type (e.g., "STRING", "INTEGER", "TIMESTAMP")
- `is_nullable` (boolean): Whether column accepts NULL values (default: `true`)
- `is_primary_key` (boolean): Whether column is a primary key (default: `false`)
- `is_foreign_key` (boolean): Whether column is a foreign key (default: `false`)

**Validation:**
- A column cannot be both a primary key and a foreign key

**Derived by connector:**
- Column ID: `{database_id}.{schema_id}.{table_name}.{column_name}`
- HAS_COLUMN relationship: `(table_id)-[:HAS_COLUMN]->(column_id)`

**Example:**
```csv
database_id,schema_id,table_name,column_name,data_type,is_nullable,is_primary_key,is_foreign_key,description
my-project,sales,orders,order_id,STRING,false,true,false,Unique order identifier
my-project,sales,orders,customer_id,STRING,false,false,true,Customer reference
my-project,sales,orders,order_date,TIMESTAMP,false,false,false,Order creation timestamp
my-project,sales,orders,total_amount,FLOAT64,true,false,false,Total order amount
```

---

### Relationship Files

#### 5. `column_references_info.csv` (References relationships)

Creates `(:Column)-[:REFERENCES]->(:Column)` relationships representing foreign key constraints and join conditions discovered from query logs or schema analysis.

**Required columns:**
- `source_database_id` (string): Source database identifier
- `source_schema_id` (string): Source schema identifier
- `source_table_name` (string): Source table name
- `source_column_name` (string): Source column name (foreign key column)
- `target_database_id` (string): Target database identifier
- `target_schema_id` (string): Target schema identifier
- `target_table_name` (string): Target table name
- `target_column_name` (string): Target column name (referenced primary key column)

**Optional columns:**
- `criteria` (string): Join condition or constraint criteria (e.g., `"orders.customer_id = customers.customer_id"`)

**Derived by connector:**
- Source column ID: `source_database_id.source_schema_id.source_table_name.source_column_name`
- Target column ID: `target_database_id.target_schema_id.target_table_name.target_column_name`

**Example:**
```csv
source_database_id,source_schema_id,source_table_name,source_column_name,target_database_id,target_schema_id,target_table_name,target_column_name,criteria
my-project,sales,orders,customer_id,my-project,sales,customers,customer_id,orders.customer_id = customers.customer_id
my-project,sales,order_items,order_id,my-project,sales,orders,order_id,order_items.order_id = orders.order_id
my-project,sales,order_items,product_id,my-project,sales,products,product_id,order_items.product_id = products.product_id
```

---

### Extended Entity Files

#### 6. `value_info.csv` (Value nodes)

Creates `:Value` nodes and `(:Column)-[:HAS_VALUE]->(:Value)` relationships representing unique/sample values in columns.

**Required columns:**
- `database_id` (string): Database identifier
- `schema_id` (string): Schema identifier
- `table_name` (string): Table name
- `column_name` (string): Column name
- `value` (string): The actual value as a string

**Derived by connector:**
- Value ID: `{database_id}.{schema_id}.{table_name}.{column_name}.{value_hash}`
- HAS_VALUE relationship: `(column_id)-[:HAS_VALUE]->(value_id)`

**Example:**
```csv
database_id,schema_id,table_name,column_name,value
my-project,sales,orders,status,pending
my-project,sales,orders,status,completed
my-project,sales,orders,status,cancelled
my-project,sales,products,category,Electronics
my-project,sales,products,category,Clothing
```

---

#### 7. `query_info.csv` (Query nodes)

Creates `:Query` nodes representing SQL queries from query logs.

**Required columns:**
- `query_id` (string): Unique identifier for the query
- `content` (string): SQL query content

**Optional columns:**
- `description` (string): Query description

**Example:**
```csv
query_id,content,description
q001,"SELECT * FROM sales.orders WHERE status = 'completed'",Get completed orders
q002,"SELECT customer_id, SUM(total_amount) FROM sales.orders GROUP BY customer_id",Customer revenue summary
```

---

#### 8. `query_table_info.csv` (UsesTable relationships)

Creates `(:Query)-[:USES_TABLE]->(:Table)` relationships.

**Required columns:**
- `query_id` (string): Query identifier
- `table_id` (string): Table full ID (must match ID constructed from `table_info.csv`)

**Example:**
```csv
query_id,table_id
q001,my-project.sales.orders
q002,my-project.sales.orders
```

---

#### 9. `query_column_info.csv` (UsesColumn relationships)

Creates `(:Query)-[:USES_COLUMN]->(:Column)` relationships.

**Required columns:**
- `query_id` (string): Query identifier
- `column_id` (string): Column full ID (must match ID constructed from `column_info.csv`)

**Example:**
```csv
query_id,column_id
q001,my-project.sales.orders.status
q002,my-project.sales.orders.customer_id
q002,my-project.sales.orders.total_amount
```

---

### Glossary Entity Files

#### 10. `glossary_info.csv` (Glossary nodes)

Creates `:Glossary` nodes representing business glossaries.

**Required columns:**
- `glossary_id` (string): Unique identifier for the glossary

**Optional columns:**
- `name` (string): Display name (defaults to `glossary_id`)
- `description` (string): Glossary description

**Example:**
```csv
glossary_id,name,description
sales_glossary,Sales Glossary,Business terms for sales domain
product_glossary,Product Glossary,Product and inventory terminology
```

---

#### 11. `category_info.csv` (Category nodes)

Creates `:Category` nodes and `(:Glossary)-[:HAS_CATEGORY]->(:Category)` relationships.

**Required columns:**
- `glossary_id` (string): Parent glossary identifier
- `category_id` (string): Category identifier

**Optional columns:**
- `name` (string): Display name (defaults to `category_id`)
- `description` (string): Category description

**Derived by connector:**
- HAS_CATEGORY relationship: `(glossary_id)-[:HAS_CATEGORY]->(category_id)`

**Example:**
```csv
glossary_id,category_id,name,description
sales_glossary,customer_metrics,Customer Metrics,Metrics related to customer behavior
sales_glossary,revenue,Revenue,Revenue and financial metrics
```

---

#### 12. `business_term_info.csv` (BusinessTerm nodes)

Creates `:BusinessTerm` nodes and `(:Category)-[:HAS_BUSINESS_TERM]->(:BusinessTerm)` relationships.

**Required columns:**
- `category_id` (string): Parent category identifier
- `term_id` (string): Business term identifier

**Optional columns:**
- `name` (string): Display name (defaults to `term_id`)
- `description` (string): Business term description

**Derived by connector:**
- HAS_BUSINESS_TERM relationship: `(category_id)-[:HAS_BUSINESS_TERM]->(term_id)`

**Example:**
```csv
category_id,term_id,name,description
customer_metrics,ltv,Customer Lifetime Value,Total revenue expected from a customer over their lifetime
customer_metrics,cac,Customer Acquisition Cost,Average cost to acquire a new customer
revenue,arr,Annual Recurring Revenue,Predictable revenue normalized to a yearly amount
```

---

## Minimal CSV Set

To get started, you need at minimum:
1. `database_info.csv`
2. `schema_info.csv`
3. `table_info.csv`
4. `column_info.csv`

All other files are optional and can be added to enrich the graph with additional metadata.

## Data Quality Notes

1. **NULL Handling**: Empty cells or cells containing "NaN", "NULL", or "null" will be treated as `None` in the data model
2. **Boolean Values**: Accepted formats: `true/false`, `True/False`, `1/0`
3. **String Normalization**:
   - `service` and `platform` fields are automatically converted to uppercase
   - Leading/trailing whitespace is trimmed
4. **ID Uniqueness**: All IDs must be unique within their entity type
5. **Referential Integrity**:
   - Parent identifier columns (e.g., `database_id` in `schema_info.csv`) must reference existing entities in parent CSV files
   - Relationship CSV files must reference valid entity IDs that match the connector-constructed IDs
6. **ID Format**: When providing IDs in relationship CSVs, use the fully qualified format: `database_id.schema_id.table_name.column_name`

## Connector Configuration

### Custom File Mapping

You can customize CSV file names by providing a `csv_file_map` parameter:

```python
custom_file_map = {
    "database": "my_database.csv",
    "schema": "my_schemas.csv",
    "table": "my_tables.csv",
    # ... other custom filenames
}

connector = CSVConnector(
    csv_directory="datasets/csv",
    neo4j_driver=neo4j_driver,
    database_name=neo4j_database,
    csv_file_map=custom_file_map
)
```

Default file names (if not overridden):
- `database_info.csv`
- `schema_info.csv`
- `table_info.csv`
- `column_info.csv`
- `column_references_info.csv`
- `value_info.csv`
- `query_info.csv`
- `query_table_info.csv`
- `query_column_info.csv`
- `glossary_info.csv`
- `category_info.csv`
- `business_term_info.csv`

### Selective Loading

You can choose which nodes and relationships to load:

```python
# Load only core schema entities
connector.run(
    include_nodes=["database", "schema", "table", "column"],
    include_relationships=["has_schema", "has_table", "has_column"]
)

# Load schema + column values
connector.run(
    include_nodes=["database", "schema", "table", "column", "value"],
    include_relationships=["has_schema", "has_table", "has_column", "has_value", "references"]
)

# Load everything including queries and glossary
connector.run()  # No filters = load all available CSV files
```

## Usage Examples

### Basic Usage

```python
import os
from neo4j import GraphDatabase
from semantic_graph.connectors.csv import CSVConnector

# Initialize Neo4j driver
neo4j_driver = GraphDatabase.driver(
    uri=os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
)
neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")

# Create connector instance
connector = CSVConnector(
    csv_directory="datasets/csv",
    neo4j_driver=neo4j_driver,
    database_name=neo4j_database
)

# Run the complete connector (loads all available CSV files)
connector.run()

# Cleanup
neo4j_driver.close()
```

### Advanced Usage with Custom Configuration

```python
# Custom file mapping and selective loading
custom_file_map = {
    "table": "custom_tables.csv",
    "column": "custom_columns.csv"
}

connector = CSVConnector(
    csv_directory="path/to/csv/files",
    neo4j_driver=neo4j_driver,
    database_name="neo4j",
    csv_file_map=custom_file_map
)

# Load only specific entities
connector.run(
    include_nodes=["database", "schema", "table", "column", "value"],
    include_relationships=["has_schema", "has_table", "has_column", "has_value", "references"]
)
```

### Runtime File Override

```python
# Override file mapping at runtime (without modifying instance config)
connector.run(
    csv_file_map={"table": "alternative_tables.csv"},
    include_nodes=["table"],
    include_relationships=["has_table"]
)
```
