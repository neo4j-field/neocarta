"""Common ingest functions for Neo4j."""

from neo4j import Driver, RoutingControl
from ...data_model.core import (
    Database,
    Schema,
    Table,
    Column,
    HasSchema,
    HasTable,
    HasColumn,
    References,
)
from ...data_model.expanded import (
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

from functools import partial

from ..utils import _validate_properties_list, _build_node_ingest_query, _build_relationship_ingest_query, write_neo4j_constraints
from .constraints import KEY_CONSTRAINTS_LOOKUP, UNIQUE_CONSTRAINTS_LOOKUP


class Neo4jRDBMSLoader:
    """
    Loader class for loading RDBMS metadata into Neo4j.
    Loads nodes and relationships into Neo4j.
    """

    def __init__(self, neo4j_driver: Driver, database_name: str = "neo4j"):
        """
        Initialize the Neo4j loader.
        """
        self.neo4j_driver = neo4j_driver
        self.database_name = database_name

        self._write_node_constraint = partial(
            write_neo4j_constraints, 
            neo4j_driver=self.neo4j_driver, 
            key_constraints=KEY_CONSTRAINTS_LOOKUP, 
            unique_constraints=UNIQUE_CONSTRAINTS_LOOKUP, 
            database_name=self.database_name
        )

    def load_database_nodes(
        self, database_nodes: list[Database],
        overwrite_existing: bool = False,
        properties_list: list[str] = ["name", "description", "service", "platform"]
    ) -> dict:

        _validate_properties_list(Database, properties_list)
        self._write_node_constraint(node_labels=["Database"])
        query = _build_node_ingest_query("Database", overwrite_existing, properties_list)
        
        _, summary, _ = self.neo4j_driver.execute_query(
            query_=query,
            parameters_={"rows": [n.model_dump() for n in database_nodes]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )

        return summary.counters.__dict__


    def load_schema_nodes(
        self,
        schema_nodes: list[Schema],
        overwrite_existing: bool = False,
        properties_list: list[str] = ["name", "description"]
    ) -> dict:
        _validate_properties_list(Schema, properties_list)

        self._write_node_constraint(node_labels=["Schema"])
        query = _build_node_ingest_query("Schema", overwrite_existing, properties_list)

        _, summary, _ = self.neo4j_driver.execute_query(
            query_=query,
            parameters_={"rows": [n.model_dump() for n in schema_nodes]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_table_nodes(
        self,
        table_nodes: list[Table],
        overwrite_existing: bool = False,
        properties_list: list[str] = ["name", "description"]
    ) -> dict:
        _validate_properties_list(Table, properties_list)

        self._write_node_constraint(node_labels=["Table"])
        query = _build_node_ingest_query("Table", overwrite_existing, properties_list)

        _, summary, _ = self.neo4j_driver.execute_query(
            query_=query,
            parameters_={"rows": [n.model_dump() for n in table_nodes]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_column_nodes(
        self,
        column_nodes: list[Column],
        overwrite_existing: bool = False,
        properties_list: list[str] = ["name", "description", "type", "nullable", "is_primary_key", "is_foreign_key"]
    ) -> dict:
        _validate_properties_list(Column, properties_list)

        self._write_node_constraint(node_labels=["Column"])
        query = _build_node_ingest_query("Column", overwrite_existing, properties_list)

        _, summary, _ = self.neo4j_driver.execute_query(
            query_=query,
            parameters_={"rows": [n.model_dump() for n in column_nodes]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_value_nodes(
        self,
        value_nodes: list[Value],
        overwrite_existing: bool = False,
        properties_list: list[str] = ["value"]
    ) -> dict:
        """
        Load Value nodes into Neo4j.
        """
        _validate_properties_list(Value, properties_list)

        self._write_node_constraint(node_labels=["Value"])
        query = _build_node_ingest_query("Value", overwrite_existing, properties_list)

        _, summary, _ = self.neo4j_driver.execute_query(
            query_=query,
            parameters_={"rows": [n.model_dump() for n in value_nodes]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_has_schema_relationships(
        self,
        has_schema_relationships: list[HasSchema],
        overwrite_existing: bool = False,
        properties_list: list[str] = []
    ) -> dict:
        if properties_list:
            _validate_properties_list(HasSchema, properties_list)

        query = _build_relationship_ingest_query(
            "HAS_SCHEMA",
            "Database",
            "Schema",
            "database_id",
            "schema_id",
            overwrite_existing,
            properties_list
        )

        _, summary, _ = self.neo4j_driver.execute_query(
            query_=query,
            parameters_={"rows": [n.model_dump() for n in has_schema_relationships]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_has_table_relationships(
        self,
        has_table_relationships: list[HasTable],
        overwrite_existing: bool = False,
        properties_list: list[str] = []
    ) -> dict:
        if properties_list:
            _validate_properties_list(HasTable, properties_list)

        query = _build_relationship_ingest_query(
            "HAS_TABLE",
            "Schema",
            "Table",
            "schema_id",
            "table_id",
            overwrite_existing,
            properties_list
        )

        _, summary, _ = self.neo4j_driver.execute_query(
            query_=query,
            parameters_={"rows": [n.model_dump() for n in has_table_relationships]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_has_column_relationships(
        self,
        has_column_relationships: list[HasColumn],
        overwrite_existing: bool = False,
        properties_list: list[str] = []
    ) -> dict:
        if properties_list:
            _validate_properties_list(HasColumn, properties_list)

        query = _build_relationship_ingest_query(
            "HAS_COLUMN",
            "Table",
            "Column",
            "table_id",
            "column_id",
            overwrite_existing,
            properties_list
        )

        _, summary, _ = self.neo4j_driver.execute_query(
            query_=query,
            parameters_={"rows": [n.model_dump() for n in has_column_relationships]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_references_relationships(
        self,
        references_relationships: list[References],
        overwrite_existing: bool = False,
        properties_list: list[str] = ["criteria"]
    ) -> dict:
        if properties_list:
            _validate_properties_list(References, properties_list)

        query = _build_relationship_ingest_query(
            "REFERENCES",
            "Column",
            "Column",
            "source_column_id",
            "target_column_id",
            overwrite_existing,
            properties_list
        )

        _, summary, _ = self.neo4j_driver.execute_query(
            query_=query,
            parameters_={"rows": [n.model_dump() for n in references_relationships]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_glossary_nodes(
        self,
        glossary_nodes: list[Glossary],
        overwrite_existing: bool = False,
        properties_list: list[str] = ["name", "description"]
    ) -> dict:
        _validate_properties_list(Glossary, properties_list)

        self._write_node_constraint(node_labels=["Glossary"])
        query = _build_node_ingest_query("Glossary", overwrite_existing, properties_list)

        _, summary, _ = self.neo4j_driver.execute_query(
            query_=query,
            parameters_={"rows": [n.model_dump() for n in glossary_nodes]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_category_nodes(
        self,
        category_nodes: list[Category],
        overwrite_existing: bool = False,
        properties_list: list[str] = ["name", "description"]
    ) -> dict:
        _validate_properties_list(Category, properties_list)

        self._write_node_constraint(node_labels=["Category"])
        query = _build_node_ingest_query("Category", overwrite_existing, properties_list)

        _, summary, _ = self.neo4j_driver.execute_query(
            query_=query,
            parameters_={"rows": [n.model_dump() for n in category_nodes]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_business_term_nodes(
        self,
        business_term_nodes: list[BusinessTerm],
        overwrite_existing: bool = False,
        properties_list: list[str] = ["name", "description"]
    ) -> dict:
        _validate_properties_list(BusinessTerm, properties_list)

        self._write_node_constraint(node_labels=["BusinessTerm"])
        query = _build_node_ingest_query("BusinessTerm", overwrite_existing, properties_list)

        _, summary, _ = self.neo4j_driver.execute_query(
            query_=query,
            parameters_={"rows": [n.model_dump() for n in business_term_nodes]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_has_category_relationships(
        self,
        has_category_relationships: list[HasCategory],
        overwrite_existing: bool = False,
        properties_list: list[str] = []
    ) -> dict:
        if properties_list:
            _validate_properties_list(HasCategory, properties_list)

        query = _build_relationship_ingest_query(
            "HAS_CATEGORY",
            "Glossary",
            "Category",
            "glossary_id",
            "category_id",
            overwrite_existing,
            properties_list
        )

        _, summary, _ = self.neo4j_driver.execute_query(
            query_=query,
            parameters_={"rows": [n.model_dump() for n in has_category_relationships]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_has_business_term_relationships(
        self,
        has_business_term_relationships: list[HasBusinessTerm],
        overwrite_existing: bool = False,
        properties_list: list[str] = []
    ) -> dict:
        if properties_list:
            _validate_properties_list(HasBusinessTerm, properties_list)

        query = _build_relationship_ingest_query(
            "HAS_BUSINESS_TERM",
            "Category",
            "BusinessTerm",
            "category_id",
            "business_term_id",
            overwrite_existing,
            properties_list
        )

        _, summary, _ = self.neo4j_driver.execute_query(
            query_=query,
            parameters_={"rows": [n.model_dump() for n in has_business_term_relationships]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__


    def load_has_value_relationships(
        self,
        has_value_relationships: list[HasValue],
        overwrite_existing: bool = False,
        properties_list: list[str] = []
    ) -> dict:
        if properties_list:
            _validate_properties_list(HasValue, properties_list)

        query = _build_relationship_ingest_query(
            "HAS_VALUE",
            "Column",
            "Value",
            "column_id",
            "value_id",
            overwrite_existing,
            properties_list
        )

        _, summary, _ = self.neo4j_driver.execute_query(
            query_=query,
            parameters_={"rows": [n.model_dump() for n in has_value_relationships]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__

    def load_query_nodes(
        self,
        query_nodes: list[Query],
        overwrite_existing: bool = False,
        properties_list: list[str] = ["content"]
    ) -> dict:
        _validate_properties_list(Query, properties_list)

        self._write_node_constraint(node_labels=["Query"])
        query = _build_node_ingest_query("Query", overwrite_existing, properties_list)

        _, summary, _ = self.neo4j_driver.execute_query(
            query_=query,
            parameters_={"rows": [n.model_dump() for n in query_nodes]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__

    def load_uses_table_relationships(
        self,
        uses_table_relationships: list[UsesTable],
        overwrite_existing: bool = False,
        properties_list: list[str] = []
    ) -> dict:
        if properties_list:
            _validate_properties_list(UsesTable, properties_list)

        query = _build_relationship_ingest_query(
            "USES_TABLE",
            "Query",
            "Table",
            "query_id",
            "table_id",
            overwrite_existing,
            properties_list
        )

        _, summary, _ = self.neo4j_driver.execute_query(
            query_=query,
            parameters_={"rows": [n.model_dump() for n in uses_table_relationships]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__

    def load_uses_column_relationships(
        self,
        uses_column_relationships: list[UsesColumn],
        overwrite_existing: bool = False,
        properties_list: list[str] = []
    ) -> dict:
        if properties_list:
            _validate_properties_list(UsesColumn, properties_list)

        query = _build_relationship_ingest_query(
            "USES_COLUMN",
            "Query",
            "Column",
            "query_id",
            "column_id",
            overwrite_existing,
            properties_list
        )

        _, summary, _ = self.neo4j_driver.execute_query(
            query_=query,
            parameters_={"rows": [n.model_dump() for n in uses_column_relationships]},
            routing_=RoutingControl.WRITE,
            database_=self.database_name,
        )
        return summary.counters.__dict__