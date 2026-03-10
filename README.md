# Text2SQL Template

End to end template for generating a RDBMS metadata knowledge graph for Text2SQL workflows.

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management and requires Python 3.12 or higher.

### Prerequisites

Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install All Dependencies (Recommended)

For most users, install all dependencies to run the complete workflow:
```bash
make install
```

This installs all dependency groups and allows you to:
- Create the metadata graph from BigQuery
- Run the MCP server
- Run the Text2SQL agent

### Install Specific Components

If you only need specific components, you can install individual dependency groups:

**Metadata Graph Only** (BigQuery ETL + embeddings)
```bash
make install-metadata-graph
```

**MCP Server Only** (SQL metadata retrieval server)
```bash
make install-mcp-server
```

**Agent Only** (Text2SQL agent with MCP servers)
```bash
make install-agent
```
*Note: The agent group automatically includes mcp-server dependencies*

### Dependency Groups

The project is organized into the following dependency groups:

- **metadata-graph**: BigQuery metadata extraction, Neo4j loading, and embedding generation
- **mcp-server**: Local MCP server for SQL metadata retrieval from Neo4j
- **agent**: Text2SQL agent with LangChain (includes mcp-server dependencies)
- **dev**: Development tools (Jupyter notebooks)

## Metadata Graph

The metadata graph has the following schema. All connectors must convert their schema information to this graph schema to be compatible with the provided MCP server and ingestion tooling.

```mermaid
---
config:
    layout: elk
---
graph LR
%% Nodes
Database("Database<br/>id: STRING | KEY<br/>name: STRING<br/>description: STRING<br/>embedding: VECTOR")
Schema("Schema<br/>id: STRING | KEY<br/>name: STRING<br/>description: STRING<br/>embedding: VECTOR")
Table("Table<br/>id: STRING | KEY<br/>name: STRING<br/>description: STRING<br/>embedding: VECTOR")
Column("Column<br/>id: STRING | KEY<br/>name: STRING<br/>description: STRING<br/>embedding: VECTOR<br/>type: STRING<br/>nullable: BOOLEAN<br/>isPrimaryKey: BOOLEAN<br/>isForeignKey: BOOLEAN")
Value("Value<br/>id: STRING | KEY<br/>value: STRING")

%% Relationships
Database -->|HAS_SCHEMA| Schema
Schema -->|HAS_TABLE| Table
Table -->|HAS_COLUMN| Column
Column -->|REFERENCES| Column
Column -->|HAS_VALUE| Value


%% Styling
classDef node_0_color fill:#e3f2fd,stroke:#1976d2,stroke-width:3px,color:#000,font-size:12px
class Database node_0_color

classDef node_1_color fill:#fff9c4,stroke:#f57f17,stroke-width:3px,color:#000,font-size:12px
class Schema node_1_color

classDef node_2_color fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px,color:#000,font-size:12px
class Table node_2_color

classDef node_3_color fill:#e8f5e8,stroke:#388e3c,stroke-width:3px,color:#000,font-size:12px
class Column node_3_color

classDef node_4_color fill:#fff3e0,stroke:#f57c00,stroke-width:3px,color:#000,font-size:12px
class Value node_4_color
```

Nodes
* `Database`
* `Schema`
* `Table`
* `Column`
* `Value`

Relationships
* `(:Database)-[:HAS_Schema]->(:Schema)`
* `(:Schema)-[:HAS_TABLE]->(:Table)`
* `(:Table)-[:HAS_COLUMN]->(:Column)`
* `(:Column)-[:HAS_VALUE]->(:Value)`
* `(:Column)-[:REFERENCES]->(:Column)`


## Graph Generation

This project provides workflow classes that organize the ETL process into reusable components:
* **Extractors** - Connect to source data and read metadata tables
* **Transformers** - Transform metadata into defined Neo4j schema
* **Loaders** - Ingest transformed data into Neo4j
* **Workflows** - Orchestrate the extract, transform, and load process

Each workflow is implemented as a class that encapsulates its extractor, transformer, and loader components, providing a clean interface for metadata ingestion.

### Workflow Class Architecture

All workflows follow a consistent class-based architecture:

