from typing import TypedDict

import pandas as pd


class SchemaExtractorCache(TypedDict):
    """Cache dictionary for BigQuery schema metadata extraction."""

    database_info: pd.DataFrame | None
    schema_info: pd.DataFrame | None
    table_info: pd.DataFrame | None
    column_info: pd.DataFrame | None
    column_references_info: pd.DataFrame | None
    column_unique_values: pd.DataFrame | None
