from typing import TypedDict, Optional
import pandas as pd

class InfoTablesCache(TypedDict):
    "Cache dictionary used to store extracted information tables from BigQuery."
    database_info: Optional[pd.DataFrame]
    schema_info: Optional[pd.DataFrame]
    table_info: Optional[pd.DataFrame]
    column_info: Optional[pd.DataFrame]
    column_references_info: Optional[pd.DataFrame]
    column_unique_values: Optional[pd.DataFrame]