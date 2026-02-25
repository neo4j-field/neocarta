"""Common ingest functions for Neo4j."""

from pydantic import BaseModel
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

def _validate_properties_list(model: BaseModel, properties_list: list[str]) -> None:
    """
    Validate the properties list for a given Pydantic model.
    Will raise an error if any properties are not found in the model fields.

    Parameters
    ----------
    model: BaseModel
        The Pydantic model to validate the properties list for.
    properties_list: list[str]
        The list of properties to validate.

    Raises
    ------
    ValueError
        If any properties are not found in the model fields.
    """

    invalid_props = set(properties_list) - set(model.model_fields)
    if invalid_props:
        raise ValueError(f"Properties list contains invalid properties for model {model.__class__.__name__}: {invalid_props}")

def _build_node_ingest_query(node_label: str, overwrite_existing: bool, properties_list: list[str]) -> str:
    """
    Build a node ingest query for a given node label, overwrite existing flag, and properties list.
    Will return a MERGE query that sets properties according to the configuration.

    Parameters
    ----------
    node_label: str
        The label of the node to ingest.
    overwrite_existing: bool
        Whether to overwrite existing nodes on MATCH.
    properties_list: list[str]
        The list of properties to set on the node.

    Returns
    -------
    str
        The MERGE query to ingest the nodes.
    """
    query = f"""
UNWIND $rows as row
MERGE (n:{node_label} {{id: row.id}})
"""

    # Only add ON CREATE and SET if there are properties to set
    if len(properties_list) == 0:
        return query.rstrip()

    # Determine indentation based on overwrite setting
    if not overwrite_existing:
        query += "ON CREATE\n    SET "
        indent = " " * 8  # 8 spaces for continuation lines
    else:
        query += "SET "
        indent = " " * 4  # 4 spaces for continuation lines

    for idx, prop in enumerate(properties_list):
        query += f"n.{prop} = row.{prop}"
        if idx < len(properties_list) - 1:
            query += ",\n" + indent

    return query


def _build_relationship_ingest_query(relationship_type: str, 
source_node_label: str, 
target_node_label: str, 
source_id_column_name: str,
target_id_column_name: str,
overwrite_existing: bool, properties_list: list[str]) -> str:
    """
    Build a relationship ingest query for a given relationship type, source node label, target node label, source id column name, target id column name, overwrite existing flag, and properties list.
    """
    query = f"""
UNWIND $rows as row
MATCH (n1:{source_node_label} {{id: row.{source_id_column_name}}})
MATCH (n2:{target_node_label} {{id: row.{target_id_column_name}}})
MERGE (n1)-[r:{relationship_type}]->(n2)
"""
    # Only add ON CREATE and SET if there are properties to set
    if len(properties_list) == 0:
        return query.rstrip()

    # Determine indentation based on overwrite setting
    if not overwrite_existing:
        query += "ON CREATE\n    SET "
        indent = " " * 8  # 8 spaces for continuation lines
    else:
        query += "SET "
        indent = " " * 4  # 4 spaces for continuation lines

    for idx, prop in enumerate(properties_list):
        query += f"r.{prop} = row.{prop}"
        if idx < len(properties_list) - 1:
            query += ",\n" + indent

    return query

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
        self, database_nodes: list[Database],
        overwrite_existing: bool = False,
        properties_list: list[str] = ["name", "description", "service", "platform"]
    ) -> dict:

        _validate_properties_list(Database, properties_list)

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