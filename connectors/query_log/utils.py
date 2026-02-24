import json
import pandas as pd
import sqlglot
from sqlglot.expressions import Column, Table, Insert, Update, Join
import hashlib

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
            "query_id": hashlib.sha256(query.encode()).hexdigest(),
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
        # tables = set()
        column_info = list()
        references_info = []
        # aliases = {}
        alias_to_table_name = dict()
        alias_to_table_id = dict()
        table_info = list()

        table_ids = set()

        # tables and aliases
        # for table_expr in parsed.find_all(Table):
        #     table_name = table_expr.name
        #     alias = table_expr.alias
        #     tables.add(table_name)
        #     aliases[alias or table_name] = table_name        
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

        # tables_df = pd.DataFrame(table_info)


        # columns
        # for column_expr in parsed.find_all(Column):
        #     column_name = column_expr.name
        #     table_or_alias = column_expr.table
        #     if table_or_alias:
        #         table_name = aliases.get(table_or_alias, table_or_alias)
        #         columns.add((table_name, column_name))
        #     else:
        #         if len(tables) == 1:
        #             columns.add((next(iter(tables)), column_name))
        #         else:
        #             # columns.add((None, column_name))
        #             pass # don't add column unless we can match it to a table
        for c in parsed.find_all(Column):
            table_alias = c.table
            table_name = alias_to_table_name.get(table_alias, table_alias)
            table_id = alias_to_table_id.get(table_alias, table_alias)
            column_name = c.this
            column_info.append({
                "table_alias": table_alias,
                "table_name": table_name,
                "column_name": column_name,
                "table_id": table_id,
                "column_id": f"{table_id}.{column_name}",
                "query_id": query_id,
            })
        # columns_df = pd.DataFrame(column_info)

        # JOINs
        # for join in parsed.find_all(JOIN):
        #     join_table_expr = join.this
        #     join_table_name = join_table_expr.name
        #     tables.add(join_table_name)
        #     alias = join_table_expr.alias
        #     aliases[alias or join_table_name] = join_table_name
        #     join_condition = str(join.args.get("on")) if "on" in join.args else None
        #     joins.append({"left_table": join_table_name, "right_table": join_table_name, "criteria": join_condition})

        # join_criteria = "; ".join([f"JOIN {j['table']} ON {j['criteria']}" for j in joins if j['criteria']]) if joins else None
        for j in parsed.find_all(Join):
            left_table = j.this
            left_table_name = left_table.name
            left_table_alias = left_table.alias

            join_condition = j.args.get("on") if "on" in j.args else None

            if join_condition:
                right_table_alias = join_condition.this.table
                right_table_name = alias_to_table_name.get(right_table_alias, "?")
            else:
                right_table_name = None
                right_table_alias = None
            
            references_info.append({
                "left_table_name": left_table_name, 
                "left_table_id": alias_to_table_id.get(left_table_alias, left_table_alias),
                "left_table_alias": left_table_alias,
                "left_column_name": join_condition.expression.this,
                "left_column_id": f"{alias_to_table_id.get(left_table_alias, left_table_alias)}.{join_condition.expression.this}",
                "right_table_name": right_table_name, 
                "right_table_id": alias_to_table_id.get(right_table_alias, right_table_alias),
                "right_table_alias": right_table_alias,
                "right_column_name": join_condition.this.this,
                "right_column_id": f"{alias_to_table_id.get(right_table_alias, right_table_alias)}.{join_condition.this.this}",
                "criteria": str(join_condition)
                })
        # references_info_df = pd.DataFrame(references_info)
# 
        # insert
        # if isinstance(parsed, Insert):
        #     table_name = parsed.this.name
        #     columns_expr = parsed.args.get("columns")
        #     if columns_expr:
        #         for col_expr in columns_expr.expressions:
        #             columns.add((table_name, col_expr.name))

        # update
        # if isinstance(parsed, Update):
        #     table_name = parsed.this.name
        #     assignments = parsed.args.get("expressions")
        #     if assignments:
        #         for assign in assignments:
        #             col_expr = assign.this
        #             columns.add((table_name, col_expr.name))

        return {
            "table_info": table_info,
            "column_info": column_info,
            "references_info": references_info,
        }
    except Exception as e:
        print(f"Error parsing SQL query: {e}")
        # sometimes it doesn't work
        return None