```python
class Workflow:
    def __init__(self, clients, config):
        # Initialize with required clients and configuration
        self.extractor = Extractor(...)
        self.transformer = Transformer(...)
        self.loader = Loader(...)

    def extract_metadata(self):
        # Extract data from source and cache
        pass

    def transform_metadata(self):
        # Transform extracted data to graph schema and cache
        pass

    def load_metadata(self):
        # Load transformed data into Neo4j
        pass

    def run(self):
        # Orchestrate the full ETL pipeline
        self.extract_metadata()
        self.transform_metadata()
        self.load_metadata()
```

**Benefits of the class-based approach:**
* **Modularity** - Each component (extractor, transformer, loader) is independently testable
* **Reusability** - Components can be reused across different workflows
* **Maintainability** - Clear separation of concerns makes the codebase easier to understand and modify
* **Caching** - Intermediate results are cached as class properties, enabling step-by-step execution
* **Flexibility** - Individual ETL steps can be run separately for debugging or custom workflows

### Connectors

#### **BigQuery Schema Connector**

Connector for reading BigQuery Information Schema tables and ingesting **schema metadata** into Neo4j. Primary and foreign keys must be defined in the Information Schema tables in order for column level relationships to be created in the Neo4j graph.

**What it extracts:**
* Database (GCP project)
* Schemas (datasets)
* Tables with descriptions
* Columns with types, constraints, descriptions
* Column references (foreign keys)
* Column unique values (sample data)

This workflow requires the following variables to be set in the `.env` file:
* NEO4J_USERNAME=neo4j-username
* NEO4J_PASSWORD=neo4j-password
* NEO4J_URI=neo4j-uri
* NEO4J_DATABASE=neo4j-database
* GCP_PROJECT_ID=project-id
* BIGQUERY_DATASET_ID=dataset-id

#### **BigQuery Logs Connector**

Connector for extracting **query logs** from BigQuery `INFORMATION_SCHEMA.JOBS_BY_PROJECT`, parsing SQL queries to understand table and column usage, and loading query patterns into Neo4j.

**What it extracts:**
* SQL Queries
* Tables and columns referenced in queries (discovered via SQL parsing)
* Join relationships between tables (from SQL JOINs)
* Query-to-table and query-to-column usage relationships

**Graph schema additions:**
* `Query` nodes with properties:
  - `query` - The SQL text
  - `query_id` - Hash of query text
* `(:Query)-[:USES_TABLE]->(:Table)` relationships
* `(:Query)-[:USES_COLUMN]->(:Column)` relationships

This workflow requires the following variables to be set in the `.env` file:
* NEO4J_USERNAME=neo4j-username
* NEO4J_PASSWORD=neo4j-password
* NEO4J_URI=neo4j-uri
* NEO4J_DATABASE=neo4j-database
* GCP_PROJECT_ID=project-id
* BIGQUERY_DATASET_ID=dataset-id
* BIGQUERY_REGION=region-us (optional, defaults to region-us)


##### Workflow Architecture
```mermaid
---
config:
    layout: elk
---
graph LR
    subgraph Schema["Graph Schema"]
        GS(Data Model Definition)
    end

    subgraph Source["Source Repository"]
        BQ(BigQuery Database)        
    end

    subgraph ETL["ETL Processes"]
        QE(Read RDBMS Schema)   
        PM(Validate + Transform<br>with Pydantic) 
    
        QE -->|Raw Data<br/>JSON| PM
    end
    
    subgraph Graph["Database"]
        NEO[(Neo4j Graph)]
    end

    BQ -->|Information Schema| QE
    GS -->|Schema Definition| PM
    PM -->|Ingest Data| NEO
```

##### Code Example - Schema Connector

```python
import os
from neo4j import GraphDatabase
from google.cloud import bigquery
from semantic_graph.connectors.bigquery import BigQuerySchemaWorkflow

# Initialize clients
neo4j_driver = GraphDatabase.driver(
    uri=os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
)
neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
bigquery_client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"))

# Create workflow instance
workflow = BigQuerySchemaWorkflow(
    client=bigquery_client,
    project_id=os.getenv("GCP_PROJECT_ID"),
    dataset_id=os.getenv("BIGQUERY_DATASET_ID"),
    neo4j_driver=neo4j_driver,
    database_name=neo4j_database,
)

# Run the workflow to extract, transform, and load BigQuery schema metadata into Neo4j
workflow.run()
```

##### Code Example - Logs Connector

