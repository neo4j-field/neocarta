"""Models for CSV connector."""

from typing import TypedDict

import pandas as pd


class CSVExtractorCache(TypedDict):
    """Cache dictionary for CSV metadata extraction."""

    # Core entity DataFrames
    database_info: pd.DataFrame | None
    schema_info: pd.DataFrame | None
    table_info: pd.DataFrame | None
    column_info: pd.DataFrame | None

    # Relationship DataFrames
    column_references_info: pd.DataFrame | None

    # Extended entity DataFrames
    value_info: pd.DataFrame | None
    query_info: pd.DataFrame | None
    query_table_info: pd.DataFrame | None
    query_column_info: pd.DataFrame | None

    # Glossary entity DataFrames
    glossary_info: pd.DataFrame | None
    category_info: pd.DataFrame | None
    business_term_info: pd.DataFrame | None
