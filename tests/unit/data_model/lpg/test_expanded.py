"""Unit tests for LPG expanded data model components."""

import pytest
from pydantic import ValidationError

from neocarta.data_model.lpg import HasValue, Value


def test_value_string():
    """Test creating a Value with string type."""
    val = Value(id="v1", value="John Doe", type="STRING", count=10)
    assert val.id == "v1"
    assert val.value == "John Doe"
    assert val.type == "STRING"
    assert val.count == 10


def test_value_integer():
    """Test creating a Value with integer type."""
    val = Value(id="v2", value=42, type="INTEGER", count=5)
    assert val.value == 42
    assert val.type == "INTEGER"
    assert val.count == 5


def test_value_float():
    """Test creating a Value with float type."""
    val = Value(id="v3", value=3.14, type="FLOAT", count=3)
    assert val.value == 3.14
    assert val.type == "FLOAT"


def test_value_boolean():
    """Test creating a Value with boolean type."""
    val = Value(id="v4", value=True, type="BOOLEAN", count=7)
    assert val.value is True
    assert val.type == "BOOLEAN"


def test_value_list():
    """Test creating a Value with list type."""
    val = Value(id="v5", value=["tag1", "tag2"], type="LIST", count=2)
    assert val.value == ["tag1", "tag2"]
    assert val.type == "LIST"


def test_value_default_count():
    """Test that count defaults to 1."""
    val = Value(id="v1", value="test", type="STRING")
    assert val.count == 1


def test_value_with_embedding():
    """Test Value with embedding vector."""
    embedding = [0.1, 0.2, 0.3]
    val = Value(id="v1", value="test", type="STRING", embedding=embedding)
    assert val.embedding == embedding


def test_value_null():
    """Test creating a Value with None/null value."""
    val = Value(id="v6", value=None, type="NULL", count=15)
    assert val.value is None
    assert val.type == "NULL"
    assert val.count == 15


def test_has_value_valid():
    """Test creating a valid HasValue relationship."""
    rel = HasValue(property_id="p1", value_id="v1")
    assert rel.property_id == "p1"
    assert rel.value_id == "v1"


def test_value_missing_required_fields():
    """Test that missing required fields raise ValidationError."""
    with pytest.raises(ValidationError):
        Value(id="v1", value="test")


def test_has_value_missing_required_fields():
    """Test that missing required fields raise ValidationError."""
    with pytest.raises(ValidationError):
        HasValue(property_id="p1")


def test_value_optional_defaults():
    """Test that optional fields have correct defaults."""
    val = Value(id="v1", value="test", type="STRING")
    assert val.count == 1
    assert val.embedding is None


def test_value_all_optionals_specified():
    """Test Value with all optional fields specified."""
    embedding = [0.1, 0.2, 0.3]
    val = Value(id="v1", value="test", type="STRING", count=5, embedding=embedding)
    assert val.count == 5
    assert val.embedding == embedding
