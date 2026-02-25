"""Common ingest functions for Neo4j."""

from neo4j import Driver, RoutingControl
from ..data_model.core import (
    Database,
    Schema,
    Table,
    Column,
    HasSchema,
    HasTable,
    HasColumn,
    References,
)
from ..data_model.expanded import (
    Value,
    HasValue,
    Glossary,
    Category,
    BusinessTerm,
    HasCategory,
    HasBusinessTerm,
    Query,
    UsesTable,
    UsesColumn,
)


class Neo4jLoader:
    """
    Loader class for Neo4j.
    Loads nodes and relationships into Neo4j.
    """

    def __init__(self, neo4j_driver: Driver, database_name: str = "neo4j"):
        """
        Initialize the Neo4j loader.
        """
        self.neo4j_driver = neo4j_driver
        self.database_name = database_name

    def load_database_nodes(
        self, database_nodes: list[Database]
    ) -> dict:
        _, summary, _ = self.neo4j_driver.execute_query(
            query_="""
        UNWIND $rows as row
        MERGE (d:Database {id: row.id})
        ON CREATE
            SET d.name = row.name, 
                d.description = row.description,
                d.service = row.service,
                d.platform = row.platform
        """,
            parameters_={"rows": [n.model_dump() for n in database_nodes]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )

        return summary.counters.__dict__


    def load_schema_nodes(
        self, schema_nodes: list[Schema]
    ) -> dict:
        _, summary, _ = self.neo4j_driver.execute_query(
            query_="""
        UNWIND $rows as row
        MERGE (s:Schema {id: row.id})
        ON CREATE
            SET s.name = row.name,
                s.description = row.description
        """,
            parameters_={"rows": [n.model_dump() for n in schema_nodes]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_table_nodes(
        self, table_nodes: list[Table]
    ) -> dict:
        _, summary, _ = self.neo4j_driver.execute_query(
            query_="""
        UNWIND $rows as row
        MERGE (t:Table {id: row.id})
        ON CREATE
            SET t.name = row.name, 
                t.description = row.description
        """,
            parameters_={"rows": [n.model_dump() for n in table_nodes]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_column_nodes(
        self, column_nodes: list[Column]
    ) -> dict:
        _, summary, _ = self.neo4j_driver.execute_query(
            query_="""
        UNWIND $rows as row
        MERGE (c:Column {id: row.id})
        ON CREATE
            SET c.name = row.name, 
                c.description = row.description, 
                c.type = row.type, 
                c.nullable = row.nullable, 
                c.is_primary_key = row.is_primary_key, 
                c.is_foreign_key = row.is_foreign_key
        """,
            parameters_={"rows": [n.model_dump() for n in column_nodes]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_value_nodes(
        self, value_nodes: list[Value]
    ) -> dict:
        """
        Load Value nodes into Neo4j.
        """

        _, summary, _ = self.neo4j_driver.execute_query(
            query_="""
        UNWIND $rows as row
        MERGE (v:Value {id: row.id})
        ON CREATE
            SET v.value = row.value
        """,
            parameters_={"rows": [n.model_dump() for n in value_nodes]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_has_schema_relationships(
        self, has_schema_relationships: list[HasSchema]
    ) -> dict:
        _, summary, _ = self.neo4j_driver.execute_query(
            query_="""
        UNWIND $rows as row
        MATCH (d:Database {id: row.database_id})
        MATCH (s:Schema {id: row.schema_id})
        MERGE (d)-[:HAS_SCHEMA]->(s)
        """,
            parameters_={"rows": [n.model_dump() for n in has_schema_relationships]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_has_table_relationships(
        self, has_table_relationships: list[HasTable]
    ) -> dict:
        _, summary, _ = self.neo4j_driver.execute_query(
            query_="""
        UNWIND $rows as row
        MATCH (s:Schema {id: row.schema_id})
        MATCH (t:Table {id: row.table_id})
        MERGE (s)-[:HAS_TABLE]->(t)
        """,
            parameters_={"rows": [n.model_dump() for n in has_table_relationships]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_has_column_relationships(
        self, has_column_relationships: list[HasColumn]
    ) -> dict:
        _, summary, _ = self.neo4j_driver.execute_query(
            query_="""
        UNWIND $rows as row
        MATCH (t:Table {id: row.table_id})
        MATCH (c:Column {id: row.column_id})
        MERGE (t)-[:HAS_COLUMN]->(c)
        """,
            parameters_={"rows": [n.model_dump() for n in has_column_relationships]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_references_relationships(
        self, references_relationships: list[References]
    ) -> dict:
        _, summary, _ = self.neo4j_driver.execute_query(
            query_="""
        UNWIND $rows as row
        MATCH (c1:Column {id: row.source_column_id})
        MATCH (c2:Column {id: row.target_column_id})
        MERGE (c1)-[r:REFERENCES]->(c2)
        ON CREATE
            SET r.criteria = row.criteria
        """,
            parameters_={"rows": [n.model_dump() for n in references_relationships]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_glossary_nodes(
        self, glossary_nodes: list[Glossary]
    ) -> dict:
        _, summary, _ = self.neo4j_driver.execute_query(
            query_="""
        UNWIND $rows as row
        MERGE (g:Glossary {id: row.id})
        ON CREATE
            SET g.name = row.name,
                g.description = row.description
        """,
            parameters_={"rows": [n.model_dump() for n in glossary_nodes]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_category_nodes(
        self, category_nodes: list[Category]
    ) -> dict:
        _, summary, _ = self.neo4j_driver.execute_query(
            query_="""
        UNWIND $rows as row
        MERGE (cat:Category {id: row.id})
        ON CREATE
            SET cat.name = row.name,
                cat.description = row.description
        """,
            parameters_={"rows": [n.model_dump() for n in category_nodes]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_business_term_nodes(
        self, business_term_nodes: list[BusinessTerm]
    ) -> dict:
        _, summary, _ = self.neo4j_driver.execute_query(
            query_="""
        UNWIND $rows as row
        MERGE (bt:BusinessTerm {id: row.id})
        ON CREATE
            SET bt.name = row.name,
                bt.description = row.description
        """,
            parameters_={"rows": [n.model_dump() for n in business_term_nodes]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_has_category_relationships(
        self, has_category_relationships: list[HasCategory]
    ) -> dict:
        _, summary, _ = self.neo4j_driver.execute_query(
            query_="""
        UNWIND $rows as row
        MATCH (g:Glossary {id: row.glossary_id})
        MATCH (cat:Category {id: row.category_id})
        MERGE (g)-[:HAS_CATEGORY]->(cat)
        """,
            parameters_={"rows": [n.model_dump() for n in has_category_relationships]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_has_business_term_relationships(
        self, has_business_term_relationships: list[HasBusinessTerm]
    ) -> dict:
        _, summary, _ = self.neo4j_driver.execute_query(
            query_="""
        UNWIND $rows as row
        MATCH (parent:Category {id: row.category_id})
        MATCH (bt:BusinessTerm {id: row.business_term_id})
        MERGE (parent)-[:HAS_BUSINESS_TERM]->(bt)
        """,
            parameters_={"rows": [n.model_dump() for n in has_business_term_relationships]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_has_value_relationships(
        self, has_value_relationships: list[HasValue]
    ) -> dict:
        _, summary, _ = self.neo4j_driver.execute_query(
            query_="""
        UNWIND $rows as row
        MATCH (c:Column {id: row.column_id})
        MATCH (v:Value {id: row.value_id})
        MERGE (c)-[:HAS_VALUE]->(v)
        """,
            parameters_={"rows": [n.model_dump() for n in has_value_relationships]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__

    def load_query_nodes(
        self, query_nodes: list[Query]
    ) -> dict:
        _, summary, _ = self.neo4j_driver.execute_query(
            query_="""
        UNWIND $rows as row
        MERGE (q:Query {id: row.id})
        ON CREATE
            SET q.content = row.content,
                q.description = row.description
        """,
            parameters_={"rows": [n.model_dump() for n in query_nodes]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__

    def load_uses_table_relationships(
        self, uses_table_relationships: list[UsesTable]
    ) -> dict:
        _, summary, _ = self.neo4j_driver.execute_query(
            query_="""
        UNWIND $rows as row
        MATCH (q:Query {id: row.query_id})
        MATCH (t:Table {id: row.table_id})
        MERGE (q)-[:USES_TABLE]->(t)
        """,
            parameters_={"rows": [n.model_dump() for n in uses_table_relationships]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__

    def load_uses_column_relationships(
        self, uses_column_relationships: list[UsesColumn]
    ) -> dict:
        _, summary, _ = self.neo4j_driver.execute_query(
            query_="""
        UNWIND $rows as row
        MATCH (q:Query {id: row.query_id})
        MATCH (c:Column {id: row.column_id})
        MERGE (q)-[:USES_COLUMN]->(c)
        """,    
            parameters_={"rows": [n.model_dump() for n in uses_column_relationships]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__