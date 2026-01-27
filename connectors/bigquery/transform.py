from data_model.core import (
    Database,
    Table,
    Column,
    ContainsTable,
    HasColumn,
    References,
)
import pandas as pd
from data_model.expanded import Value, HasValue


def transform_to_database_nodes(database_info: pd.DataFrame) -> list[Database]:
    """
    Transform BigQuery database information into database nodes.

    Parameters
    ----------
    database_info: pd.DataFrame
        A Pandas DataFrame containing the BigQuery database information.
        Has columns `table_catalog`, `table_schema`, and `description`.

    Returns
    -------
    list[Database]
        The database nodes.
    """
    return [
        Database(
            id=row.table_catalog + "." + row.table_schema,
            name=row.table_catalog + "." + row.table_schema,
            description=row.description,
        )
        for _, row in database_info.iterrows()
    ]


def transform_to_table_nodes(table_info: pd.DataFrame) -> list[Table]:
    """
    Transform BigQuery table information into table nodes.

    Parameters
    ----------
    table_info: pd.DataFrame
        A Pandas DataFrame containing the BigQuery table information.
        Has columns `table_catalog`, `table_schema`, `table_name`, and `description`.

    Returns
    -------
    list[Table]
        The table nodes.
    """
    return [
        Table(
            id=row.table_catalog + "." + row.table_schema + "." + row.table_name,
            name=row.table_name,
            description=row.description,
        )
        for _, row in table_info.iterrows()
    ]


def transform_to_column_nodes(column_info: pd.DataFrame) -> list[Column]:
    """
    Transform BigQuery column information into column nodes.

    Parameters
    ----------
    column_info: pd.DataFrame
        A Pandas DataFrame containing the BigQuery column information.
        Has columns `table_catalog`, `table_schema`, `table_name`, `column_name`, `is_nullable`, `data_type`, `description`, and `constraint_name`.

    Returns
    -------
    list[Column]
        The column nodes.
    """
    return [
        Column(
            id=row.table_catalog
            + "."
            + row.table_schema
            + "."
            + row.table_name
            + "."
            + row.column_name,
            name=row.column_name,
            description=row.description,
            type=row.data_type,
            nullable=row.is_nullable,
            is_primary_key=row.is_primary_key,
            is_foreign_key=row.is_foreign_key,
        )
        for _, row in column_info.iterrows()
    ]


def transform_to_value_nodes(value_info: pd.DataFrame) -> list[Value]:

    """
    Transform BigQuery value information into value nodes.

    Parameters
    ----------
    value_info: pd.DataFrame
        A Pandas DataFrame containing the BigQuery value information.

    Returns
    -------
    list[Value]
        The value nodes.
    """
    return [
        Value(
            id=row.value_id,
            value=row.unique_value,
        )
        for _, row in value_info.iterrows()
    ]

def transform_to_contains_table_relationships(
    table_info: pd.DataFrame,
) -> list[ContainsTable]:
    """
    Transform BigQuery table information into contains table relationships.

    Parameters
    ----------
    table_info: pd.DataFrame
        A Pandas DataFrame containing the BigQuery table information.
        Has columns `table_catalog`, `table_schema`, and `table_name`.

    Returns
    -------
    list[ContainsTable]
        The contains table relationships.
    """

    return [
        ContainsTable(
            database_id=row.table_catalog + "." + row.table_schema,
            table_id=row.table_catalog + "." + row.table_schema + "." + row.table_name,
        )
        for _, row in table_info.iterrows()
    ]


def transform_to_has_column_relationships(column_info: pd.DataFrame) -> list[HasColumn]:
    """
    Transform BigQuery column information into has column relationships.

    Parameters
    ----------
    column_info: pd.DataFrame
        A Pandas DataFrame containing the BigQuery column information.
        Has columns `table_catalog`, `table_schema`, `table_name`, and `column_name`.

    Returns
    -------
    list[HasColumn]
        The has column relationships.
    """
    return [
        HasColumn(
            table_id=row.table_catalog + "." + row.table_schema + "." + row.table_name,
            column_id=row.table_catalog
            + "."
            + row.table_schema
            + "."
            + row.table_name
            + "."
            + row.column_name,
        )
        for _, row in column_info.iterrows()
    ]


def transform_to_references_relationships(
    column_references_info: pd.DataFrame,
) -> list[References]:
    """
    Transform BigQuery column references information into references relationships.

    Parameters
    ----------
    column_references_info: pd.DataFrame
        A Pandas DataFrame containing the BigQuery column references information.
        Has columns `constraint_catalog`, `constraint_schema`, `table_name`, `column_name`, `referenced_table`, and `referenced_column`.

    Returns
    -------
    list[References]
        The references relationships.
    """
    return [
        References(
            source_column_id=row.constraint_catalog
            + "."
            + row.constraint_schema
            + "."
            + row.table_name
            + "."
            + row.column_name,
            target_column_id=row.constraint_catalog
            + "."
            + row.constraint_schema
            + "."
            + row.referenced_table
            + "."
            + row.referenced_column,
        )
        for _, row in column_references_info[
            column_references_info["constraint_type"] == "FOREIGN KEY"
        ].iterrows()
    ]

def transform_to_has_value_relationships(value_info: pd.DataFrame) -> list[HasValue]:
    """
    Transform BigQuery value information into has value relationships.

    Parameters
    ----------
    value_info: pd.DataFrame
        A Pandas DataFrame containing the BigQuery value information.
        Must have columns `column_id` and `value_id`.
    """
    return [
        HasValue(
            column_id=row.column_id,
            value_id=row.value_id,
        )
        for _, row in value_info.iterrows()
    ]