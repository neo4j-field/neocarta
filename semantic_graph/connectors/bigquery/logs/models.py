from typing import TypedDict, Optional
import pandas as pd

class LogsExtractorCache(TypedDict):
    """Cache dictionary for BigQuery query logs extraction."""
    query_info: Optional[pd.DataFrame]
    table_info: Optional[pd.DataFrame]
    column_info: Optional[pd.DataFrame]
    column_references_info: Optional[pd.DataFrame]