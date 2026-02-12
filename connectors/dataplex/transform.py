"""Transform Dataplex metadata into graph nodes and relationships."""

import pandas as pd
from data_model.core import (
    Database,
    Schema,
    Table,
    Column,
    HasSchema,
    HasTable,
    HasColumn,
)
from data_model.expanded import (
    Glossary,
    Category,
    BusinessTerm,
    HasCategory,
    HasBusinessTerm,
)


def transform_to_database_nodes(database_metadata_info: pd.DataFrame) -> list[Database]:
    """
    Transform Dataplex database metadata into Database nodes.

    Parameters
    ----------
    database_metadata_info: pd.DataFrame
        A Pandas DataFrame containing Dataplex database metadata.
        Has columns `project_id`, `service`, and `platform`.

    Returns
    -------
    list[Database]
        The database nodes.
    """
    return [
        Database(
            id=row.project_id,
            name=row.project_id,
            description=None,
            service=row.service,
            platform=row.platform,
        )
        for _, row in database_metadata_info.iterrows()
    ]


def transform_to_schema_nodes(schema_metadata_info: pd.DataFrame) -> list[Schema]:
    """
    Transform Dataplex schema metadata into Schema nodes.

    Parameters
    ----------
    schema_metadata_info: pd.DataFrame
        A Pandas DataFrame containing Dataplex schema metadata.
        Has columns `project_id` and `dataset_id`.

    Returns
    -------
    list[Schema]
        The schema nodes.
    """
    return [
        Schema(
            id=row.project_id + "." + row.dataset_id,
            name=row.dataset_id,
            description=None, # no description in extraction step
        )
        for _, row in schema_metadata_info.iterrows()
    ]

def transform_to_table_nodes(table_metadata_info: pd.DataFrame) -> list[Table]:
    """
    Transform Dataplex table metadata into Table nodes.

    Parameters
    ----------
    table_metadata_info: pd.DataFrame
        A Pandas DataFrame containing Dataplex BigQuery metadata.
        Has columns `project_id`, `dataset_id`, `table_id`, `table_display_name`,
        and `table_description`.

    Returns
    -------
    list[Table]
        The table nodes.
    """
    return [
        Table(
            id=row.project_id + "." + row.dataset_id + "." + row.table_id,
            name=row.table_display_name,
            description=row.table_description or None,
        )
        for _, row in table_metadata_info.iterrows()
    ]


def transform_to_column_nodes(column_metadata_info: pd.DataFrame) -> list[Column]:
    """
    Transform Dataplex BigQuery metadata into column nodes.

    Parameters
    ----------
    bigquery_metadata_info: pd.DataFrame
        A Pandas DataFrame containing Dataplex BigQuery metadata.
        Has columns `project_id`, `dataset_id`, `table_id`, `column_name`,
        `column_data_type`, `column_mode`, and `column_description`.

    Returns
    -------
    list[Column]
        The column nodes.
    """
    return [
        Column(
            id=row.project_id
            + "."
            + row.dataset_id
            + "."
            + row.table_id
            + "."
            + row.column_name,
            name=row.column_name,
            description=row.column_description,
            type=row.column_data_type,
            nullable=row.column_mode == "NULLABLE",
            is_primary_key=False, # no primary key in extraction step
            is_foreign_key=False, # no foreign key in extraction step
        )
        for _, row in column_metadata_info.iterrows()
    ]


def transform_to_glossary_nodes(glossary_info: pd.DataFrame) -> list[Glossary]:
    """
    Transform Dataplex glossary information into glossary nodes.

    Parameters
    ----------
    glossary_info: pd.DataFrame
        A Pandas DataFrame containing Dataplex glossary information.
        Has columns `glossary_id` and `glossary_name`.

    Returns
    -------
    list[Glossary]
        The glossary nodes.
    """
    return [
        Glossary(
            id=row.glossary_id,
            name=row.glossary_name,
            description=None, # no description in extraction step
        )
        for _, row in glossary_info.iterrows()
    ]


def transform_to_category_nodes(category_info: pd.DataFrame) -> list[Category]:
    """
    Transform Dataplex glossary category information into Category nodes.

    Parameters
    ----------
    category_info: pd.DataFrame
        A Pandas DataFrame containing Dataplex glossary information.
        Has columns `glossary_id` and `category_id`.

    Returns
    -------
    list[Category]
        The category nodes.
    """
    return [
        Category(
            id=row.category_id,
            name=row.category_id,
            description=None, # no description in extraction step
        )
        for _, row in category_info.iterrows()
    ]


