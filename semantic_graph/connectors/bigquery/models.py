from typing import TypedDict, Optional
import pandas as pd
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
from ...data_model.expanded import Value, HasValue

class InfoTablesCache(TypedDict):
    "Cache dictionary used to store extracted information tables from BigQuery."
    database_info: Optional[pd.DataFrame]
    schema_info: Optional[pd.DataFrame]
    table_info: Optional[pd.DataFrame]
    column_info: Optional[pd.DataFrame]
    column_references_info: Optional[pd.DataFrame]
    column_unique_values: Optional[pd.DataFrame]

class MetadataNodesCache(TypedDict):
    """Cache dictionary used to store transformed metadata nodes."""
    database_nodes: Optional[list[Database]]
    schema_nodes: Optional[list[Schema]]
    table_nodes: Optional[list[Table]]
    column_nodes: Optional[list[Column]]
    value_nodes: Optional[list[Value]]

class MetadataRelationshipsCache(TypedDict):
    """Cache dictionary used to store transformed metadata relationships."""
    has_schema_relationships: Optional[list[HasSchema]]
    has_table_relationships: Optional[list[HasTable]]
    has_column_relationships: Optional[list[HasColumn]]
    references_relationships: Optional[list[References]]
    has_value_relationships: Optional[list[HasValue]]