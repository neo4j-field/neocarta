"""Unit tests for Dataplex connector import warnings."""

import importlib
import warnings

import neocarta.connectors.dataplex as dataplex_module


def test_dataplex_import_triggers_no_warning():
    """Importing the Dataplex connector should not emit any warnings."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        importlib.reload(dataplex_module)
