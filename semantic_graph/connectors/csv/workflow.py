"""CSV Connector Workflow for loading metadata from CSV files into Neo4j."""

import pandas as pd
from pathlib import Path
from typing import Optional
from neo4j import Driver

from ...data_model.core import (
    Database,
    Schema,
    Table,
    Column,
    HasSchema,
    HasTable,
    HasColumn,
    References,
)
from ...data_model.expanded import (
    Value,
    HasValue,
    Glossary,
    Category,
    BusinessTerm,
    HasCategory,
    HasBusinessTerm,
    Query,
    UsesTable,
    UsesColumn,
)
from ...ingest.rdbms import Neo4jRDBMSLoader
from ..utils.generate_id import (
    generate_database_id,
    generate_schema_id,
    generate_table_id,
    generate_column_id,
    generate_value_id,
)


class CSVWorkflow:
    """
    Workflow for loading metadata from CSV files into Neo4j.

    Reads CSV files from a directory, validates them, generates IDs,
    and loads them into Neo4j.
    """

    # Default CSV file names
    DEFAULT_FILE_MAP = {
        "database": "database_info.csv",
        "schema": "schema_info.csv",
        "table": "table_info.csv",
        "column": "column_info.csv",
        "value": "value_info.csv",
        "query": "query_info.csv",
        "query_table": "query_table_info.csv",
        "query_column": "query_column_info.csv",
        "glossary": "glossary_info.csv",
        "category": "category_info.csv",
        "business_term": "business_term_info.csv",
        "column_references": "column_references_info.csv",
    }

    def __init__(
        self,
        csv_directory: str,
        neo4j_driver: Driver,
        database_name: str = "neo4j",
        csv_file_map: Optional[dict[str, str]] = None
    ):
        """
        Initialize the CSV workflow.

        Parameters
        ----------
        csv_directory : str
            Path to directory containing CSV files
        neo4j_driver : Driver
            Neo4j driver instance
        database_name : str, optional
            Neo4j database name, by default "neo4j"
        csv_file_map : dict[str, str], optional
            Custom mapping of entity types to CSV filenames.
            Merges with DEFAULT_FILE_MAP, allowing partial overrides.
        """
        self.csv_directory = Path(csv_directory)
        self.neo4j_driver = neo4j_driver
        self.database_name = database_name
        self.loader = Neo4jRDBMSLoader(neo4j_driver, database_name)

        # Merge custom file map with defaults
        self.csv_file_map = self.DEFAULT_FILE_MAP.copy()
        if csv_file_map:
            self.csv_file_map.update(csv_file_map)

    def _read_csv_if_exists(self, filename: str) -> Optional[pd.DataFrame]:
        """Read a CSV file if it exists."""
        filepath = self.csv_directory / filename
        if not filepath.exists():
            return None
        return pd.read_csv(filepath)

    def _get_properties_list(
        self,
        df: pd.DataFrame,
        exclude_columns: list[str],
        column_mapping: dict[str, str] = None,
        always_include: list[str] = None
    ) -> list[str]:
        """
        Get list of properties to load based on CSV columns.

        Parameters
        ----------
        df : pd.DataFrame
            The dataframe to extract columns from
        exclude_columns : list[str]
            Columns to exclude (typically ID fields used for node identification)
        column_mapping : dict[str, str], optional
            Mapping from CSV column names to model property names
        always_include : list[str], optional
            Properties to always include (e.g., 'name' which is always set)

        Returns
        -------
        list[str]
            List of property names to load (using model property names)
        """
        # Always exclude 'id' column plus any additional columns specified
        all_excluded = ["id"] + exclude_columns
        csv_columns = [col for col in df.columns if col not in all_excluded]

        # Map CSV column names to model property names
        if column_mapping:
            properties = [column_mapping.get(col, col) for col in csv_columns]
        else:
            properties = csv_columns

        # Add properties that should always be included
        if always_include:
            for prop in always_include:
                if prop not in properties:
                    properties.append(prop)

        return properties

    def load_database_nodes(self, csv_filename: Optional[str] = None) -> None:
        """
        Load database nodes from CSV file.

        Parameters
        ----------
        csv_filename : str, optional
            CSV filename to load from. Defaults to value in csv_file_map['database'].
        """
        filename = csv_filename or self.csv_file_map["database"]
        df = self._read_csv_if_exists(filename)
        if df is None or df.empty:
            print(f"No {filename} found or file is empty")
            return

        nodes = [
            Database(
                id=generate_database_id(row.database_id),
                name=row.get("name", row.database_id),
                platform=row.get("platform"),
                service=row.get("service"),
                description=row.get("description"),
            )
            for _, row in df.iterrows()
        ]

        properties_list = self._get_properties_list(
            df,
            exclude_columns=["database_id"],
            always_include=["name"]
        )

        print(f"Loading {len(nodes)} database nodes...")
        print(self.loader.load_database_nodes(nodes, properties_list=properties_list))

    def load_schema_nodes(self, csv_filename: Optional[str] = None) -> None:
        """
        Load schema nodes from CSV file.

        Parameters
        ----------
        csv_filename : str, optional
            CSV filename to load from. Defaults to value in csv_file_map['schema'].
        """
        filename = csv_filename or self.csv_file_map["schema"]
        df = self._read_csv_if_exists(filename)
        if df is None or df.empty:
            print(f"No {filename} found or file is empty")
            return

        nodes = [
            Schema(
                id=generate_schema_id(row.database_id, row.schema_id),
                name=row.get("name", row.schema_id),
                description=row.get("description"),
            )
            for _, row in df.iterrows()
        ]

        properties_list = self._get_properties_list(
            df,
            exclude_columns=["database_id", "schema_id"],
            always_include=["name"]
        )

        print(f"Loading {len(nodes)} schema nodes...")
        print(self.loader.load_schema_nodes(nodes, properties_list=properties_list))

    def load_has_schema_relationships(self, csv_filename: Optional[str] = None) -> None:
        """
        Load HAS_SCHEMA relationships from CSV file.

        Parameters
        ----------
        csv_filename : str, optional
            CSV filename to load from. Defaults to value in csv_file_map['schema'].
        """
        filename = csv_filename or self.csv_file_map["schema"]
        df = self._read_csv_if_exists(filename)
        if df is None or df.empty:
            print(f"No {filename} found or file is empty")
            return

        relationships = [
            HasSchema(
                database_id=generate_database_id(row.database_id),
                schema_id=generate_schema_id(row.database_id, row.schema_id),
            )
            for _, row in df.iterrows()
        ]

        print(f"Loading {len(relationships)} HAS_SCHEMA relationships...")
        print(self.loader.load_has_schema_relationships(relationships))

    def load_table_nodes(self, csv_filename: Optional[str] = None) -> None:
        """
        Load table nodes from CSV file.

        Parameters
        ----------
        csv_filename : str, optional
            CSV filename to load from. Defaults to value in csv_file_map['table'].
        """
        filename = csv_filename or self.csv_file_map["table"]
        df = self._read_csv_if_exists(filename)
        if df is None or df.empty:
            print(f"No {filename} found or file is empty")
            return

        nodes = [
            Table(
                id=generate_table_id(row.database_id, row.schema_id, row.table_name),
                name=row.get("name", row.table_name),
                description=row.get("description"),
            )
            for _, row in df.iterrows()
        ]

        properties_list = self._get_properties_list(
            df,
            exclude_columns=["database_id", "schema_id", "table_name"],
            always_include=["name"]
        )

        print(f"Loading {len(nodes)} table nodes...")
        print(self.loader.load_table_nodes(nodes, properties_list=properties_list))

    def load_has_table_relationships(self, csv_filename: Optional[str] = None) -> None:
        """
        Load HAS_TABLE relationships from CSV file.

        Parameters
        ----------
        csv_filename : str, optional
            CSV filename to load from. Defaults to value in csv_file_map['table'].
        """
        filename = csv_filename or self.csv_file_map["table"]
        df = self._read_csv_if_exists(filename)
        if df is None or df.empty:
            print(f"No {filename} found or file is empty")
            return

        relationships = [
            HasTable(
                schema_id=generate_schema_id(row.database_id, row.schema_id),
                table_id=generate_table_id(row.database_id, row.schema_id, row.table_name),
            )
            for _, row in df.iterrows()
        ]

        print(f"Loading {len(relationships)} HAS_TABLE relationships...")
        print(self.loader.load_has_table_relationships(relationships))

    def load_column_nodes(self, csv_filename: Optional[str] = None) -> None:
        """
        Load column nodes from CSV file.

        Parameters
        ----------
        csv_filename : str, optional
            CSV filename to load from. Defaults to value in csv_file_map['column'].
        """
        filename = csv_filename or self.csv_file_map["column"]
        df = self._read_csv_if_exists(filename)
        if df is None or df.empty:
            print(f"No {filename} found or file is empty")
            return

        nodes = [
            Column(
                id=generate_column_id(
                    row.database_id, row.schema_id, row.table_name, row.column_name
                ),
                name=row.get("name", row.column_name),
                description=row.get("description"),
                type=row.get("data_type"),
                nullable=row.get("is_nullable", True),
                is_primary_key=row.get("is_primary_key", False),
                is_foreign_key=row.get("is_foreign_key", False),
            )
            for _, row in df.iterrows()
        ]

        # Map CSV column names to model property names
        column_mapping = {
            "data_type": "type",
            "is_nullable": "nullable"
        }

        properties_list = self._get_properties_list(
            df,
            exclude_columns=["database_id", "schema_id", "table_name", "column_name"],
            column_mapping=column_mapping,
            always_include=["name"]
        )

        print(f"Loading {len(nodes)} column nodes...")
        print(self.loader.load_column_nodes(nodes, properties_list=properties_list))

    def load_has_column_relationships(self, csv_filename: Optional[str] = None) -> None:
        """
        Load HAS_COLUMN relationships from CSV file.

        Parameters
        ----------
        csv_filename : str, optional
            CSV filename to load from. Defaults to value in csv_file_map['column'].
        """
        filename = csv_filename or self.csv_file_map["column"]
        df = self._read_csv_if_exists(filename)
        if df is None or df.empty:
            print(f"No {filename} found or file is empty")
            return

        relationships = [
            HasColumn(
                table_id=generate_table_id(row.database_id, row.schema_id, row.table_name),
                column_id=generate_column_id(
                    row.database_id, row.schema_id, row.table_name, row.column_name
                ),
            )
            for _, row in df.iterrows()
        ]

        print(f"Loading {len(relationships)} HAS_COLUMN relationships...")
        print(self.loader.load_has_column_relationships(relationships))

    def load_value_nodes(self, csv_filename: Optional[str] = None) -> None:
        """
        Load value nodes from CSV file.

        Parameters
        ----------
        csv_filename : str, optional
            CSV filename to load from. Defaults to value in csv_file_map['value'].
        """
        filename = csv_filename or self.csv_file_map["value"]
        df = self._read_csv_if_exists(filename)
        if df is None or df.empty:
            print(f"No {filename} found or file is empty")
            return

        nodes = [
            Value(
                id=generate_value_id(row.database_id, row.schema_id, row.table_name, row.column_name, row.value),
                value=row.value,
            )
            for _, row in df.iterrows()
        ]

        # Exclude columns used for ID generation
        properties_list = self._get_properties_list(
            df,
            exclude_columns=["database_id", "schema_id", "table_name", "column_name"],
            always_include=["value"]
        )

        print(f"Loading {len(nodes)} value nodes...")
        print(self.loader.load_value_nodes(nodes, properties_list=properties_list))

    def load_has_value_relationships(self, csv_filename: Optional[str] = None) -> None:
        """
        Load HAS_VALUE relationships from CSV file.

        Parameters
        ----------
        csv_filename : str, optional
            CSV filename to load from. Defaults to value in csv_file_map['value'].
        """
        filename = csv_filename or self.csv_file_map["value"]
        df = self._read_csv_if_exists(filename)
        if df is None or df.empty:
            print(f"No {filename} found or file is empty")
            return

        relationships = [
            HasValue(
                column_id=generate_column_id(row.database_id, row.schema_id, row.table_name, row.column_name),
                value_id=generate_value_id(row.database_id, row.schema_id, row.table_name, row.column_name, row.value),
            )
            for _, row in df.iterrows()
        ]

        print(f"Loading {len(relationships)} HAS_VALUE relationships...")
        print(self.loader.load_has_value_relationships(relationships))

    def load_query_nodes(self, csv_filename: Optional[str] = None) -> None:
        """
        Load query nodes from CSV file.

        Parameters
        ----------
        csv_filename : str, optional
            CSV filename to load from. Defaults to value in csv_file_map['query'].
        """
        filename = csv_filename or self.csv_file_map["query"]
        df = self._read_csv_if_exists(filename)
        if df is None or df.empty:
            print(f"No {filename} found or file is empty")
            return

        nodes = [
            Query(
                id=row.query_id,
                content=row.content,
                description=row.get("description"),
            )
            for _, row in df.iterrows()
        ]

        properties_list = self._get_properties_list(df, exclude_columns=["query_id"], always_include=["content"])

        print(f"Loading {len(nodes)} query nodes...")
        print(self.loader.load_query_nodes(nodes, properties_list=properties_list))

    def load_glossary_nodes(self, csv_filename: Optional[str] = None) -> None:
        """
        Load glossary nodes from CSV file.

        Parameters
        ----------
        csv_filename : str, optional
            CSV filename to load from. Defaults to value in csv_file_map['glossary'].
        """
        filename = csv_filename or self.csv_file_map["glossary"]
        df = self._read_csv_if_exists(filename)
        if df is None or df.empty:
            print(f"No {filename} found or file is empty")
            return

        nodes = [
            Glossary(
                id=row.glossary_id,
                name=row.get("name", row.glossary_id),
                description=row.get("description"),
            )
            for _, row in df.iterrows()
        ]

        properties_list = self._get_properties_list(df, exclude_columns=["glossary_id"], always_include=["name"])

        print(f"Loading {len(nodes)} glossary nodes...")
        print(self.loader.load_glossary_nodes(nodes, properties_list=properties_list))

    def load_category_nodes(self, csv_filename: Optional[str] = None) -> None:
        """
        Load category nodes from CSV file.

        Parameters
        ----------
        csv_filename : str, optional
            CSV filename to load from. Defaults to value in csv_file_map['category'].
        """
        filename = csv_filename or self.csv_file_map["category"]
        df = self._read_csv_if_exists(filename)
        if df is None or df.empty:
            print(f"No {filename} found or file is empty")
            return

        nodes = [
            Category(
                id=row.category_id,
                name=row.get("name", row.category_id),
                description=row.get("description"),
            )
            for _, row in df.iterrows()
        ]

        properties_list = self._get_properties_list(df, exclude_columns=["glossary_id", "category_id"], always_include=["name"])

        print(f"Loading {len(nodes)} category nodes...")
        print(self.loader.load_category_nodes(nodes, properties_list=properties_list))

    def load_has_category_relationships(self, csv_filename: Optional[str] = None) -> None:
        """
        Load HAS_CATEGORY relationships from CSV file.

        Parameters
        ----------
        csv_filename : str, optional
            CSV filename to load from. Defaults to value in csv_file_map['category'].
        """
        filename = csv_filename or self.csv_file_map["category"]
        df = self._read_csv_if_exists(filename)
        if df is None or df.empty:
            print(f"No {filename} found or file is empty")
            return

        relationships = [
            HasCategory(
                glossary_id=row.glossary_id,
                category_id=row.category_id,
            )
            for _, row in df.iterrows()
        ]

        print(f"Loading {len(relationships)} HAS_CATEGORY relationships...")
        print(self.loader.load_has_category_relationships(relationships))

    def load_business_term_nodes(self, csv_filename: Optional[str] = None) -> None:
        """
        Load business term nodes from CSV file.

        Parameters
        ----------
        csv_filename : str, optional
            CSV filename to load from. Defaults to value in csv_file_map['business_term'].
        """
        filename = csv_filename or self.csv_file_map["business_term"]
        df = self._read_csv_if_exists(filename)
        if df is None or df.empty:
            print(f"No {filename} found or file is empty")
            return

        nodes = [
            BusinessTerm(
                id=row.term_id,
                name=row.get("name", row.term_id),
                description=row.get("description"),
            )
            for _, row in df.iterrows()
        ]

        properties_list = self._get_properties_list(df, exclude_columns=["category_id", "term_id"], always_include=["name"])

        print(f"Loading {len(nodes)} business term nodes...")
        print(self.loader.load_business_term_nodes(nodes, properties_list=properties_list))

    def load_has_business_term_relationships(self, csv_filename: Optional[str] = None) -> None:
        """
        Load HAS_BUSINESS_TERM relationships from CSV file.

        Parameters
        ----------
        csv_filename : str, optional
            CSV filename to load from. Defaults to value in csv_file_map['business_term'].
        """
        filename = csv_filename or self.csv_file_map["business_term"]
        df = self._read_csv_if_exists(filename)
        if df is None or df.empty:
            print(f"No {filename} found or file is empty")
            return

        relationships = [
            HasBusinessTerm(
                category_id=row.category_id,
                business_term_id=row.term_id,
            )
            for _, row in df.iterrows()
        ]

        print(f"Loading {len(relationships)} HAS_BUSINESS_TERM relationships...")
        print(self.loader.load_has_business_term_relationships(relationships))

    def load_references_relationships(self, csv_filename: Optional[str] = None) -> None:
        """
        Load REFERENCES relationships from CSV file.

        Parameters
        ----------
        csv_filename : str, optional
            CSV filename to load from. Defaults to value in csv_file_map['column_references'].
        """
        filename = csv_filename or self.csv_file_map["column_references"]
        df = self._read_csv_if_exists(filename)
        if df is None or df.empty:
            print(f"No {filename} found or file is empty")
            return

        relationships = [
            References(
                source_column_id=generate_column_id(
                    row.source_database_id,
                    row.source_schema_id,
                    row.source_table_name,
                    row.source_column_name
                ),
                target_column_id=generate_column_id(
                    row.target_database_id,
                    row.target_schema_id,
                    row.target_table_name,
                    row.target_column_name
                ),
                criteria=row.get("criteria"),
            )
            for _, row in df.iterrows()
        ]

        print(f"Loading {len(relationships)} REFERENCES relationships...")
        print(self.loader.load_references_relationships(relationships))

    def load_query_relationships(
        self,
        query_table_csv: Optional[str] = None,
        query_column_csv: Optional[str] = None
    ) -> None:
        """
        Load query relationships from CSV files.

        Parameters
        ----------
        query_table_csv : str, optional
            CSV filename for query-table relationships.
            Defaults to value in csv_file_map['query_table'].
        query_column_csv : str, optional
            CSV filename for query-column relationships.
            Defaults to value in csv_file_map['query_column'].
        """
        # Load USES_TABLE relationships
        table_filename = query_table_csv or self.csv_file_map["query_table"]
        df_tables = self._read_csv_if_exists(table_filename)
        if df_tables is not None and not df_tables.empty:
            relationships = [
                UsesTable(
                    query_id=row.query_id,
                    table_id=row.table_id,
                )
                for _, row in df_tables.iterrows()
            ]
            print(f"Loading {len(relationships)} USES_TABLE relationships...")
            print(self.loader.load_uses_table_relationships(relationships))
        else:
            print(f"No {table_filename} found or file is empty")

        # Load USES_COLUMN relationships
        column_filename = query_column_csv or self.csv_file_map["query_column"]
        df_columns = self._read_csv_if_exists(column_filename)
        if df_columns is not None and not df_columns.empty:
            relationships = [
                UsesColumn(
                    query_id=row.query_id,
                    column_id=row.column_id,
                )
                for _, row in df_columns.iterrows()
            ]
            print(f"Loading {len(relationships)} USES_COLUMN relationships...")
            print(self.loader.load_uses_column_relationships(relationships))
        else:
            print(f"No {column_filename} found or file is empty")

    def run(self, csv_file_map: Optional[dict[str, str]] = None) -> None:
        """
        Run the complete CSV workflow.

        Loads CSV files, transforms data, and loads into Neo4j.
        All nodes are loaded first, then all relationships.
        Files that don't exist are skipped with a warning message.

        Parameters
        ----------
        csv_file_map : dict[str, str], optional
            Runtime override for CSV file mapping. Merges with instance csv_file_map.
            Allows per-run customization without modifying the instance.
        """
        # Temporarily override file map if provided
        original_map = self.csv_file_map.copy()
        if csv_file_map:
            self.csv_file_map.update(csv_file_map)

        try:
            print(f"Reading CSV files from {self.csv_directory}...")

            print("\n=== Loading Nodes ===")
            # Load core nodes (in dependency order)
            self.load_database_nodes()
            self.load_schema_nodes()
            self.load_table_nodes()
            self.load_column_nodes()

            # Load extended nodes
            self.load_value_nodes()
            self.load_query_nodes()
            self.load_glossary_nodes()
            self.load_category_nodes()
            self.load_business_term_nodes()

            print("\n=== Loading Relationships ===")
            # Load hierarchical relationships
            self.load_has_schema_relationships()
            self.load_has_table_relationships()
            self.load_has_column_relationships()
            self.load_has_value_relationships()

            # Load glossary relationships
            self.load_has_category_relationships()
            self.load_has_business_term_relationships()

            # Load reference relationships
            self.load_references_relationships()

            # Load query relationships
            self.load_query_relationships()

            print("\nCSV workflow completed successfully!")
        finally:
            # Restore original file map
            self.csv_file_map = original_map
