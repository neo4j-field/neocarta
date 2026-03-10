import json
import pandas as pd
import sqlglot
from sqlglot.expressions import Column, Table, Insert, Update, Join
import hashlib

def create_query_id(query: str) -> str:
    """
    Create a query ID from a query string.
    """
    return hashlib.sha256(query.encode()).hexdigest()

def parse_bigquery_query_log_json(query_log_file: str) -> pd.DataFrame:
    """
    Parse a BigQuery query log JSON file into a Pandas DataFrame.
    """
    with open(query_log_file, "r") as f:
        data = json.load(f)
    
    query_metadata = []
    table_ids: set[str] = set()

    for item in data:
        if "jobQueryRequest" not in item["protoPayload"]["serviceData"]:
            continue

        base = item["protoPayload"]["serviceData"]
        project_id = base["jobQueryRequest"]["projectId"]
        query = base["jobQueryRequest"]["query"]
        ref_tables = base["jobQueryResponse"]["job"]["jobStatistics"]["referencedTables"]

        query_metadata.append({
            "project_id": project_id,
            "query": query,
            "query_id": create_query_id(query),
        })
        # format as table id
        for ref_table in ref_tables:
            table_ids.add(f"{project_id}.{ref_table['datasetId']}.{ref_table['tableId']}")

    
    ref_tables_metadata = []
    for tid in table_ids:
        parts = tid.split(".")
        project_id = parts[0]
        dataset_id = parts[1]
        table_id = parts[2]
        ref_tables_metadata.append({
            "project_id": project_id,
            "dataset_id": dataset_id,
            "table_id": table_id,
        })
    return {
        "query_info": pd.DataFrame(query_metadata),
        "table_info": pd.DataFrame(ref_tables_metadata),
    }

def parse_sql_query(query: str, query_id: str, read: str = "bigquery") -> dict[str, list[dict]]:
    """
    Parse a SQL query into a Pandas DataFrame.

    Parameters
    ----------
    query: str
        The SQL query to parse.
    query_id: str
        The id of the query.
    read: str
        The dialect of the query.

    Returns
    -------
    dict[str, list[dict]]
        A dictionary with the query information.
        - table_info: A list of dictionaries with the table information.
        - column_info: A list of dictionaries with the column information.
        - references_info: A list of dictionaries with the references information.
    """

    # Database node properties
    platform = None
    service = None

    match read:
        case "bigquery":
            platform = "GCP"
            service = "BIGQUERY"
        case _:
            raise ValueError(f"Unsupported read argument: {read}")

    try:
        parsed = sqlglot.parse_one(query, read=read)
        column_info = list()
        references_info = []
        alias_to_table_name = dict()
        alias_to_table_id = dict()
        table_info = list()

        table_ids = set()

        # Table information and defining aliases
        for t in parsed.find_all(Table):
            table = t.this
            table_name = table.name
            table_alias = t.alias
            
            alias_to_table_name[table_alias or table_name] = table_name
            table_id = f"{t.catalog}.{t.db}.{table_name}"

            alias_to_table_id[table_alias or table_name] = table_id

            table_ids.add(table_id)
            table_info.append({
                "platform": platform,
                "service": service,
                "table_id": table_id,
                "table_name": table_name,
                "dataset_id": f"{t.catalog}.{t.db}",
                "dataset_name": t.db,
                "project_name": t.catalog,
                "project_id": t.catalog,
                "table_alias": table_alias,
                "query_id": query_id,
            })


        # Column information
        for c in parsed.find_all(Column):
            table_alias = c.table
            table_name = alias_to_table_name.get(table_alias, table_alias)
            table_id = alias_to_table_id.get(table_alias, table_alias)
            column_name = c.name
            column_info.append({
                "table_alias": table_alias,
                "table_name": table_name,
                "column_name": column_name,
                "table_id": table_id,
                "column_id": f"{table_id}.{column_name}",
                "query_id": query_id,
            })
        
        # Join information
        for j in parsed.find_all(Join):
            left_table = j.this
            left_table_name = left_table.name
            left_table_alias = left_table.alias

            join_condition = j.args.get("on") if "on" in j.args else None

            if join_condition:
                right_table_alias = getattr(join_condition.this, 'table', None) if hasattr(join_condition, 'this') else None
                right_table_name = alias_to_table_name.get(right_table_alias, "?") if right_table_alias else None
            else:
                right_table_name = None
                right_table_alias = None

            # Extract column information from join condition if available
            left_column_name = None
            left_column_id = None
            right_column_name = None
            right_column_id = None

            if join_condition:
                # Try to extract left column (expression side)
                if hasattr(join_condition, 'expression') and join_condition.expression:
                    left_column_name = getattr(join_condition.expression, 'name', None)
                    if left_column_name and left_table_alias:
                        left_column_id = f"{alias_to_table_id.get(left_table_alias, left_table_alias)}.{getattr(join_condition.expression, 'this', left_column_name)}"

                # Try to extract right column (this side)
                if hasattr(join_condition, 'this') and join_condition.this:
                    right_column_name = getattr(join_condition.this, 'name', None)
                    if right_column_name and right_table_alias:
                        right_column_id = f"{alias_to_table_id.get(right_table_alias, right_table_alias)}.{getattr(join_condition.this, 'this', right_column_name)}"

            to_add = {
                "left_table_name": left_table_name,
                "left_table_id": alias_to_table_id.get(left_table_alias, left_table_alias),
                "left_table_alias": left_table_alias,
                "left_column_name": left_column_name,
                "left_column_id": left_column_id,
                "right_table_name": right_table_name,
                "right_table_id": alias_to_table_id.get(right_table_alias, right_table_alias),
                "right_table_alias": right_table_alias,
                "right_column_name": right_column_name,
                "right_column_id": right_column_id,
                "criteria": str(join_condition) if join_condition else None
                }
            
            # only add valid references. we know a reference is valid if both left and right column ids are known
            if to_add.get("left_column_id") is not None and to_add.get("right_column_id") is not None:
                references_info.append(to_add)

        return {
            "table_info": table_info,
            "column_info": column_info,
            "references_info": references_info,
        }
    except Exception as e:
        print(f"Error parsing SQL query: {e}")
        # sometimes it doesn't work
        return None