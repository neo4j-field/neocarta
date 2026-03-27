from semantic_graph.connectors.utils.generate_id import generate_value_id

def test_generate_value_id_string():
    """Test generating a value ID for a string value."""
    value_id = generate_value_id("my-project", "sales", "orders", "status", "completed")
    assert value_id

def test_generate_value_id_int():
    """Test generating a value ID for an int value."""
    value_id = generate_value_id("my-project", "sales", "orders", "status", 1)
    assert value_id

def test_generate_value_id_float():
    """Test generating a value ID for a float value."""
    value_id = generate_value_id("my-project", "sales", "orders", "status", 1.0)
    assert value_id
