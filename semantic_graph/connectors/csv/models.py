"""Models for CSV connector."""

from typing import TypedDict, Optional
import pandas as pd


class CSVExtractorCache(TypedDict):
    """Cache dictionary for CSV metadata extraction."""
    # Core entity DataFrames
    database_info: Optional[pd.DataFrame]
    schema_info: Optional[pd.DataFrame]
    table_info: Optional[pd.DataFrame]
    column_info: Optional[pd.DataFrame]

    # Relationship DataFrames
    column_references_info: Optional[pd.DataFrame]

    # Extended entity DataFrames
    value_info: Optional[pd.DataFrame]
    query_info: Optional[pd.DataFrame]
    query_table_info: Optional[pd.DataFrame]
    query_column_info: Optional[pd.DataFrame]

    # Glossary entity DataFrames
    glossary_info: Optional[pd.DataFrame]
    category_info: Optional[pd.DataFrame]
    business_term_info: Optional[pd.DataFrame]
