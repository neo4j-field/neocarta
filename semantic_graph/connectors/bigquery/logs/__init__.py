"""BigQuery logs connector."""

from .extract import BigQueryLogsExtractor
from .workflow import BigQueryLogsWorkflow

__all__ = ["BigQueryLogsExtractor", "BigQueryLogsWorkflow"]
