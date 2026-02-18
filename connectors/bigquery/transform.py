from data_model.core import (
    Database,
    Schema,
    Table,
    Column,
    HasSchema,
    HasTable,
    HasColumn,
    References,
)
import pandas as pd
from data_model.expanded import Value, HasValue
from connectors.bigquery.models import MetadataNodesCache, MetadataRelationshipsCache

class BigQueryTransformer:
    """
    Transformer class for BigQuery. 
    Transforms metadata from BigQuery Information Tables into data model nodes and relationships.
    """

    def __init__(self):
        """
        Initialize the BigQuery transformer.
        """
        self.metadata_nodes_cache: MetadataNodesCache = MetadataNodesCache()
        self.metadata_relationships_cache: MetadataRelationshipsCache = MetadataRelationshipsCache()

    def transform_to_database_nodes(self, database_info: pd.DataFrame, cache: bool = False) -> list[Database]:
        """
        Transform BigQuery database (project) information into database nodes.

        Parameters
        ----------
        database_info: pd.DataFrame
            A Pandas DataFrame containing the BigQuery database information.
            Has column `project_id`.
        cache: bool = False
            Whether to cache the transform. If True, will cache the database nodes in the instance.

        Returns
        -------
        list[Database]
            The database nodes.
        """
        database_nodes = [
            Database(
                id=row.project_id,
                name=row.project_id,
                description=None,
            )
            for _, row in database_info.iterrows()
        ]

        if cache:
            self.metadata_nodes_cache["database_nodes"] = database_nodes

        return database_nodes


    def transform_to_schema_nodes(self, schema_info: pd.DataFrame, cache: bool = False) -> list[Schema]:
        """
        Transform BigQuery schema (dataset) information into schema nodes.

        Parameters
        ----------
        schema_info: pd.DataFrame
            A Pandas DataFrame containing the BigQuery schema information.
            Has columns `project_id`, `dataset_id`, and `description`.

        Returns
        -------
        list[Schema]
            The schema nodes.
        """
        schema_nodes = [
            Schema(
                id=row.project_id + "." + row.dataset_id,
                name=row.dataset_id,
                description=row.description,
            )
            for _, row in schema_info.iterrows()
        ]

        if cache:
            self.metadata_nodes_cache["schema_nodes"] = schema_nodes

        return schema_nodes


    def transform_to_table_nodes(self, table_info: pd.DataFrame, cache: bool = False) -> list[Table]:
        """
        Transform BigQuery table information into table nodes.

        Parameters
        ----------
        table_info: pd.DataFrame
            A Pandas DataFrame containing the BigQuery table information.
            Has columns `table_catalog`, `table_schema`, `table_name`, and `description`.
        cache: bool = False
            Whether to cache the transform. If True, will cache the table nodes in the instance.

        Returns
        -------
        list[Table]
            The table nodes.
        """
        table_nodes = [
            Table(
                id=row.table_catalog + "." + row.table_schema + "." + row.table_name,
                name=row.table_name,
                description=row.description,
            )
            for _, row in table_info.iterrows()
        ]

        if cache:
            self.metadata_nodes_cache["table_nodes"] = table_nodes

        return table_nodes


    def transform_to_column_nodes(self, column_info: pd.DataFrame, cache: bool = False) -> list[Column]:
        """
        Transform BigQuery column information into column nodes.

        Parameters
        ----------
        column_info: pd.DataFrame
            A Pandas DataFrame containing the BigQuery column information.
            Has columns `table_catalog`, `table_schema`, `table_name`, `column_name`, `is_nullable`, `data_type`, `description`, and `constraint_name`.
        cache: bool = False
            Whether to cache the transform. If True, will cache the column nodes in the instance.

        Returns
        -------
        list[Column]
            The column nodes.
        """
        column_nodes = [
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

        if cache:
            self.metadata_nodes_cache["column_nodes"] = column_nodes

        return column_nodes


    def transform_to_value_nodes(self, value_info: pd.DataFrame, cache: bool = False) -> list[Value]:
        """
        Transform BigQuery value information into value nodes.

        Parameters
        ----------
        value_info: pd.DataFrame
            A Pandas DataFrame containing the BigQuery value information.
        cache: bool = False
            Whether to cache the transform. If True, will cache the value nodes in the instance.

        Returns
        -------
        list[Value]
            The value nodes.
        """
        value_nodes = [
            Value(
                id=row.value_id,
                value=row.unique_value,
            )
            for _, row in value_info.iterrows()
        ]

        if cache:
            self.metadata_nodes_cache["value_nodes"] = value_nodes

        return value_nodes


    def transform_to_has_schema_relationships(
        self, schema_info: pd.DataFrame,
        cache: bool = False
    ) -> list[HasSchema]:
        """
        Transform BigQuery schema information into contains schema relationships.

        Parameters
        ----------
        schema_info: pd.DataFrame
            A Pandas DataFrame containing the BigQuery schema information.
            Has columns `project_id` and `dataset_id`.

        Returns
        -------
        list[HasSchema]
            The contains schema relationships.
        """
        has_schema_relationships = [
            HasSchema(
                database_id=row.project_id,
                schema_id=row.project_id + "." + row.dataset_id,
            )
            for _, row in schema_info.iterrows()
        ]

        if cache:
            self.metadata_relationships_cache["has_schema_relationships"] = has_schema_relationships

        return has_schema_relationships


    def transform_to_has_table_relationships(
        self, table_info: pd.DataFrame,
        cache: bool = False
    ) -> list[HasTable]:
        """
        Transform BigQuery table information into contains table relationships.

        Parameters
        ----------
        table_info: pd.DataFrame
            A Pandas DataFrame containing the BigQuery table information.
            Has columns `table_catalog`, `table_schema`, and `table_name`.
        cache: bool = False
            Whether to cache the transform. If True, will cache the has table relationships in the instance.

        Returns
        -------
        list[HasTable]
            The contains table relationships.
        """

        has_table_relationships = [
            HasTable(
                schema_id=row.table_catalog + "." + row.table_schema,
                table_id=row.table_catalog + "." + row.table_schema + "." + row.table_name,
            )
            for _, row in table_info.iterrows()
        ]

        if cache:
            self.metadata_relationships_cache["has_table_relationships"] = has_table_relationships

        return has_table_relationships


    def transform_to_has_column_relationships(self, column_info: pd.DataFrame, cache: bool = False) -> list[HasColumn]:
        """
        Transform BigQuery column information into has column relationships.

        Parameters
        ----------
        column_info: pd.DataFrame
            A Pandas DataFrame containing the BigQuery column information.
            Has columns `table_catalog`, `table_schema`, `table_name`, and `column_name`.
        cache: bool = False
            Whether to cache the transform. If True, will cache the has column relationships in the instance.
            
        Returns
        -------
        list[HasColumn]
            The has column relationships.
        """
        has_column_relationships = [
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

        if cache:
            self.metadata_relationships_cache["has_column_relationships"] = has_column_relationships

        return has_column_relationships


    def transform_to_references_relationships(
        self, column_references_info: pd.DataFrame,
        cache: bool = False
    ) -> list[References]:
        """
        Transform BigQuery column references information into references relationships.

        Parameters
        ----------
        column_references_info: pd.DataFrame
            A Pandas DataFrame containing the BigQuery column references information.
            Has columns `constraint_catalog`, `constraint_schema`, `table_name`, `column_name`, `referenced_table`, and `referenced_column`.
        cache: bool = False
            Whether to cache the transform. If True, will cache the references relationships in the instance.

        Returns
        -------
        list[References]
            The references relationships.
        """
        references_relationships = [
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

        if cache:
            self.metadata_relationships_cache["references_relationships"] = references_relationships

        return references_relationships


    def transform_to_has_value_relationships(self, value_info: pd.DataFrame, cache: bool = False) -> list[HasValue]:
        """
        Transform BigQuery value information into has value relationships.

        Parameters
        ----------
        value_info: pd.DataFrame
            A Pandas DataFrame containing the BigQuery value information.
            Must have columns `column_id` and `value_id`.
        cache: bool = False
            Whether to cache the transform. If True, will cache the has value relationships in the instance.
            
        Returns
        -------
        list[HasValue]
            The has value relationships.
        """
        has_value_relationships = [
            HasValue(
                column_id=row.column_id,
                value_id=row.value_id,
            )
            for _, row in value_info.iterrows()
        ]

        if cache:
            self.metadata_relationships_cache["has_value_relationships"] = has_value_relationships

        return has_value_relationships
