from google.cloud import bigquery
import pandas as pd
import hashlib


def extract_database_info(
    client: bigquery.Client, project_id: str, dataset_id: str
) -> pd.DataFrame:
    """
    Extract BigQuery database information.

    Parameters
    ----------
    client: bigquery.Client
        The BigQuery client.
    project_id: str
        The project ID.
    dataset_id: str
        The dataset ID.

    Returns
    -------
    pd.DataFrame
        A Pandas DataFrame containing the BigQuery database information.
    """

    return client.query(f"""
SELECT 
    DISTINCT table_catalog,
    table_schema,
    option_value as description
FROM `{project_id}`.`{dataset_id}`.INFORMATION_SCHEMA.TABLES tables
    LEFT JOIN `{project_id}`.INFORMATION_SCHEMA.SCHEMATA_OPTIONS schemata_options
        ON tables.table_schema = schemata_options.schema_name
WHERE option_name = 'description'
""").to_dataframe()


def extract_table_info(
    client: bigquery.Client, project_id: str, dataset_id: str
) -> pd.DataFrame:
    """
    Extract BigQuery table information.

    Parameters
    ----------
    client: bigquery.Client
        The BigQuery client.
    project_id: str
        The project ID.
    dataset_id: str
        The dataset ID.

    Returns
    -------
    pd.DataFrame
        A Pandas DataFrame containing the BigQuery table information.
    """

    return client.query(f"""
SELECT 
    tables.table_catalog,
    tables.table_schema,
    tables.table_name,
    tables.table_type,
    tables.creation_time,
    tables.ddl,
    table_options.option_value as description
FROM `{project_id}`.`{dataset_id}`.INFORMATION_SCHEMA.TABLES as tables
    LEFT JOIN `{project_id}`.`{dataset_id}`.INFORMATION_SCHEMA.TABLE_OPTIONS as table_options
        ON tables.table_catalog = table_options.table_catalog
        AND tables.table_schema = table_options.table_schema
        AND tables.table_name = table_options.table_name
WHERE table_type = 'BASE TABLE'
ORDER BY table_name
""").to_dataframe()


def extract_column_info(
    client: bigquery.Client, project_id: str, dataset_id: str
) -> pd.DataFrame:
    """
    Extract BigQuery column information.

    Parameters
    ----------
    client: bigquery.Client
        The BigQuery client.
    project_id: str
        The project ID.
    dataset_id: str
        The dataset ID.

    Returns
    -------
    pd.DataFrame
        A Pandas DataFrame containing the BigQuery column information.
    """

    def _is_pk(row: pd.Series) -> bool:
        return isinstance(row["constraint_name"], str) and row[
            "constraint_name"
        ].endswith("pk$")

    def _is_fk(row: pd.Series) -> bool:
        return (
            isinstance(row["constraint_name"], str) and ".fk_" in row["constraint_name"]
        )

    df = client.query(f"""
SELECT 
    columns.table_catalog,
    columns.table_schema,
    columns.table_name,
    columns.column_name,
    columns.is_nullable,
    columns.data_type,
    column_field_paths.description,
    key_column_usage.constraint_name

FROM `{project_id}`.`{dataset_id}`.INFORMATION_SCHEMA.COLUMNS as columns
    LEFT JOIN `{project_id}`.`{dataset_id}`.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS column_field_paths
        ON columns.table_schema = column_field_paths.table_schema
        AND columns.table_name = column_field_paths.table_name
        AND columns.column_name = column_field_paths.column_name

    LEFT JOIN `{project_id}`.`{dataset_id}`.INFORMATION_SCHEMA.KEY_COLUMN_USAGE key_column_usage
        ON columns.table_schema = key_column_usage.table_schema
        AND columns.table_name = key_column_usage.table_name
        AND columns.column_name = key_column_usage.column_name
""").to_dataframe()

    df["is_primary_key"] = df.apply(_is_pk, axis=1)
    df["is_foreign_key"] = df.apply(_is_fk, axis=1)
    return df


def extract_column_references_info(
    client: bigquery.Client, project_id: str, dataset_id: str
) -> pd.DataFrame:
    """
    Extract BigQuery column references information.

    Parameters
    ----------
    client: bigquery.Client
        The BigQuery client.
    project_id: str
        The project ID.
    dataset_id: str
        The dataset ID.

    Returns
    -------
    pd.DataFrame
        A Pandas DataFrame containing the BigQuery column references information.
    """
    return client.query(f"""
SELECT 
    tc.constraint_catalog,
    tc.constraint_schema,
    tc.constraint_name,
    tc.constraint_type,
    tc.table_name,
    kcu.column_name,
    kcu.ordinal_position,
    ccu.table_name AS referenced_table,
    ccu.column_name AS referenced_column
FROM `{project_id}`.`{dataset_id}`.INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
    LEFT JOIN `{project_id}`.`{dataset_id}`.INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
        ON tc.constraint_name = kcu.constraint_name
    LEFT JOIN `{project_id}`.`{dataset_id}`.INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu
        ON tc.constraint_name = ccu.constraint_name
ORDER BY tc.table_name, tc.constraint_type, kcu.ordinal_position
""").to_dataframe()

def extract_column_unique_values(
    client: bigquery.Client, project_id: str, dataset_id: str, table_name: str, column_names: list[str], limit: int = 10
) -> pd.DataFrame:
    """
    Extract BigQuery column unique values to be used as reference values.

    Parameters
    ----------
    client: bigquery.Client
        The BigQuery client.
    project_id: str
        The project ID.
    dataset_id: str
        The dataset ID.
    table_name: str
        The table name.
    column_names: list[str]
        List of column names to extract unique values from.
    limit: int
        The number of unique values to extract per column.

    Returns
    -------
    pd.DataFrame
        A Pandas DataFrame with columns: column_name, unique_value.
        Each row represents one unique value for a column.
    """

    # Build ARRAY_AGG aggregation for each column
    select_clauses = []
    for col in column_names:
        select_clauses.append(f"ARRAY_AGG(DISTINCT `{col}` IGNORE NULLS LIMIT {limit}) as `{col}`")

    query = f"""
    SELECT {', '.join(select_clauses)}
    FROM `{project_id}`.`{dataset_id}`.{table_name}
    """

    df = client.query(query).to_dataframe()
    # Reshape to long format: column_name, unique_value
    # Melt the dataframe to get column names as a column, then explode the arrays
    result = df.melt(var_name='column_name', value_name='unique_value')
    result = result.explode('unique_value').dropna().reset_index(drop=True)

    result['unique_value'] = result['unique_value'].astype(str)

    # Add column_id in the format: project_id.dataset_id.table_name.column_name
    result['column_id'] = project_id + '.' + dataset_id + '.' + table_name + '.' + result['column_name']

    # Hash the unique value and append to column_id for value_id
    result['value_id'] = result.apply(
        lambda row: row['column_id'] + '.' + hashlib.md5(row['unique_value'].encode()).hexdigest(),
        axis=1
    )

    return result
