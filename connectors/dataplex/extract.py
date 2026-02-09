"""Extract metadata from GCP Dataplex."""

from google.cloud import dataplex_v1
import pandas as pd


def extract_dataplex_entities(
    metadata_client: dataplex_v1.MetadataServiceClient,
    project_id: str,
    location: str,
    lake_id: str,
    zone_id: str,
) -> pd.DataFrame:
    """
    Extract Dataplex entities (tables) from a zone.

    Parameters
    ----------
    metadata_client: dataplex_v1.MetadataServiceClient
        The Dataplex Metadata client.
    project_id: str
        The GCP project ID.
    location: str
        The location (e.g., 'us-central1').
    lake_id: str
        The Dataplex lake ID.
    zone_id: str
        The Dataplex zone ID.

    Returns
    -------
    pd.DataFrame
        A DataFrame with entity information including project_id, dataset_id,
        table_name, description, and schema fields.
    """
    parent = f"projects/{project_id}/locations/{location}/lakes/{lake_id}/zones/{zone_id}"

    try:
        entities = metadata_client.list_entities(parent=parent)
    except Exception as e:
        print(f"Error listing entities: {e}")
        return pd.DataFrame()

    entity_data = []

    for entity in entities:
        # Only process BIGQUERY tables
        if entity.system != dataplex_v1.StorageSystem.BIGQUERY:
            continue

        # Parse the data_path to extract project_id, dataset_id, table_name
        # Format: projects/{project}/datasets/{dataset}/tables/{table}
        if entity.data_path:
            parts = entity.data_path.split("/")
            if len(parts) >= 6:
                bq_project = parts[1]
                bq_dataset = parts[3]
                bq_table = parts[5]

                # Extract schema information
                schema_fields = []
                if entity.schema and entity.schema.fields:
                    schema_fields = [
                        {
                            "column_name": field.name,
                            "data_type": field.type_.name if field.type_ else "STRING",
                            "mode": field.mode.name if field.mode else "NULLABLE",
                            "description": field.description or "",
                        }
                        for field in entity.schema.fields
                    ]

                entity_data.append({
                    "project_id": bq_project,
                    "dataset_id": bq_dataset,
                    "table_name": bq_table,
                    "description": entity.description or "",
                    "entity_id": entity.id,
                    "schema_fields": schema_fields,
                    "create_time": entity.create_time,
                    "update_time": entity.update_time,
                })

    return pd.DataFrame(entity_data)


def extract_all_columns_from_entities(entities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Expand schema fields from entities into a columns DataFrame.

    Parameters
    ----------
    entities_df: pd.DataFrame
        DataFrame with entity information including schema_fields column.

    Returns
    -------
    pd.DataFrame
        A DataFrame with one row per column, including project_id, dataset_id,
        table_name, column_name, data_type, mode (nullable), and description.
    """
    if entities_df.empty:
        return pd.DataFrame()

    columns_data = []

    for _, entity_row in entities_df.iterrows():
        project_id = entity_row["project_id"]
        dataset_id = entity_row["dataset_id"]
        table_name = entity_row["table_name"]

        for field in entity_row["schema_fields"]:
            columns_data.append({
                "project_id": project_id,
                "dataset_id": dataset_id,
                "table_name": table_name,
                "column_name": field["column_name"],
                "data_type": field["data_type"],
                "mode": field["mode"],
                "description": field["description"],
            })

    return pd.DataFrame(columns_data)


def extract_unique_databases(entities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract unique database (project) information from entities.

    Parameters
    ----------
    entities_df: pd.DataFrame
        DataFrame with entity information.

    Returns
    -------
    pd.DataFrame
        A DataFrame with unique project_id values.
    """
    if entities_df.empty:
        return pd.DataFrame()

    unique_projects = entities_df[["project_id"]].drop_duplicates()
    return unique_projects


def extract_unique_schemas(entities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract unique schema (dataset) information from entities.

    Parameters
    ----------
    entities_df: pd.DataFrame
        DataFrame with entity information.

    Returns
    -------
    pd.DataFrame
        A DataFrame with unique project_id and dataset_id combinations.
    """
    if entities_df.empty:
        return pd.DataFrame()

    unique_datasets = entities_df[["project_id", "dataset_id"]].drop_duplicates()
    # Add empty description for schemas (Dataplex doesn't provide dataset-level descriptions)
    unique_datasets["description"] = ""
    return unique_datasets