```python
import os
from neo4j import GraphDatabase
from google.cloud import bigquery
from semantic_graph.connectors.bigquery import BigQueryLogsWorkflow

# Initialize clients
neo4j_driver = GraphDatabase.driver(
    uri=os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
)
neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
bigquery_client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"))

# Create workflow instance
workflow = BigQueryLogsWorkflow(
    client=bigquery_client,
    project_id=os.getenv("GCP_PROJECT_ID"),
    neo4j_driver=neo4j_driver,
    database_name=neo4j_database,
)

# Run the workflow to extract query logs, parse SQL, and load into Neo4j
workflow.run(
    dataset_id=os.getenv("BIGQUERY_DATASET_ID"),
    region="region-us",
    start_timestamp="2024-01-01 00:00:00",  # Optional
    end_timestamp="2024-01-31 23:59:59",    # Optional
    limit=100,                               # Optional, default 100
    drop_failed_queries=True,                # Optional, default True
)
```

##### Combined Usage

For the most complete picture, run both connectors:

```python
# 1. Extract schema metadata
schema_workflow = BigQuerySchemaWorkflow(...)
schema_workflow.run()

# 2. Extract query logs
logs_workflow = BigQueryLogsWorkflow(...)
logs_workflow.run(dataset_id=os.getenv("BIGQUERY_DATASET_ID"))
```

This allows you to compare declared schema vs. actual usage patterns.

#### **GCP Dataplex Universal Catalog**

Connector for reading BigQuery metadata and Glossary information from Dataplex and ingesting into Neo4j. Please see the [Dataplex README](./connectors/dataplex/README.md) for more information and caveats of using this connector.

##### Workflow Architecture 

```mermaid
---
config:
    layout: elk
---
graph LR
    subgraph Schema["Graph Schema"]
        GS(Data Model Definition)
    end
    subgraph Big["Google Cloud Platform"]
        subgraph SR["Source Repository"]
            BQ(BigQuery Database)  
        end      
    

        subgraph Source["GCP Dataplex Universal Catalog"]
            G(Glossaries)
            MT(Metadata Types)        
        end
    end

    subgraph ETL["ETL Processes"]
        QE(Read Data Catalog)   
        PM(Validate + Transform<br>with Pydantic) 
    
        QE -->|Raw Data<br/>JSON| PM
    end
    
    subgraph Graph["Database"]
        NEO[(Neo4j Graph)]
    end

    BQ -->|BigQuery Metadata|MT
    G -->| Glossary Content| QE
    MT -->|BigQuery Metadata| QE
    GS -->|Schema Definition| PM
    PM -->|Ingest Data| NEO
```

#### **Query Logs**

Connector for parsing query log JSON files into Neo4j. Please see the [Query Logs README](./connectors/query_log/README.md) for more information and caveats of using this connector.

##### Workflow Architecture

```mermaid
---
config:
    layout: elk
---
graph LR
    subgraph Schema["Graph Schema"]
        GS(Data Model Definition)
    end
    subgraph Big["Google Cloud Platform"]
        subgraph Source["Source Repository"]
            BQ(BigQuery Database)
        end

        subgraph Logging["GCP Logging"]
            GL(Logs)
        end
    end

    subgraph ETL["ETL Processes"]
        QL(Read Query Logs)
        PM(Validate + Transform<br>with Pydantic)

        QL -->|Raw Logs<br/>JSON| PM
    end

    subgraph Graph["Database"]
        NEO[(Neo4j Graph)]
    end

    BQ -->|Query Logs| GL
    GL -->|Query Logs| QL
    GS -->|Schema Definition| PM
    PM -->|Ingest Data| NEO
```

### Embeddings 

Embeddings may be generated for the `description` fields of the following nodes:
* `Database`
* `Schema`
* `Table`
* `Column`
* `BusinessTerm`

This project currently supports the following embeddings Providers:
* OpenAI

This workflow requires the following variables to be set in the `.env` file:
* OPENAI_API_KEY=sk-...

#### Workflow Architecture

```mermaid
---
config:
    layout: elk
---
graph LR

    subgraph D["Database Preparation"]
        VI(Create Vector Index)
    end

    subgraph ES["Embedding Service"]
        E(OpenAI Embeddings)
    end

    subgraph Graph["Database"]
        NEO[(Neo4j Graph)]
    end

    subgraph EP["Embedding Workflow"]
        C(Create Embeddings) 
    end
    
    VI-->NEO

    C<-->E

    NEO-->|Unprocessed Node Descriptions|C
    C-->|Embeddings|NEO
```

