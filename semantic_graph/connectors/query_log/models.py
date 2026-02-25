from typing import TypedDict, Optional
import pandas as pd

class QueryLogExtractorCache(TypedDict):
    """Cache dictionary used to store extracted query log information."""
    database_info: Optional[pd.DataFrame]
    schema_info: Optional[pd.DataFrame]
    table_info: Optional[pd.DataFrame]
    column_info: Optional[pd.DataFrame]
    column_references_info: Optional[pd.DataFrame]
    query_info: Optional[pd.DataFrame]