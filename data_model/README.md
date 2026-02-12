# Data Model

This module contains the graph data model components in a metadata graph.

**The data model components defined in this document are subject to change throughout development.**

## Core Data Model

The core data model consists of four nodes and four relationships. 

Nodes
* [`Database`](./core.py#L9)
    * Top level node containing information about the database
* [`Schema`](./core.py#L31)
    * Contains details about the database schema
* [`Table`](./core.py#L44)
    * Contains information about a table within the database schema
* [`Column`](./core.py#L57)
    * Contains information about a column within a table

Relationships
* [`(:Database)-[:HAS_SCHEMA]->(:Schema)`](./core.py#L88)
    * Defines the database to schema hierarchy
* [`(:Schema)-[:HAS_TABLE]->(:Table)`](./core.py#L98)
    * Defines the schema to table hierarchy
* [`(:Table)-[:HAS_COLUMN]->(:Column)`](./core.py#L108)
    * Defines the table to column hierarchy
* [`(:Column)-[:REFERENCES]->(:Column)`](./core.py#L118)
    * Defines relationship where two columns represent the same information, but exist in different tables
    * Columns identifed with this relationship may be used to join their respective tables

## Value Nodes

Value nodes provide example values and enums that may augment the database context. 
For example upon matching a `Column`, `k` values may be returned as examples by traversing to related `Value` nodes.
If values are constrained to a set of options, these may be provded as an enum in the context to provide additional guidance.

Nodes
* [`Value`](./expanded.py#L5)
    * Represents a single unique value within a column
    * Values are unique on the column level within the graph
    * A value may not have more than one relationship with a `Column` node

Relationships
* [`(:Column)-[:HAS_VALUE]->(:Value)`](./expanded.py#L12)
    * Defines a value's parent column

## Glossary Data Model **(Partially Implemented)**

Data catalogs allow business terms to be defined and linked to columns. 
This allows table relationships to be inferred by shared business terms between their columns.
For example `TableA.customer_id` and `TableB.cstmr_id` both are tagged with the business term "Customer ID", implying that we can join these tables on `customer_id` and `cstmr_id`.

Nodes
* [`Glossary`](./expanded.py#L21)
    * The glossary containing categories and business terms
* [`Category`](./expanded.py#L27)
    * Contains information about a category in the glossary
* [`BusinessTerm`](./expanded.py#L33)
    * A leaf level term in the glossary
    * Defines globally recognized term across databases in the system

Relationships
* [`(:Glossary)-[:HAS_CATEGORY]->(:Category)`](./expanded.py#L42)
    * Defines glossary to category hierarchy
* [`(:Category)-[:HAS_BUSINESS_TERM]->(:BusinessTerm)`](./expanded.py#L50)
    * Defines category to business term hierarchy
* `(:Column)-[:RESOLVES_TO]->(:BusinessTerm)`
    * Defines how a column resolves to a business term
    * Columns that resolve to the same business term may likely may be used to join their respective tables

## Data Stewards **(Not Implemented)**

Data catalogs allows data stewards to be defined and linked to the appropriate assets in the database.

Nodes
* `Steward`

Relationships
* `(:Steward)-[:STEWARDS_SCHEMA]->(:Schema)`
* `(:Steward)-[:STEWARDS_TABLE]->(:Table)`
* `(:Steward)-[:STEWARDS_CATEGORY]->(:Category)`
* `(:Steward)-[:STEWARDS_BUSINESS_TERM]->(:BusinessTerm)`

## Rules **(Not Implemented)**

Data catalogs allow for data quality and business rules to be defined and linked to the appropriate assets. 
These rules may be returned alongside their respective data assets to guide the agent in how to use them properly.

Nodes
* `DataQualityRule`
    * A rule that enforces data correctness and completeness
* `BusinessRule`
    * A rule that describes business logic and constraints

Relationships
* `(:DataQualityRule)-[:ENFORCES_TABLE]->(:Table)`
* `(:DataQualityRule)-[:ENFORCES_COLUMN]->(:Column)`
* `(:BusinessRule)-[:APPLIES_TO_TABLE]->(:Table)`
* `(:BusinessRule)-[:APPLIES_TO_COLUMN]->(:Column)`
* `(:BusinessRule)-[:RELATED_TO]->(:BusinessTerm)`
    * Defines which business terms are related to the business rule
    * This relationship may be used to identify columns that are impacted by a business rule 

## SQL Queries **(Not Implemented)**

SQL queries may be cached in the graph and provided as few-shot examples in the context.

Nodes
* `SQLQuery`

Relationships
* `(:SQLQuery)-[:USES_TABLE]->(:Table)`
* `(:SQLQuery)-[:USES_COLUMN]->(:Table)`

## Metrics + KPIs **(Not Implemented)**

Metrics and KPIs may be stored in the graph and linked to their associated tables and columns. 
They may also be linked to `SQLQuery` nodes, which define how to calculate the metric.
`Metric` is the main node label, however they may also have the additional node label `KPI`.

Nodes
* `Metric`
* `Metric&KPI`
    * All `KPI` labels are an additional label on `Metric` nodes

Relationships
* `(:Metric&KPI)-[:HAS_SQL_QUERY]->(:SQLQuery)`





