# GCP Dataplex Universal Catalog Connector

## Overview

This connector reads information from the GCP Dataplex Universal Catalog via the Python client and maps it to the graph data model schema defined in this library. 

Currently this connector supports reading BigQuery metadata stored in Dataplex and Glossary information.

## Data Model

### BigQuery Metadata

The BigQuery metadata available via Dataplex is not as comprehensive as reading the metadata directly from BigQuery. Below is the supported data model. Notably absent are the primary and foreign key identifiers. Each column is therefore loaded with `isPrimaryKey=False` and `isForeignKey=False`.

```mermaid
---
config:
    layout: elk
---
graph LR
%% Nodes
Database("Database<br/>id: STRING | KEY<br/>name: STRING<br/>platform: STRING<br/>service: STRING")
Schema("Schema<br/>id: STRING | KEY<br/>name: STRING")
Table("Table<br/>id: STRING | KEY<br/>name: STRING<br/>description: STRING<br/>embedding: VECTOR")
Column("Column<br/>id: STRING | KEY<br/>name: STRING<br/>description: STRING<br/>embedding: VECTOR<br/>type: STRING<br/>nullable: BOOLEAN<br/>")

%% Relationships
Database -->|HAS_SCHEMA| Schema
Schema -->|HAS_TABLE| Table
Table -->|HAS_COLUMN| Column
Column -->|REFERENCES| Column
```

### Glossary Information

Dataplex has a Glossary that allows us to store business terms. Ideally terms may then be connected to columns, which allows us to infer table relationships via columns that resolve to a shared business term. Below is the data model for Dataplex glossary information.

```mermaid
---
config:
    layout: elk
---
graph LR
%% Nodes
Glossary("Glossary<br/>id: STRING | KEY<br/>name: STRING<br/>description: STRING")
Category("Category<br/>id: STRING | KEY<br/>name: STRING<br/>description: STRING")
BusinessTerm("BusinessTerm<br/>id: STRING | KEY<br/>name: STRING<br/>description: STRING<br/>embedding: VECTOR")

%% Relationships
Glossary -->|HAS_CATEGORY| Category
Category -->|HAS_BUSINESS_TERM| BusinessTerm
```

## Known Issues

### Unable to connect business terms to columns

The Dataplex API has no method of retrieving entityLink IDs. This means that we can not automatically retrieve the connections between columns and business terms. This is a feature that is in the preview version of the Dataplex API and should be released in the future. Once publically available, it will be implemented in this library. 

### Aspect handling

Information such as primary / foreign keys and data stewardship may be defined as Dataplex Aspects. Aspects are custom definitions and so automating the indetification and mapping of Aspects to Steward nodes, for example, is difficult. Additionally, the inaccessible entityLink IDs mean that even if we properly map these Aspects to nodes in our data model, we can't identify relationships via the Dataplex API.


