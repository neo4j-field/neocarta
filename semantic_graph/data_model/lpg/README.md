# LPG Graph Data Model Components

This module contains the graph data model components for a Labeled Property Graph (LPG) metadata graph.

**The data model components defined in this document are subject to change throughout development.**

## Core Data Model **(Not Implemented)**

The core data model represents the metadata structure of a Labeled Property Graph database. It consists of five nodes and seven relationships.

```mermaid
---
config:
    layout: elk
---
graph LR

Database("Database<br/>id: STRING | KEY<br/>name: STRING<br/>description: STRING<br/>embedding: VECTOR<br/>platform: STRING<br/>service: STRING")

Schema("Schema<br/>id: STRING | KEY<br/>name: STRING<br/>description: STRING<br/>embedding: VECTOR")

Node("Node<br/>id: STRING | KEY<br/>label: STRING<br/>additionalLabels: LIST&lt;STRING&gt;<br/>description: STRING<br/>embedding: VECTOR")

Relationship("Relationship<br/>id: STRING | KEY<br/>type: STRING<br/>description: STRING<br/>embedding: VECTOR")

Property("Property<br/>id: STRING | KEY<br/>name: STRING<br/>type: STRING<br/>description: STRING<br/>unique: BOOLEAN<br/>nullable: BOOLEAN<br/>indexed: BOOLEAN<br/>existence: BOOLEAN<br/>embedding: VECTOR")

%% Relationships
Database -->|HAS_SCHEMA| Schema
Schema -->|HAS_NODE| Node
Schema -->|HAS_RELATIONSHIP| Relationship
Relationship -->|HAS_SOURCE_NODE| Node
Relationship -->|HAS_TARGET_NODE| Node
Relationship -->|HAS_PROPERTY| Property
Node -->|HAS_PROPERTY| Property
```

Nodes
* `Database`
    * Top level node containing information about the graph database
    * Properties: id, name, description, embedding, platform, service
* `Schema`
    * Contains details about the database schema or namespace
    * Properties: id, name, description, embedding
* `Node`
    * Represents a node label in the LPG
    * Contains information about nodes with this label in the graph database
    * Properties: id, label, additionalLabels, description, embedding
* `Relationship`
    * Represents a relationship type in the LPG
    * Contains information about relationships of this type in the graph database
    * Properties: id, type, description, embedding
* `Property`
    * Represents a property that can exist on nodes or relationships
    * Properties: id, name, type, description, unique, nullable, indexed, existence, embedding

Relationships
* `(:Database)-[:HAS_SCHEMA]->(:Schema)`
    * Defines the database to schema hierarchy
* `(:Schema)-[:HAS_NODE]->(:Node)`
    * Defines which node labels exist in the schema
* `(:Schema)-[:HAS_RELATIONSHIP]->(:Relationship)`
    * Defines which relationship types exist in the schema
* `(:Relationship)-[:HAS_SOURCE_NODE]->(:Node)`
    * Defines the source node label for a relationship type
* `(:Relationship)-[:HAS_TARGET_NODE]->(:Node)`
    * Defines the target node label for a relationship type
* `(:Node)-[:HAS_PROPERTY]->(:Property)`
    * Defines which properties exist on a node label
* `(:Relationship)-[:HAS_PROPERTY]->(:Property)`
    * Defines which properties exist on a relationship type

## Glossary Data Model **(Not Implemented)**

Data catalogs allow business terms to be defined and linked to nodes, relationships, and properties.
This allows semantic relationships to be inferred by shared business terms.

Nodes
* `Glossary`
    * The glossary containing categories and business terms
* `Category`
    * Contains information about a category in the glossary
* `BusinessTerm`
    * A leaf level term in the glossary
    * Defines globally recognized term across databases in the system

Relationships
* `(:Glossary)-[:HAS_CATEGORY]->(:Category)`
    * Defines glossary to category hierarchy
* `(:Category)-[:HAS_BUSINESS_TERM]->(:BusinessTerm)`
    * Defines category to business term hierarchy
* `(:Node)-[:RESOLVES_TO]->(:BusinessTerm)`
    * Defines how a node label resolves to a business term
* `(:Relationship)-[:RESOLVES_TO]->(:BusinessTerm)`
    * Defines how a relationship type resolves to a business term
* `(:Property)-[:RESOLVES_TO]->(:BusinessTerm)`
    * Defines how a property resolves to a business term

## Data Stewards **(Not Implemented)**

Data catalogs allow data stewards to be defined and linked to the appropriate assets in the graph database.

Nodes
* `Steward`

Relationships
* `(:Steward)-[:STEWARDS_SCHEMA]->(:Schema)`
* `(:Steward)-[:STEWARDS_NODE]->(:Node)`
* `(:Steward)-[:STEWARDS_RELATIONSHIP]->(:Relationship)`
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
* `(:DataQualityRule)-[:ENFORCES_NODE]->(:Node)`
* `(:DataQualityRule)-[:ENFORCES_RELATIONSHIP]->(:Relationship)`
* `(:DataQualityRule)-[:ENFORCES_PROPERTY]->(:Property)`
* `(:BusinessRule)-[:APPLIES_TO_NODE]->(:Node)`
* `(:BusinessRule)-[:APPLIES_TO_RELATIONSHIP]->(:Relationship)`
* `(:BusinessRule)-[:APPLIES_TO_PROPERTY]->(:Property)`
* `(:BusinessRule)-[:RELATED_TO]->(:BusinessTerm)`
    * Defines which business terms are related to the business rule
    * This relationship may be used to identify nodes, relationships, or properties that are impacted by a business rule

## Cypher Queries **(Not Implemented)**

Cypher queries may be cached in the graph and provided as few-shot examples in the context.

Nodes
* `CypherQuery`

Relationships
* `(:CypherQuery)-[:USES_NODE]->(:Node)`
* `(:CypherQuery)-[:USES_RELATIONSHIP]->(:Relationship)`
* `(:CypherQuery)-[:USES_PROPERTY]->(:Property)`

## Metrics + KPIs **(Not Implemented)**

Metrics and KPIs may be stored in the graph and linked to their associated nodes, relationships, and properties.
They may also be linked to `CypherQuery` nodes, which define how to calculate the metric.
`Metric` is the main node label, however they may also have the additional node label `KPI`.

Nodes
* `Metric`
* `Metric&KPI`
    * All `KPI` labels are an additional label on `Metric` nodes

Relationships
* `(:Metric&KPI)-[:HAS_CYPHER_QUERY]->(:CypherQuery)`