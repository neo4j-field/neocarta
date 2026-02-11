"""Extract metadata from GCP Dataplex."""

from google.cloud import dataplex_v1
import pandas as pd
from typing import Optional
from connectors.dataplex.models import BigQueryMetadataInfoResponse, GlossaryInfoResponse


def extract_bigquery_metadata_info(
    catalog_client: dataplex_v1.CatalogServiceClient,
    project_id: str,
    project_number: str,
    dataplex_location: str,
    dataset_id: str,
    table_id: str,
) -> pd.DataFrame:
    """
    Extract full table metadata from Dataplex Universal Catalog for a BigQuery table.
    Returns project, dataset, table, schema, and service info.

    Parameters
    ----------
    catalog_client: dataplex_v1.CatalogServiceClient
        The Dataplex Catalog client.
    project_id: str
        The GCP project ID.
    project_number: str
        The GCP project number.
    dataplex_location: str
        The Dataplex location.
    dataset_id: str
        The BigQuery dataset ID.
    table_id: str
        The BigQuery table ID.

    Returns
    -------
    pd.DataFrame
        A Pandas DataFrame with one row per column.
        Has columns: project_id, project_number, dataset_id, table_id, table_display_name, table_description, column_name, column_data_type, column_metadata_type, column_mode, column_description, service, platform, location, resource_name, fully_qualified_name, parent_entry, entry_type.
    """

    table_entry_name = f"projects/{project_number}/locations/{dataplex_location}/entryGroups/@bigquery/entries/bigquery.googleapis.com/projects/{project_id}/datasets/{dataset_id}/tables/{table_id}"


    request = dataplex_v1.LookupEntryRequest(
        name=f"projects/{project_id}/locations/{dataplex_location}",
        entry=table_entry_name,
        view=dataplex_v1.EntryView.FULL,
    )
    entry = catalog_client.lookup_entry(request=request)

    # Parse FQN: "bigquery:ai-field-alex-g.demo_ecommerce.customers"
    fqn = entry.fully_qualified_name

    # Entry source metadata
    src = entry.entry_source

    # Storage aspect for resource name
    storage = {}
    for key, aspect in entry.aspects.items():
        if "storage" in key and aspect.data:
            storage = dict(aspect.data)
        
    # Schema fields
    schema_fields = []
    for key, aspect in entry.aspects.items():
        print(key)
        if "schema" in key and aspect.data:
            print(dict(aspect.data))
            for field in aspect.data["fields"]:
                print(dict(field))
                schema_fields.append(dict(field))

    records = []
    for col in schema_fields:
        records.append(BigQueryMetadataInfoResponse(
            project_id=project_id,
            project_number=project_number,
            dataset_id=dataset_id,
            table_id=table_id,
            table_display_name=src.display_name,
            table_description=src.description,
            column_name=col.get("name"),
            column_data_type=col.get("dataType"),
            column_metadata_type=col.get("metadataType"),
            column_mode=col.get("mode"),
            column_description=col.get("description", ""),
            service=src.system,
            platform=src.platform,
            location=src.location,
            resource_name=storage.get("resourceName", ""),
            fully_qualified_name=fqn,
            parent_entry=entry.parent_entry,
            entry_type=entry.entry_type,
        ))

    return pd.DataFrame(records)

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
        A Pandas DataFrame with one row per term.
        Has columns: term_id, term_name, term_description, glossary_id, glossary_name, term_parent, category_id.
    """
    parent = f"projects/{project_id}/locations/{location}"

    records = []

    try:
        glossaries = glossary_client.list_glossaries(parent=parent)
    except Exception as e:
        print(f"Error listing glossaries: {e}")
        return []

    for glossary in glossaries:
        glossary_id = glossary.name.split("/")[-1]
        glossary_name = glossary.display_name or glossary_id

        try:
            terms = glossary_client.list_glossary_terms(parent=glossary.name)
        except Exception as e:
            print(f"Error listing terms for glossary {glossary_id}: {e}")
            continue

        for term in terms:
            print(term)
            records.append(
                GlossaryInfoResponse(
                    term_id=term.name,
                    term_name=term.display_name or term.name.split("/")[-1],
                    term_description=term.description or "",
                    glossary_id=glossary_id,
                    glossary_name=glossary_name,
                    term_parent=term.parent,
                    category_id=_parse_glossary_category_id(term.parent),
                )
            )

    return pd.DataFrame(records)


