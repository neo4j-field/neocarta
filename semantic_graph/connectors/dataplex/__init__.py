"""Dataplex connector."""

import warnings

from .connector import DataplexConnector
from .extract import DataplexExtractor
from .transform import DataplexTransformer

warnings.warn(
    "The Dataplex connector is an incomplete feature. Current limitations of the Dataplex API prevent relationships between business terms and their tagged entities.",
    stacklevel=2,
)

__all__ = ["DataplexConnector", "DataplexExtractor", "DataplexTransformer"]