#### Code Example

```python
import asyncio
import os
from neo4j import GraphDatabase
from openai import AsyncOpenAI
from embeddings.openai_embeddings import OpenAIEmbeddingWorkflow

# Initialize clients
neo4j_driver = GraphDatabase.driver(
    uri=os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
)
neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
embedding_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Create workflow instance
workflow = OpenAIEmbeddingWorkflow(
    async_embedding_client=embedding_client,
    embedding_model="text-embedding-3-small",
    dimensions=768,
    neo4j_driver=neo4j_driver,
    database_name=neo4j_database,
)

# The node labels to generate embeddings for
node_labels = ["Database", "Table", "Column"]

# Run the workflow to create embeddings for the nodes
await workflow.arun(node_labels=node_labels)
```

### Full Pipeline

The full graph generation pipeline will run the BigQuery workflow followed by the embedding generation workflow. 

It requires the following variables to be set in the `.env` file:
* NEO4J_USERNAME=neo4j-username
* NEO4J_PASSWORD=neo4j-password
* NEO4J_URI=neo4j-uri
* NEO4J_DATABASE=neo4j-database
* GCP_PROJECT_ID=project-id
* BIGQUERY_DATASET_ID=dataset-id
* OPENAI_API_KEY=sk-...

#### Architecture

The combined BigQuery + Embeddings workflow is seen below.

```mermaid
flowchart LR
    subgraph Schema["Graph Schema"]
        GS(Data Model Definition)
    end

    subgraph Source["Source Repository"]
        BQ(BigQuery Database)        
    end

    subgraph ETL["ETL Processes"]
        QE(Read RDBMS Schema)   
        PM(Validate + Transform<br>with Pydantic) 
    end
    
    subgraph Graph["Database"]
        NEO[(Neo4j Graph)]
    end

    subgraph D["Database Preparation"]
        VI(Create Vector Index)
    end

    subgraph ES["Embedding Service"]
        E(OpenAI Embeddings)
    end

    subgraph EP["Embedding Workflow"]
        C(Create Embeddings) 
    end

    %% BigQuery Flow
    BQ -->|Information Schema| QE
    QE -->|Raw Data JSON| PM
    GS -->|Schema Definition| PM
    PM -->|Ingest Data| NEO

    %% Embeddings Flow
    NEO -->|Database Ready| VI
    VI -->|Vector Index Created| NEO
    NEO -->|Unprocessed Node Descriptions| C
    C <--> E
    C -->|Embeddings| NEO
```

**Running The Full Workflow**

To run the full workflow, use the following Make command:

```bash
make create-graph
```

## Sample Dataset

This repository contains a sample dataset of ecommerce data.

Ensure that the following environment variable is set before running and that you are credentialed via the gcloud cli.

```bash
GCP_PROJECT_ID=project-id
```

To create the dataset in your BigQuery instance, you may run the following Make command.

```bash
make load-ecommerce-dataset
```

## MCP

This project uses two MCP servers for the Text2SQL agent.

### **Local SQL Metadata MCP Server**

This is a custom SQL metadata retrieval MCP server that provides tools to query the Neo4j database for relevant RDBMS schema information using semantic similarity search.

**Tools**
* `get_metadata_schema_by_semantic_similarity` - Retrieves table metadata using vector similarity search on column embeddings and graph traversal. Returns the most relevant tables and column subset with their references, and example values.
* `get_full_metadata_schema` - Retrieves complete metadata schema for all tables in the database. Returns the tables and columns with their references, and example values.


**Environment Variables**
* `NEO4J_URI` - Neo4j database connection URI (e.g., `bolt://localhost:7687`)
* `NEO4J_USERNAME` - Neo4j username (default: `neo4j`)
* `NEO4J_PASSWORD` - Neo4j password
* `NEO4J_DATABASE` - Neo4j database name (default: `neo4j`)
* `OPENAI_API_KEY` - OpenAI API key for generating query embeddings
* `EMBEDDING_MODEL` - OpenAI embedding model to use (default: `text-embedding-3-small`)
* `EMBEDDING_DIMENSIONS` - Embedding vector dimensions (default: `768`)



### **Remote BigQuery MCP Server**

