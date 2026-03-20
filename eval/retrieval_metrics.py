"""Retrieval quality metrics for semantic layer evaluation."""

from typing import Any
import sys
sys.path.append('/Users/alexandergilmore/Documents/projects/text2sql-template/mcp_server/src')
from mcp_server.src.models import TableContext


def extract_objects_from_table_contexts(table_contexts: list[TableContext]) -> dict[str, set[str]]:
    """
    Extract all schema objects from retrieved TableContext objects.

    Parameters
    ----------
    table_contexts : list[TableContext]
        Retrieved table contexts from MCP server

    Returns
    -------
    dict
        Dictionary with:
        - tables: set of table names
        - columns: set of column names
        - schemas: set of schema names
    """
    tables = set()
    columns = set()
    schemas = set()

    for ctx in table_contexts:
        # Add fully qualified table name
        full_table = f"{ctx.schema_name}.{ctx.table_name}"
        tables.add(full_table)
        tables.add(ctx.table_name)  # Also add short name
        schemas.add(ctx.schema_name)

        # Add all column names
        for col in ctx.columns:
            columns.add(col.column_name)

    return {
        "tables": tables,
        "columns": columns,
        "schemas": schemas,
    }


def score_retrieval(
    retrieved_contexts: list[TableContext],
    required_objects: dict[str, set[str]],
) -> dict[str, Any]:
    """
    Score retrieval quality at the object level.

    Since we retrieve structured TableContext objects from the graph,
    we measure precision/recall based on schema objects (tables, columns).

    Parameters
    ----------
    retrieved_contexts : list[TableContext]
        Actual table contexts retrieved from MCP server
    required_objects : dict
        Ground truth required objects from sqlglot parse
        {"tables": set, "columns": set, "joins": set}

    Returns
    -------
    dict
        Retrieval scores:
        - table_recall: fraction of required tables that were retrieved
        - column_recall: fraction of required columns that were retrieved
        - object_recall: overall recall across tables and columns
        - table_precision: fraction of retrieved tables that were needed
        - column_precision: fraction of retrieved columns that were needed
        - missing_tables: list of required tables not retrieved
        - missing_columns: list of required columns not retrieved
        - extra_tables: list of retrieved tables not needed
        - extra_columns: list of retrieved columns not needed
    """
    # Extract objects from retrieved contexts
    retrieved_objects = extract_objects_from_table_contexts(retrieved_contexts)

    required_tables = required_objects.get("tables", set())
    required_cols = required_objects.get("columns", set())

    retrieved_tables = retrieved_objects["tables"]
    retrieved_cols = retrieved_objects["columns"]

    # Normalize to lowercase for matching
    required_tables_lower = {t.lower() for t in required_tables}
    required_cols_lower = {c.lower() for c in required_cols}
    retrieved_tables_lower = {t.lower() for t in retrieved_tables}
    retrieved_cols_lower = {c.lower() for c in retrieved_cols}

    # Calculate matches
    matched_tables = required_tables_lower & retrieved_tables_lower
    matched_cols = required_cols_lower & retrieved_cols_lower

    # Recall: what fraction of required objects were retrieved?
    table_recall = len(matched_tables) / max(len(required_tables_lower), 1)
    column_recall = len(matched_cols) / max(len(required_cols_lower), 1)

    total_required = len(required_tables_lower) + len(required_cols_lower)
    total_matched = len(matched_tables) + len(matched_cols)
    object_recall = total_matched / max(total_required, 1)

    # Precision: what fraction of retrieved objects were needed?
    table_precision = len(matched_tables) / max(len(retrieved_tables_lower), 1)
    column_precision = len(matched_cols) / max(len(retrieved_cols_lower), 1)

    total_retrieved = len(retrieved_tables_lower) + len(retrieved_cols_lower)
    object_precision = total_matched / max(total_retrieved, 1)

    # Missing and extra objects
    missing_tables = required_tables_lower - retrieved_tables_lower
    missing_columns = required_cols_lower - retrieved_cols_lower
    extra_tables = retrieved_tables_lower - required_tables_lower
    extra_columns = retrieved_cols_lower - required_cols_lower

    return {
        "table_recall": table_recall,
        "column_recall": column_recall,
        "object_recall": object_recall,
        "table_precision": table_precision,
        "column_precision": column_precision,
        "object_precision": object_precision,
        "missing_tables": list(missing_tables),
        "missing_columns": list(missing_columns),
        "extra_tables": list(extra_tables),
        "extra_columns": list(extra_columns),
        "found_tables": list(matched_tables),
        "found_columns": list(matched_cols),
        "num_retrieved_tables": len(retrieved_tables_lower),
        "num_retrieved_columns": len(retrieved_cols_lower),
    }


def serialize_table_contexts(table_contexts: list[TableContext]) -> list[str]:
    """
    Serialize TableContext objects to strings for token counting and LLM input.

    Parameters
    ----------
    table_contexts : list[TableContext]
        Table contexts from MCP server

    Returns
    -------
    list[str]
        Serialized context strings, one per table
    """
    serialized = []

    for ctx in table_contexts:
        # Format as structured text
        lines = [
            f"Table: {ctx.schema_name}.{ctx.table_name}",
            f"Description: {ctx.table_description}",
            "Columns:",
        ]

        for col in ctx.columns:
            col_info = f"  - {col.column_name} ({col.data_type})"
            if col.column_description:
                col_info += f": {col.column_description}"
            if col.key_type:
                col_info += f" [{col.key_type} key]"
            if not col.nullable:
                col_info += " [NOT NULL]"
            if col.examples:
                col_info += f" (examples: {', '.join(str(e) for e in col.examples[:3])})"
            lines.append(col_info)

            # Add references
            if col.references:
                for ref in col.references:
                    lines.append(f"    -> references {ref.table_name}.{ref.column_name}")

        # Add joins
        if ctx.joins:
            lines.append("Joins:")
            for join in ctx.joins:
                lines.append(f"  - {join.table_name} on {', '.join(join.column_names)}")

        serialized.append("\n".join(lines))

    return serialized
