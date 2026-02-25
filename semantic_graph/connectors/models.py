"""global models for connectors."""

from typing import TypedDict, Optional
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
from ..data_model.expanded import Value, HasValue, Glossary, Category, BusinessTerm, HasCategory, HasBusinessTerm
from ..data_model.expanded import Query, UsesTable, UsesColumn

class NodesCache(TypedDict):
    """Cache dictionary used to store transformed metadata nodes."""
    # Core nodes
    database_nodes: Optional[list[Database]]
    schema_nodes: Optional[list[Schema]]
    table_nodes: Optional[list[Table]]
    column_nodes: Optional[list[Column]]
    # Value nodes
    value_nodes: Optional[list[Value]]

    # Glossary nodes
    glossary_nodes: Optional[list[Glossary]]
    category_nodes: Optional[list[Category]]
    business_term_nodes: Optional[list[BusinessTerm]]

    # Query nodes
    query_nodes: Optional[list[Query]]

class RelationshipsCache(TypedDict):
    """Cache dictionary used to store transformed metadata relationships."""
    # Core relationships
    has_schema_relationships: Optional[list[HasSchema]]
    has_table_relationships: Optional[list[HasTable]]
    has_column_relationships: Optional[list[HasColumn]]
    references_relationships: Optional[list[References]]

    # Value relationships
    has_value_relationships: Optional[list[HasValue]]

    # Glossary relationships
    has_category_relationships: Optional[list[HasCategory]]
    has_business_term_relationships: Optional[list[HasBusinessTerm]]

    # Query relationships
    uses_table_relationships: Optional[list[UsesTable]]
    uses_column_relationships: Optional[list[UsesColumn]]