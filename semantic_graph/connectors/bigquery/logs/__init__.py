"""BigQuery logs connector."""

from .connector import BigQueryLogsConnector
from .extract import BigQueryLogsExtractor

__all__ = ["BigQueryLogsConnector", "BigQueryLogsExtractor"]
