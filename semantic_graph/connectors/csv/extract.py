"""CSV Extractor for reading and validating CSV files into a cache."""

from pathlib import Path
from typing import ClassVar

import pandas as pd

from .models import CSVExtractorCache

# Required columns per entity type
REQUIRED_COLUMNS: dict[str, list[str]] = {
    "database": ["database_id"],
    "schema": ["database_id", "schema_id"],
    "table": ["database_id", "schema_id", "table_name"],
    "column": ["database_id", "schema_id", "table_name", "column_name"],
    "column_references": [
        "source_database_id",
        "source_schema_id",
        "source_table_name",
        "source_column_name",
        "target_database_id",
        "target_schema_id",
        "target_table_name",
        "target_column_name",
    ],
    "value": ["database_id", "schema_id", "table_name", "column_name", "value"],
    "query": ["query_id", "content"],
    "query_table": ["query_id", "table_id"],
    "query_column": ["query_id", "column_id"],
    "glossary": ["glossary_id"],
    "category": ["glossary_id", "category_id"],
    "business_term": ["category_id", "term_id"],
}


# Maps node/relationship type names (as passed by callers) to the internal
# entity keys used by _extract() and csv_file_map. Defined at module level so
# they are shared between extract_all() and any validation logic.
NODE_ENTITIES: dict[str, str] = {
    "database": "database",
    "schema": "schema",
    "table": "table",
    "column": "column",
    "value": "value",
    "query": "query",
    "glossary": "glossary",
    "category": "category",
    "business_term": "business_term",
}

# Relationships that share a CSV with their parent node entity reuse that entity
# key (e.g. has_schema is built from schema_info.csv). Cross-entity relationship
# CSVs (column_references, query_table, query_column) have their own keys.
REL_ENTITIES: dict[str, str] = {
    "has_schema": "schema",
    "has_table": "table",
    "has_column": "column",
    "has_value": "value",
    "has_category": "category",
    "has_business_term": "business_term",
    "references": "column_references",
    "uses_table": "query_table",
    "uses_column": "query_column",
}


