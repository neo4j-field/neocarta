"""Extract metadata from GCP Dataplex."""

from google.cloud import dataplex_v1
import pandas as pd


def extract_entity_info(
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
    # first get all entities (tables) in the zone
    parent = f"projects/{project_id}/locations/{location}/lakes/{lake_id}/zones/{zone_id}"

    try:
        entities = metadata_client.list_entities(parent=parent)
    except Exception as e:
        print(f"Error listing entities: {e}")
        return pd.DataFrame()

    entity_data = []

    for entity in entities:
        # Get specific entity schema information
        request = dataplex_v1.types.GetEntityRequest(
        name=entity.name,
        view=dataplex_v1.types.GetEntityRequest.EntityView.SCHEMA
    )
        # Parse the data_path to extract project_id, dataset_id, table_name
        bq_project, bq_dataset, bq_table = "UNKNOWN", "UNKNOWN", "UNKNOWN"
        # Format: projects/{project}/datasets/{dataset}/tables/{table}
        if entity.data_path:
            parts = entity.data_path.split("/")
            if len(parts) >= 6:
                bq_project = parts[1]
                bq_dataset = parts[3]
                bq_table = parts[5]
            

        entity_info = metadata_client.get_entity(request=request)
        # Extract schema information
        if entity_info.schema and entity_info.schema.fields:
            entity_id = f"{bq_project}.{bq_dataset}.{bq_table}"
            for field in entity_info.schema.fields:
                entity_data.append({
                    "project_id": bq_project,
                    "dataset_id": bq_dataset,
                    "lake_id": lake_id,
                    "zone_id": zone_id,
                    "entity_description": entity_info.description or "",
                    "entity_name": bq_table, # entity = table
                    "entity_id": entity_id,
                    "column_name": field.name,
                    "column_id": f"{entity_id}.{field.name}",
                    "data_type": field.type_.name if field.type_ else "STRING",
                    "nullable": True if field.mode.name == "NULLABLE" else False,
                    "description": field.description or "",
                })

    return pd.DataFrame(entity_data)
