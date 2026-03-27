"""Utility functions for generating hierarchical IDs for graph entities."""

import hashlib


def generate_database_id(database: str) -> str:
    """
    Generate a database ID.

    Parameters
    ----------
    database : str
        The database identifier (name or ID)

    Returns
    -------
    str
        The database ID

    Examples
    --------
    >>> generate_database_id("my-project")
    'my-project'
    """
    return database


def generate_schema_id(database: str, schema: str) -> str:
    """
    Generate a schema ID from database and schema identifiers.

    Parameters
    ----------
    database : str
        The database identifier (name or ID)
    schema : str
        The schema identifier (name or ID)

    Returns
    -------
    str
        The schema ID in format: {database}.{schema}

    Examples
    --------
    >>> generate_schema_id("my-project", "sales")
    'my-project.sales'
    """
    return f"{database}.{schema}"


def generate_table_id(database: str, schema: str, table: str) -> str:
    """
    Generate a table ID from database, schema, and table identifiers.

    Parameters
    ----------
    database : str
        The database identifier (name or ID)
    schema : str
        The schema identifier (name or ID)
    table : str
        The table identifier (name or ID)

    Returns
    -------
    str
        The table ID in format: {database}.{schema}.{table}

    Examples
    --------
    >>> generate_table_id("my-project", "sales", "orders")
    'my-project.sales.orders'
    """
    return f"{database}.{schema}.{table}"


def generate_column_id(database: str, schema: str, table: str, column: str) -> str:
    """
    Generate a column ID from database, schema, table, and column identifiers.

    Parameters
    ----------
    database : str
        The database identifier (name or ID)
    schema : str
        The schema identifier (name or ID)
    table : str
        The table identifier (name or ID)
    column : str
        The column identifier (name or ID)

    Returns
    -------
    str
        The column ID in format: {database}.{schema}.{table}.{column}

    Examples
    --------
    >>> generate_column_id("my-project", "sales", "orders", "order_id")
    'my-project.sales.orders.order_id'
    """
    return f"{database}.{schema}.{table}.{column}"


def generate_value_id(database: str, schema: str, table: str, column: str, value: str) -> str:
    """
    Generate a value ID from database, schema, table, column, and value.

    Creates a hierarchical ID with a hash suffix based on the value.

    Parameters
    ----------
    database : str
        The database identifier (name or ID)
    schema : str
        The schema identifier (name or ID)
    table : str
        The table identifier (name or ID)
    column : str
        The column identifier (name or ID)
    value : str
        The value as a string

    Returns
    -------
    str
        The value ID in format: {database}.{schema}.{table}.{column}.{hashed-value}

    Examples
    --------
    >>> generate_value_id("my-project", "sales", "orders", "status", "completed")
    'my-project.sales.orders.status.9cdfb439c7876e703e307864c9167a15'
    """
    # Generate a short hash of the value (first 32 characters of MD5)
    value_hash = hashlib.md5(value.encode()).hexdigest()[:32]
    return f"{database}.{schema}.{table}.{column}.{value_hash}"

def create_query_id(query: str) -> str:
    """
    Create a query ID from a query string.
    """
    return hashlib.sha256(query.encode()).hexdigest()