class CSVExtractor:
    """
    Extractor for reading CSV files from a directory and caching their contents.

    Reads each CSV file, validates that required columns are present,
    and stores the resulting DataFrames in an internal cache.
    """

    DEFAULT_FILE_MAP: ClassVar[dict[str, str]] = {
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
        csv_file_map: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize the CSV extractor.

        Parameters
        ----------
        csv_directory : str
            Path to the directory containing CSV files.
        csv_file_map : dict[str, str], optional
            Custom mapping of entity keys to CSV filenames.
            Merges with DEFAULT_FILE_MAP, allowing partial overrides.
        """
        self.csv_directory = Path(csv_directory)
        if not self.csv_directory.exists():
            raise ValueError(f"csv_directory does not exist: {self.csv_directory}")
        if not self.csv_directory.is_dir():
            raise ValueError(f"csv_directory is not a directory: {self.csv_directory}")

        self.csv_file_map = self.DEFAULT_FILE_MAP.copy()
        if csv_file_map:
            self.csv_file_map.update(csv_file_map)

        self._cache: CSVExtractorCache = CSVExtractorCache()

    # ------------------------------------------------------------------
    # Cache properties
    # ------------------------------------------------------------------

    @property
    def database_info(self) -> pd.DataFrame:
        return self._cache.get("database_info", pd.DataFrame())

    @property
    def schema_info(self) -> pd.DataFrame:
        return self._cache.get("schema_info", pd.DataFrame())

    @property
    def table_info(self) -> pd.DataFrame:
        return self._cache.get("table_info", pd.DataFrame())

    @property
    def column_info(self) -> pd.DataFrame:
        return self._cache.get("column_info", pd.DataFrame())

    @property
    def column_references_info(self) -> pd.DataFrame:
        return self._cache.get("column_references_info", pd.DataFrame())

    @property
    def value_info(self) -> pd.DataFrame:
        return self._cache.get("value_info", pd.DataFrame())

    @property
    def query_info(self) -> pd.DataFrame:
        return self._cache.get("query_info", pd.DataFrame())

    @property
    def query_table_info(self) -> pd.DataFrame:
        return self._cache.get("query_table_info", pd.DataFrame())

    @property
    def query_column_info(self) -> pd.DataFrame:
        return self._cache.get("query_column_info", pd.DataFrame())

    @property
    def glossary_info(self) -> pd.DataFrame:
        return self._cache.get("glossary_info", pd.DataFrame())

    @property
    def category_info(self) -> pd.DataFrame:
        return self._cache.get("category_info", pd.DataFrame())

    @property
    def business_term_info(self) -> pd.DataFrame:
        return self._cache.get("business_term_info", pd.DataFrame())

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _read_csv(self, filename: str) -> pd.DataFrame | None:
        """Read a CSV file if it exists, returning None otherwise."""
        filepath = self.csv_directory / filename
        if not filepath.exists():
            return None
        df = pd.read_csv(filepath)
        # pandas already converts "NaN", "NULL", "null" to float NaN via its
        # default na_values. Convert remaining NaN to Python None so downstream
        # code receives None rather than float('nan').
        return df.where(df.notna(), None)

    def _validate_columns(self, df: pd.DataFrame, entity_key: str, filename: str) -> None:
        """
        Raise ValueError if any required columns are missing from df.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to validate.
        entity_key : str
            Key into REQUIRED_COLUMNS (e.g. "schema", "column").
        filename : str
            CSV filename, used only for the error message.
        """
        required = REQUIRED_COLUMNS.get(entity_key, [])
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(
                f"{filename} is missing required columns: {missing}. "
                f"Required columns for '{entity_key}': {required}"
            )

    def _extract(self, entity_key: str, cache_key: str) -> pd.DataFrame | None:
        """
        Read, validate, and cache a single CSV file.

        Parameters
        ----------
        entity_key : str
            Key into csv_file_map and REQUIRED_COLUMNS.
        cache_key : str
            Key used to store the DataFrame in the cache.

        Returns:
        -------
        pd.DataFrame or None
            The loaded DataFrame, or None if the file does not exist.
        """
        filename = self.csv_file_map[entity_key]
        df = self._read_csv(filename)
        if df is None:
            print(f"  Skipping {filename} (file not found)")
            return None
        if df.empty:
            print(f"  Skipping {filename} (file is empty)")
            return None

        self._validate_columns(df, entity_key, filename)
        self._cache[cache_key] = df
        print(f"  Extracted {len(df)} rows from {filename}")
        return df

    # ------------------------------------------------------------------
    # Public extract methods
    # ------------------------------------------------------------------

    def extract_database_info(self) -> pd.DataFrame | None:
        return self._extract("database", "database_info")

    def extract_schema_info(self) -> pd.DataFrame | None:
        return self._extract("schema", "schema_info")

    def extract_table_info(self) -> pd.DataFrame | None:
        return self._extract("table", "table_info")

    def extract_column_info(self) -> pd.DataFrame | None:
        return self._extract("column", "column_info")

    def extract_column_references_info(self) -> pd.DataFrame | None:
        return self._extract("column_references", "column_references_info")

    def extract_value_info(self) -> pd.DataFrame | None:
        return self._extract("value", "value_info")

    def extract_query_info(self) -> pd.DataFrame | None:
        return self._extract("query", "query_info")

    def extract_query_table_info(self) -> pd.DataFrame | None:
        return self._extract("query_table", "query_table_info")

    def extract_query_column_info(self) -> pd.DataFrame | None:
        return self._extract("query_column", "query_column_info")

    def extract_glossary_info(self) -> pd.DataFrame | None:
        return self._extract("glossary", "glossary_info")

    def extract_category_info(self) -> pd.DataFrame | None:
        return self._extract("category", "category_info")

    def extract_business_term_info(self) -> pd.DataFrame | None:
        return self._extract("business_term", "business_term_info")

    def extract_all(
        self,
        include_nodes: list[str] | None = None,
        include_relationships: list[str] | None = None,
    ) -> None:
        """
        Extract and validate CSV files, caching results.

        When include_nodes or include_relationships are provided, only the CSV
        files required to satisfy those requests are read. Otherwise all files
        are extracted.

        Parameters
        ----------
        include_nodes : list[str], optional
            Node types to include. Allowed values:
            "database", "schema", "table", "column", "value",
            "query", "glossary", "category", "business_term".
        include_relationships : list[str], optional
            Relationship types to include. Allowed values:
            "has_schema", "has_table", "has_column", "has_value",
            "has_category", "has_business_term", "references",
            "uses_table", "uses_column".
        """
        if include_nodes is not None:
            unknown = sorted(set(include_nodes) - NODE_ENTITIES.keys())
            if unknown:
                raise ValueError(
                    f"Unknown node types: {unknown}. Valid values: {sorted(NODE_ENTITIES.keys())}"
                )

        if include_relationships is not None:
            unknown = sorted(set(include_relationships) - REL_ENTITIES.keys())
            if unknown:
                raise ValueError(
                    f"Unknown relationship types: {unknown}. "
                    f"Valid values: {sorted(REL_ENTITIES.keys())}"
                )

        if include_nodes is None and include_relationships is None:
            needed: set[str] = set(NODE_ENTITIES.values()) | set(REL_ENTITIES.values())
        else:
            needed = set()
            for name in include_nodes or []:
                needed.add(NODE_ENTITIES[name])
            for name in include_relationships or []:
                needed.add(REL_ENTITIES[name])

        print(f"Extracting CSV files from {self.csv_directory}...")
        if "database" in needed:
            self.extract_database_info()
        if "schema" in needed:
            self.extract_schema_info()
        if "table" in needed:
            self.extract_table_info()
        if "column" in needed:
            self.extract_column_info()
        if "column_references" in needed:
            self.extract_column_references_info()
        if "value" in needed:
            self.extract_value_info()
        if "query" in needed:
            self.extract_query_info()
        if "query_table" in needed:
            self.extract_query_table_info()
        if "query_column" in needed:
            self.extract_query_column_info()
        if "glossary" in needed:
            self.extract_glossary_info()
        if "category" in needed:
            self.extract_category_info()
        if "business_term" in needed:
            self.extract_business_term_info()