def transform_to_business_term_nodes(business_term_info: pd.DataFrame) -> list[BusinessTerm]:
    """
    Transform Dataplex glossary business term information into BusinessTerm nodes.

    Parameters
    ----------
    business_term_info: pd.DataFrame
        A Pandas DataFrame containing Dataplex glossary information.
        Has columns `term_id`, `term_name`, and `term_description`.

    Returns
    -------
    list[BusinessTerm]
        The business term nodes.
    """
    return [
        BusinessTerm(
            id=row.term_id,
            name=row.term_name,
            description=row.term_description,
        )
        for _, row in business_term_info.iterrows()
    ]


def transform_to_has_schema_relationships(
    schema_metadata_info: pd.DataFrame,
) -> list[HasSchema]:
    """
    Transform Dataplex schema metadata into has schema relationships.

    Parameters
    ----------
    schema_metadata_info: pd.DataFrame
        A Pandas DataFrame containing Dataplex schema metadata.
        Has columns `project_id` and `dataset_id`.

    Returns
    -------
    list[HasSchema]
        The has schema relationships.
    """
    return [
        HasSchema(
            database_id=row.project_id,
            schema_id=row.project_id + "." + row.dataset_id,
        )
        for _, row in schema_metadata_info.iterrows()
    ]


def transform_to_has_table_relationships(
    table_metadata_info: pd.DataFrame,
) -> list[HasTable]:
    """
    Transform Dataplex table metadata into has table relationships.

    Parameters
    ----------
    table_metadata_info: pd.DataFrame
        A Pandas DataFrame containing Dataplex table metadata.
        Has columns `project_id`, `dataset_id`, and `table_id`.

    Returns
    -------
    list[HasTable]
        The has table relationships.
    """
    return [
        HasTable(
            schema_id=row.project_id + "." + row.dataset_id,
            table_id=row.project_id + "." + row.dataset_id + "." + row.table_id,
        )
        for _, row in table_metadata_info.iterrows()
    ]


def transform_to_has_column_relationships(
    column_metadata_info: pd.DataFrame,
) -> list[HasColumn]:
    """
    Transform Dataplex column metadata into has column relationships.

    Parameters
    ----------
    column_metadata_info: pd.DataFrame
        A Pandas DataFrame containing Dataplex column metadata.
        Has columns `project_id`, `dataset_id`, `table_id`, and `column_name`.

    Returns
    -------
    list[HasColumn]
        The has column relationships.
    """
    return [
        HasColumn(
            table_id=row.project_id + "." + row.dataset_id + "." + row.table_id,
            column_id=row.project_id
            + "."
            + row.dataset_id
            + "."
            + row.table_id
            + "."
            + row.column_name,
        )
        for _, row in column_metadata_info.iterrows()
    ]


def transform_to_has_category_relationships(
    category_info: pd.DataFrame,
) -> list[HasCategory]:
    """
    Transform Dataplex category information into has category relationships.
    (:Glossary)-[:HAS_CATEGORY]->(:Category)

    Parameters
    ----------
    category_info: pd.DataFrame
        A Pandas DataFrame containing Dataplex glossary information.
        Has columns `glossary_id` and `category_id`.

    Returns
    -------
    list[HasCategory]
        The has category relationships.
    """ 
    return [
        HasCategory(
            glossary_id=row.glossary_id,
            category_id=row.category_id,
        )
        for _, row in category_info.iterrows()
    ]


def transform_to_has_business_term_relationships(
        business_term_info: pd.DataFrame,
) -> list[HasBusinessTerm]:
    """
    Transform Dataplex business term information into has business term relationships.
    (:Category)-[:HAS_BUSINESS_TERM]->(:BusinessTerm)

    Parameters
    ----------
    business_term_info: pd.DataFrame
        A Pandas DataFrame containing Dataplex business term information.
        Has columns `glossary_id` and `term_id`.

    Returns
    -------
    list[HasBusinessTerm]
        The has business term relationships.
    """
    return [
        HasBusinessTerm(
            category_id=row.category_id,
            business_term_id=row.term_id,
        )
        for _, row in business_term_info.iterrows()
    ]
