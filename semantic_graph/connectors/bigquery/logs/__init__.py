"""BigQuery logs connector."""

from .extract import BigQueryLogsExtractor
from .connector import BigQueryLogsConnector

__all__ = ["BigQueryLogsExtractor", "BigQueryLogsConnector"]