This is the official BigQuery remote MCP server and will be used to execute SQL queries against our database.

Since this is a remote server, we don't need to worry about hosting it locally. We can just connect to the MCP endpoint in our GCP environment.

**Tools** (Filtered subset of total tools the server provides)
* `execute_sql` - Execute a SQL query against BigQuery. Returns the raw results.

*Unused BigQuery MCP Tools*
* `list_dataset_ids`
* `get_dataset_info`
* `list_table_ids`
* `get_table_info`

#### Set Up

Enable use of the [Bigquery MCP server](https://docs.cloud.google.com/bigquery/docs/reference/mcp) in your project.

Additional information may be found [here](https://docs.cloud.google.com/bigquery/docs/use-bigquery-mcp).

PROJECT_ID=Google Cloud project ID
SERVICE=bigquery.googleapis.com

```bash
gcloud beta services mcp enable SERVICE --project=PROJECT_ID
```

To disable again run

```bash
gcloud beta services mcp disable SERVICE --project=PROJECT_ID
```

You can test the BigQuery server connection with the following curl command

```bash
curl -k \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -d '{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "execute_sql",
    "arguments": {
      "projectId": "<PROJECT_ID>",
      "query": "SELECT table_name FROM `<PROJECT_ID>.<DATASET_ID>.INFORMATION_SCHEMA.TABLES`"
    }
  }
}' \
  https://bigquery.googleapis.com/mcp
```

## Agent

This is the Text2SQL agent that converts natural language questions into SQL queries for BigQuery. The agent uses two MCP servers to:
1. Retrieve relevant database metadata from Neo4j using semantic similarity
2. Execute generated SQL queries against BigQuery

The agent architecture can be seen below.

```mermaid
---
config:
    layout: dagre
---

graph LR
    
    subgraph GCP["GCP Environment"]
        BQMCP(BigQuery<br>MCP)

        subgraph DataWarehouse["Data Warehouse"]
            BQData[(BigQuery)]
        end
        
        BQMCP <--> BQData
    end

    subgraph Local["Local Environment"]
        Agent("Text2SQL Agent")
        MetadataMCP("SQL Metadata<br/>MCP")
        
        subgraph Graph["Database"]
            NEO[(Neo4j Graph)]
        end
        
        Agent <--> MetadataMCP
        MetadataMCP <--> NEO
    end
    
    User("User")
    
    subgraph LLM["LLM Service"]
        Model("LLM")
    end
    
    User <--> Agent
    Agent <--> Model
    Agent <--> BQMCP

```

**How it works**
1. User asks a natural language question about the data
2. Agent calls the SQL Metadata MCP server to retrieve relevant table schemas
3. Agent generates a SQL query via an LLM call based on the retrieved metadata context
4. Agent calls `execute_sql` from the BigQuery MCP server to run the query against BigQuery
5. Agent returns formatted results to the user

**Running the Agent**

Use this command to run the agent locally:
```bash
make agent
```

The agent will start an interactive chat session in the terminal where you can ask questions about your data.


**BigQuery MCP Authentication**

The agent uses Google Cloud Application Default Credentials for BigQuery authentication:

```python
class GoogleAuth(httpx.Auth):
    def __init__(self):
        self.credentials, _ = default()

    def auth_flow(self, request):
        self.credentials.refresh(Request())
        request.headers["Authorization"] = f"Bearer {self.credentials.token}"
        yield request
```

Make sure you're authenticated with:
```bash
gcloud auth application-default login
```

**Environment Variables**

Required environment variables (add to `.env` file):

**Neo4j Connection**
* `NEO4J_URI` - Neo4j database URI (e.g., `bolt://localhost:7687`)
* `NEO4J_USERNAME` - Neo4j username (default: `neo4j`)
* `NEO4J_PASSWORD` - Neo4j password
* `NEO4J_DATABASE` - Neo4j database name (default: `neo4j`)

**LLM - OpenAI**
* `OPENAI_API_KEY` - OpenAI API key for embeddings and LLM

**Example Usage**

```
> What are the total sales by product category?

Agent: [Calls get_metadata_schema_by_semantic_similarity with query about sales and categories]
Agent: [Generates SQL query using retrieved schema]
Agent: [Calls execute_sql with generated query]
Agent: Here are the total sales by product category:
- Electronics: $15,234.50
- Clothing: $8,912.30
...
```



