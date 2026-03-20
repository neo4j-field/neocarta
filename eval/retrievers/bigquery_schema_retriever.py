"""
BigQuery schema retriever for full_schema baseline condition.

Loads the full BigQuery schema from a persisted JSON file.
The JSON format matches what the MCP server returns from get_full_metadata_schema.
"""

import json
from pathlib import Path
from typing import Any
import sys
sys.path.append('/Users/alexandergilmore/Documents/projects/text2sql-template/mcp_server/src')
from models import TableContext


class BigQuerySchemaRetriever:
    """
    Loads full BigQuery schema from a persisted JSON file.

    The schema is serialized at dataset prep time to ensure the baseline
    is stable and reproducible across eval runs.
    """

    def __init__(self, schema_path: str | Path):
        """
        Initialize retriever with path to persisted schema.

        Parameters
        ----------
        schema_path : str | Path
            Path to JSON file containing full schema
        """
        self.schema_path = Path(schema_path)
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        with open(self.schema_path) as f:
            self.schema_data: list[dict[str, Any]] = json.load(f)

        self._schema_str: str | None = None
        self._table_contexts: list[TableContext] | None = None

    def as_string(self) -> str:
        """
        Return schema as a single JSON string for LLM context injection.

        Returns
        -------
        str
            Full schema serialized as JSON
        """
        if self._schema_str is None:
            self._schema_str = json.dumps(self.schema_data, indent=2)
        return self._schema_str

    def as_table_contexts(self) -> list[TableContext]:
        """
        Return schema as structured TableContext objects.

        Returns
        -------
        list[TableContext]
            List of table contexts
        """
        if self._table_contexts is None:
            self._table_contexts = [
                TableContext.model_validate(table_data)
                for table_data in self.schema_data
            ]
        return self._table_contexts

    def as_context_list(self) -> list[str]:
        """
        Return schema split by table for structured context injection.

        Each entry is one table's schema as a formatted string.

        Returns
        -------
        list[str]
            List of table context strings
        """
        from eval.retrieval_metrics import serialize_table_contexts

        contexts = self.as_table_contexts()
        return serialize_table_contexts(contexts)

    @classmethod
    def from_mcp_response(
        cls,
        mcp_response: list[TableContext],
        persist_path: str | Path
    ) -> "BigQuerySchemaRetriever":
        """
        Persist MCP response to disk, then load it.

        Use this to create the full schema baseline file.

        Parameters
        ----------
        mcp_response : list[TableContext]
            Response from MCP server's get_full_metadata_schema
        persist_path : str | Path
            Where to save the schema file

        Returns
        -------
        BigQuerySchemaRetriever
            Retriever loaded from the persisted file
        """
        path = Path(persist_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Serialize TableContext objects to JSON
        schema_data = [ctx.model_dump() for ctx in mcp_response]

        with open(path, "w") as f:
            json.dump(schema_data, f, indent=2)

        return cls(path)

    def extract_object_names(self) -> set[str]:
        """
        Extract all table and column names for object-level recall scoring.

        Returns
        -------
        set[str]
            Set of all table and column names (lowercased)
        """
        names = set()
        for ctx in self.as_table_contexts():
            names.add(ctx.table_name.lower())
            names.add(f"{ctx.schema_name}.{ctx.table_name}".lower())
            for col in ctx.columns:
                names.add(col.column_name.lower())
        return names

    def get_num_tables(self) -> int:
        """Get total number of tables in schema."""
        return len(self.schema_data)

    def get_num_columns(self) -> int:
        """Get total number of columns across all tables."""
        return sum(
            len(ctx.columns)
            for ctx in self.as_table_contexts()
        )
