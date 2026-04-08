"""SQL parsing utilities using sqlglot for structural analysis and scoring."""

from typing import Any

import sqlglot
from sqlglot import exp


def extract_required_objects(sql: str, dialect: str = "bigquery") -> dict[str, Any]:
    """
    Extract required schema objects from SQL.

    Used for:
    - Ground truth generation (from gold SQL)
    - Faithfulness scoring (from generated SQL)

    Parameters
    ----------
    sql : str
        SQL query to parse
    dialect : str
        SQL dialect (default: bigquery)

    Returns:
    -------
    dict
        Dictionary containing:
        - tables: set of table names
        - columns: set of column names
        - joins: set of (table_name, join_condition) tuples
        - aliases: dict mapping alias to table name
    """
    try:
        tree = sqlglot.parse_one(sql, dialect=dialect)
    except Exception as e:
        return {
            "tables": set(),
            "columns": set(),
            "joins": set(),
            "aliases": {},
            "parse_error": str(e),
        }

    # Extract tables
    tables = set()
    for t in tree.find_all(exp.Table):
        # Handle schema.table notation
        if t.db:
            tables.add(f"{t.db}.{t.name}")
        else:
            tables.add(t.name)

    # Extract columns
    columns = set()
    for c in tree.find_all(exp.Column):
        # Only add the column name, not the table prefix
        columns.add(c.name)

    # Extract joins
    joins = set()
    for j in tree.find_all(exp.Join):
        table_node = j.find(exp.Table)
        if table_node:
            join_table = f"{table_node.db}.{table_node.name}" if table_node.db else table_node.name
            join_cond = str(j.args.get("on", ""))
            joins.add((join_table, join_cond))

    # Extract aliases
    aliases = {}
    for a in tree.find_all(exp.Alias):
        table_node = a.find(exp.Table)
        if table_node:
            table_name = f"{table_node.db}.{table_node.name}" if table_node.db else table_node.name
            aliases[a.alias] = table_name

    return {
        "tables": tables,
        "columns": columns,
        "joins": joins,
        "aliases": aliases,
    }


def score_structural_equivalence(
    generated_sql: str, gold_sql: str, dialect: str = "bigquery"
) -> dict[str, Any]:
    """
    Score structural equivalence between generated and gold SQL.

    No database execution required - purely syntactic comparison.

    Parameters
    ----------
    generated_sql : str
        Generated SQL to evaluate
    gold_sql : str
        Ground truth SQL
    dialect : str
        SQL dialect

    Returns:
    -------
    dict
        Scoring results with:
        - exact_match: bool (normalized SQL strings match)
        - table_match: bool (same tables referenced)
        - column_match: bool (same columns referenced)
        - structural_match: bool (tables AND columns match)
        - missing_tables: list of tables in gold but not in generated
        - extra_tables: list of tables in generated but not in gold
        - missing_columns: list of columns in gold but not in generated
        - extra_columns: list of columns in generated but not in gold
    """
    try:
        gen_objects = extract_required_objects(generated_sql, dialect)
        gold_objects = extract_required_objects(gold_sql, dialect)

        # Check for parse errors
        if "parse_error" in gen_objects:
            return {
                "parse_error": gen_objects["parse_error"],
                "structural_match": False,
                "exact_match": False,
                "table_match": False,
                "column_match": False,
            }

        if "parse_error" in gold_objects:
            return {
                "parse_error": f"Gold SQL parse error: {gold_objects['parse_error']}",
                "structural_match": False,
                "exact_match": False,
                "table_match": False,
                "column_match": False,
            }
    except Exception as e:
        return {
            "parse_error": str(e),
            "structural_match": False,
            "exact_match": False,
            "table_match": False,
            "column_match": False,
        }

    table_match = gen_objects["tables"] == gold_objects["tables"]
    col_match = gen_objects["columns"] == gold_objects["columns"]

    # Try to normalize and compare
    exact_match = False
    try:
        gen_norm = sqlglot.transpile(generated_sql, read=dialect, write=dialect, pretty=False)[0]
        gold_norm = sqlglot.transpile(gold_sql, read=dialect, write=dialect, pretty=False)[0]
        exact_match = gen_norm == gold_norm
    except Exception:
        pass

    return {
        "exact_match": exact_match,
        "table_match": table_match,
        "column_match": col_match,
        "structural_match": table_match and col_match,
        "missing_tables": list(gold_objects["tables"] - gen_objects["tables"]),
        "extra_tables": list(gen_objects["tables"] - gold_objects["tables"]),
        "missing_columns": list(gold_objects["columns"] - gen_objects["columns"]),
        "extra_columns": list(gen_objects["columns"] - gold_objects["columns"]),
    }


def score_schema_faithfulness(
    generated_sql: str, retrieved_context: list[str], dialect: str = "bigquery"
) -> dict[str, Any]:
    """
    Deterministic faithfulness scoring without LLM judge.

    Checks if tables/columns in generated SQL are grounded in retrieved context.

    Parameters
    ----------
    generated_sql : str
        Generated SQL to evaluate
    retrieved_context : list[str]
        Context chunks retrieved from semantic layer
    dialect : str
        SQL dialect

    Returns:
    -------
    dict
        Faithfulness scores:
        - table_faithfulness: ratio of tables found in context
        - column_faithfulness: ratio of columns found in context
        - hallucinated_tables: list of tables not in context
        - hallucinated_columns: list of columns not in context
        - used_objects: extracted objects from SQL
        - executable: bool (SQL parsed successfully)
    """
    try:
        used = extract_required_objects(generated_sql, dialect)

        if "parse_error" in used:
            return {
                "parse_error": used["parse_error"],
                "executable": False,
                "table_faithfulness": 0.0,
                "column_faithfulness": 0.0,
            }
    except Exception as e:
        return {
            "parse_error": str(e),
            "executable": False,
            "table_faithfulness": 0.0,
            "column_faithfulness": 0.0,
        }

    # Join context into a single blob for substring matching
    context_blob = " ".join(retrieved_context).lower()

    # Check which tables/columns are grounded in context
    grounded_tables = {t for t in used["tables"] if t.lower() in context_blob}
    grounded_cols = {c for c in used["columns"] if c.lower() in context_blob}

    table_faithfulness = len(grounded_tables) / max(len(used["tables"]), 1)
    column_faithfulness = len(grounded_cols) / max(len(used["columns"]), 1)

    return {
        "table_faithfulness": table_faithfulness,
        "column_faithfulness": column_faithfulness,
        "hallucinated_tables": list(used["tables"] - grounded_tables),
        "hallucinated_columns": list(used["columns"] - grounded_cols),
        "used_objects": {
            "tables": list(used["tables"]),
            "columns": list(used["columns"]),
        },
        "executable": True,
    }


def score_context_utilization(
    generated_sql: str, retrieved_context_objects: set[str], dialect: str = "bigquery"
) -> float:
    """
    Measure context utilization (inverse of over-retrieval).

    What fraction of retrieved schema objects were actually used in the SQL?

    Parameters
    ----------
    generated_sql : str
        Generated SQL
    retrieved_context_objects : set[str]
        Set of all table/column names in retrieved context
    dialect : str
        SQL dialect

    Returns:
    -------
    float
        Utilization score (0.0 to 1.0)
    """
    try:
        used = extract_required_objects(generated_sql, dialect)
        if "parse_error" in used:
            return 0.0
    except Exception:
        return 0.0

    all_used = used["tables"] | used["columns"]
    used_from_context = all_used & retrieved_context_objects

    if len(retrieved_context_objects) == 0:
        return 0.0

    return len(used_from_context) / len(retrieved_context_objects)
