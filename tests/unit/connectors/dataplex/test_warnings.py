"""Unit tests for Dataplex connector import warnings."""

import importlib

import pytest

import semantic_graph.connectors.dataplex as dataplex_module


def test_dataplex_import_triggers_warning():
    """Importing the Dataplex connector should emit an in-progress warning."""
    with pytest.warns(UserWarning, match="Dataplex connector"):
        importlib.reload(dataplex_module)
