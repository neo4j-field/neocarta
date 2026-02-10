"""Extract metadata from GCP Dataplex."""

from google.cloud import dataplex_v1
import pandas as pd
from typing import Optional


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
        A DataFrame with one row per column. Columns: project_id, dataset_id,
        lake_id, zone_id, entity_description, entity_name, entity_id,
        column_name, column_id, data_type, nullable, description.
    """
    parent = f"projects/{project_id}/locations/{location}/lakes/{lake_id}/zones/{zone_id}"

    try:
        entities = metadata_client.list_entities(parent=parent)
    except Exception as e:
        print(f"Error listing entities: {e}")
        return pd.DataFrame()

    entity_data = []

    for entity in entities:
        request = dataplex_v1.types.GetEntityRequest(
            name=entity.name,
            view=dataplex_v1.types.GetEntityRequest.EntityView.SCHEMA,
        )

        bq_project, bq_dataset, bq_table = "UNKNOWN", "UNKNOWN", "UNKNOWN"
        # Format: projects/{project}/datasets/{dataset}/tables/{table}
        if entity.data_path:
            parts = entity.data_path.split("/")
            if len(parts) >= 6:
                bq_project = parts[1]
                bq_dataset = parts[3]
                bq_table = parts[5]

        entity_info = metadata_client.get_entity(request=request)
        if entity_info.schema and entity_info.schema.fields:
            entity_id = f"{bq_project}.{bq_dataset}.{bq_table}"
            for field in entity_info.schema.fields:
                entity_data.append(
                    {
                        "project_id": bq_project,
                        "dataset_id": bq_dataset,
                        "lake_id": lake_id,
                        "zone_id": zone_id,
                        "entity_description": entity_info.description or "",
                        "entity_name": bq_table,
                        "entity_id": entity_id,
                        "column_name": field.name,
                        "column_id": f"{entity_id}.{field.name}",
                        "data_type": field.type_.name if field.type_ else "STRING",
                        "nullable": field.mode.name == "NULLABLE",
                        "description": field.description or "",
                    }
                )

    return pd.DataFrame(entity_data)

def _parse_glossary_category_id(term_parent: str) -> Optional[str]:
    """
    Parse a Dataplex term parent to a category ID
    (projects/{project}/locations/{location}/glossaries/{glossary}/categories/{category}).
    """
    parts = term_parent.split("/")
    if parts[-2] == "categories":
        return parts[-1]
    return None
    

def extract_glossary_info(
    glossary_client: dataplex_v1.BusinessGlossaryServiceClient,
    project_id: str,
    location: str,
) -> pd.DataFrame:
    """
    Extract all glossary terms from all glossaries in the given location.

    Parameters
    ----------
    glossary_client: dataplex_v1.BusinessGlossaryServiceClient
        The Dataplex Business Glossary client.
    project_id: str
        The GCP project ID.
    location: str
        The location (e.g., 'us-central1').

    Returns
    -------
    pd.DataFrame
        A DataFrame with one row per term. Columns: term_id, term_name,
        term_description, glossary_id, glossary_name.
    """
    parent = f"projects/{project_id}/locations/{location}"

    terms_data = []

    try:
        glossaries = glossary_client.list_glossaries(parent=parent)
    except Exception as e:
        print(f"Error listing glossaries: {e}")
        return pd.DataFrame()

    for glossary in glossaries:
        glossary_id = glossary.name.split("/")[-1]
        glossary_name = glossary.display_name or glossary_id

        try:
            terms = glossary_client.list_glossary_terms(parent=glossary.name)
        except Exception as e:
            print(f"Error listing terms for glossary {glossary_id}: {e}")
            continue

        for term in terms:
            terms_data.append(
                {
                    "term_id": term.name,
                    "term_name": term.display_name or term.name.split("/")[-1],
                    "term_description": term.description or "",
                    "glossary_id": glossary_id,
                    "glossary_name": glossary_name,
                    "term_parent": term.parent,
                    "category_id": _parse_glossary_category_id(term.parent),
                }
            )

    return pd.DataFrame(terms_data)


def _parse_entry_name_to_id(entry_name: str) -> Optional[str]:
    """
    Parse a Dataplex entry name to a table or column ID
    (project.dataset.table or project.dataset.table.column).

    BigQuery entries in the @bigquery entry group have names like:
    projects/{project}/locations/{location}/entryGroups/@bigquery/entries/{encoded}

    Where {encoded} encodes the BigQuery path, e.g.:
    bigquery.googleapis.com/projects/{p}/datasets/{d}/tables/{t}
    """
    try:
        parts = entry_name.split("/entries/")
        if len(parts) != 2:
            return None

        encoded_id = parts[1]

        if "bigquery.googleapis.com" not in encoded_id:
            return None

        bq_path = encoded_id.replace("bigquery.googleapis.com/", "")
        path_parts = bq_path.split("/")

        # Expect: ["projects", "{p}", "datasets", "{d}", "tables", "{t}"]
        if len(path_parts) < 6:
            return None

        project = path_parts[1]
        dataset = path_parts[3]
        table = path_parts[5]

        # Column level: .../tables/{t}/fields/{col}
        if len(path_parts) >= 8 and path_parts[6] == "fields":
            column = path_parts[7]
            return f"{project}.{dataset}.{table}.{column}"

        return f"{project}.{dataset}.{table}"
    except Exception:
        return None


def extract_entry_links(
    catalog_client: dataplex_v1.CatalogServiceClient,
    project_id: str,
    location: str,
) -> pd.DataFrame:
    """
    Extract EntryLinks that associate glossary terms with data entries
    (tables or columns).

    Parameters
    ----------
    catalog_client: dataplex_v1.CatalogServiceClient
        The Dataplex Catalog client.
    project_id: str
        The GCP project ID.
    location: str
        The location (e.g., 'us-central1').

    Returns
    -------
    pd.DataFrame
        A DataFrame with columns: entry_id (table or column ID), term_id
        (full glossary term resource name). Empty if no links are found.
    """
    DEFINITION_LINK_TYPE = (
        "projects/dataplex-types/locations/global/entryLinkTypes/definition"
    )
    parent = f"projects/{project_id}/locations/{location}/entryGroups/@bigquery"

    links_data = []

    try:
        entry_links = catalog_client.list_entry_links(parent=parent)
        for link in entry_links:
            if link.entry_link_type != DEFINITION_LINK_TYPE:
                continue

            term_id = None
            entry_id = None

            for entry_ref in [link.source_entry, link.target_entry]:
                name = entry_ref.name
                if "/glossaries/" in name and "/terms/" in name:
                    term_id = name
                else:
                    entry_id = _parse_entry_name_to_id(name)

            if term_id and entry_id:
                links_data.append({"entry_id": entry_id, "term_id": term_id})

    except Exception as e:
        print(f"Note: Could not extract entry links from @bigquery entry group: {e}")

    return (
        pd.DataFrame(links_data)
        if links_data
        else pd.DataFrame(columns=["entry_id", "term_id"])
    )
