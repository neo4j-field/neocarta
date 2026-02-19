"""Extract metadata from GCP Dataplex."""

from google.cloud import dataplex_v1
import pandas as pd
from typing import Optional
from connectors.dataplex.models import BigQueryMetadataInfoResponse, GlossaryInfoResponse, DataplexExtractorCache


class DataplexExtractor:
    """
    Extractor class for Dataplex.
    """

    def __init__(self, 
        catalog_client: dataplex_v1.CatalogServiceClient,
        glossary_client: dataplex_v1.BusinessGlossaryServiceClient,
        project_id: str,
        project_number: str,
        dataplex_location: str,
        dataset_id: Optional[str] = None,
    ):
        """
        Initialize the Dataplex extractor.
        
        Parameters
        ----------
        catalog_client: dataplex_v1.CatalogServiceClient
            The Dataplex Catalog client.
        glossary_client: dataplex_v1.BusinessGlossaryServiceClient
            The Dataplex Business Glossary client.
        project_id: str
            The GCP project ID. If not provided, will use the project ID from the client.
        project_number: str
            The GCP project number.
        dataset_id: Optional[str] = None
            The BigQuery dataset ID.
        dataplex_location: str
            The Dataplex location (e.g. 'us-central1' or 'us').
        """

        self.catalog_client = catalog_client
        self.glossary_client = glossary_client
        self.project_id = project_id
        self.project_number = project_number
        self.dataset_id = dataset_id
        self.dataplex_location = dataplex_location

        self._cache: DataplexExtractorCache = DataplexExtractorCache()

    @property
    def database_info(self) -> pd.DataFrame:
        """
        Get the database information DataFrame.
        """
        cols = ["project_id", "service", "platform"]
        return self._cache.get("table_info", pd.DataFrame(columns=cols)).drop_duplicates(subset=["project_id"])[cols]

    @property
    def schema_info(self) -> pd.DataFrame:
        """
        Get the schema information DataFrame.
        """
        cols = ["project_id", "dataset_id"]
        return self._cache.get("table_info", pd.DataFrame(columns=cols)).drop_duplicates(subset=["project_id", "dataset_id"])[cols]

    @property
    def table_info(self) -> pd.DataFrame:
        """
        Get the table information DataFrame.
        """
        cols = ["project_id", "dataset_id", "table_id", "table_display_name", "table_description"]
        return self._cache.get("table_info", pd.DataFrame(columns=cols)).drop_duplicates(subset=["project_id", "dataset_id", "table_id"])[cols]
    
    @property
    def column_info(self) -> pd.DataFrame:
        """
        Get the column information DataFrame.
        """
        cols = ["project_id", "dataset_id", "table_id", "column_name", "column_description", "column_data_type", "column_mode"]
        return self._cache.get("table_info", pd.DataFrame(columns=cols)).drop_duplicates(subset=["project_id", "dataset_id", "table_id", "column_name"])[cols]


    @property
    def glossary_info(self) -> pd.DataFrame:
        """
        Get the glossary information DataFrame.
        """
        cols = ["glossary_id", "glossary_name"]
        return self._cache.get("glossary_info", pd.DataFrame(columns=cols)).drop_duplicates(subset=["glossary_id"])[cols]
    
    @property
    def category_info(self) -> pd.DataFrame:
        """
        Get the category information DataFrame.
        """
        cols = ["glossary_id", "category_id"]
        return self._cache.get("glossary_info", pd.DataFrame(columns=cols)).drop_duplicates(subset=["glossary_id", "category_id"])[cols]
    
    @property
    def business_term_info(self) -> pd.DataFrame:
        """
        Get the business term information DataFrame.
        """
        cols = ["glossary_id", "category_id", "term_id", "term_name", "term_description"]
        return self._cache.get("glossary_info", pd.DataFrame(columns=cols)).drop_duplicates(subset=["glossary_id", "category_id", "term_id"])[cols]
    
    def _get_dataset_id(self, dataset_id: Optional[str] = None) -> str:
        """
        Get the dataset ID. If not provided, will use default instance `dataset_id`.

        Parameters
        ----------
        dataset_id: Optional[str] = None
            The dataset ID. If not provided, will use default instance `dataset_id`.
            
        Returns
        -------
        str
            The dataset ID.
        """
        dataset_id = dataset_id or self.dataset_id

        assert dataset_id is not None, "Dataset ID is required in either constructor as `dataset_id` or as an argument to `extract_schema_info` method."

        return dataset_id

    def _extract_bigquery_dataset_table_ids(
        self,
        dataset_id: Optional[str] = None,
    ) -> list[str]:
        """
        Discover all BigQuery table IDs in a dataset via Dataplex Universal Catalog.

        Lists entries in the managed ``@bigquery`` entry group and filters for
        entries whose name contains the target dataset's table path.

        Parameters
        ----------
        dataset_id: Optional[str] = None
            The BigQuery dataset ID. If not provided, will use default instance `dataset_id`.
       
        Returns
        -------
        list[str]
            A list of table IDs within the dataset.
        """

        dataset_id = self._get_dataset_id(dataset_id)

        entry_group = (
            f"projects/{self.project_number}/locations/{self.dataplex_location}"
            f"/entryGroups/@bigquery"
        )

        # Table entries have names of the form:
        # .../@bigquery/entries/bigquery.googleapis.com/projects/{project_id}/datasets/{dataset_id}/tables/{table_id}
        table_path_segment = (
            f"bigquery.googleapis.com/projects/{self.project_id}"
            f"/datasets/{dataset_id}/tables/"
        )

        table_ids = []
        for entry in self.catalog_client.list_entries(parent=entry_group):
            if table_path_segment in entry.name:
                table_ids.append(entry.name.split("/tables/")[-1])
        
        return table_ids


    def extract_bigquery_info_for_table(
        self,
        table_id: str,
        dataset_id: Optional[str] = None,
        cache: bool = False
    ) -> pd.DataFrame:
        """
        Extract full table metadata from Dataplex Universal Catalog for a BigQuery table.
        Returns project, dataset, table, schema, and service info.

        Parameters
        ----------
        table_id: str
            The BigQuery table ID.
        dataset_id: Optional[str] = None
            The BigQuery dataset ID. If not provided, will use default instance `dataset_id`.
        cache: bool = False
            Whether to cache the extract. If True, will cache the table information in the instance.

        Returns
        -------
        pd.DataFrame
            A Pandas DataFrame with one row per column.
            Has columns: project_id, project_number, dataset_id, table_id, table_display_name, table_description, column_name, column_data_type, column_metadata_type, column_mode, column_description, service, platform, location, resource_name, fully_qualified_name, parent_entry, entry_type.
        """

        dataset_id = self._get_dataset_id(dataset_id)

        table_entry_name = f"projects/{self.project_number}/locations/{self.dataplex_location}/entryGroups/@bigquery/entries/bigquery.googleapis.com/projects/{self.project_id}/datasets/{dataset_id}/tables/{table_id}"


        request = dataplex_v1.LookupEntryRequest(
            name=f"projects/{self.project_id}/locations/{self.dataplex_location}",
            entry=table_entry_name,
            view=dataplex_v1.EntryView.FULL,
        )
        entry = self.catalog_client.lookup_entry(request=request)

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
            if "schema" in key and aspect.data:
                for field in aspect.data["fields"]:
                    schema_fields.append(dict(field))

        records = []
        for col in schema_fields:
            records.append(BigQueryMetadataInfoResponse(
                project_id=self.project_id,
                project_number=self.project_number,
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

        # TODO: Handle caching duplicate table information if method run multiple times for same table.
        df = pd.DataFrame(records)
        if cache:
            self._cache["table_info"] = pd.concat([self._cache.get("table_info", pd.DataFrame()), df], ignore_index=True)

        return df

    def extract_bigquery_info_for_all_tables(
        self,
        dataset_id: Optional[str] = None,
        cache: bool = False
    ) -> pd.DataFrame:
        """
        Extract full table metadata from Dataplex Universal Catalog for all BigQuery tables in a dataset.

        Parameters
        ----------
        dataset_id: Optional[str] = None
            The BigQuery dataset ID. If not provided, will use default instance `dataset_id`.
        cache: bool = False
            Whether to cache the extract. If True, will cache the table information in the instance.

        Returns
        -------
        pd.DataFrame
            A Pandas DataFrame with one row per table column.
        """
        
        dataset_id = self._get_dataset_id(dataset_id)

        table_ids = self._extract_bigquery_dataset_table_ids(dataset_id)

        df = pd.DataFrame()
        for table_id in table_ids:
            df = pd.concat([df, self.extract_bigquery_info_for_table(table_id, dataset_id, cache=False)], ignore_index=True)
        
        if cache:
            self._cache["table_info"] = pd.concat([self._cache.get("table_info", pd.DataFrame()), df], ignore_index=True)

        return df

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
        self, cache: bool = False
    ) -> pd.DataFrame:
        """
        Extract all glossary terms from all glossaries in the given location.

        Parameters
        ----------
        cache: bool = False
            Whether to cache the extract. If True, will cache the glossary information in the instance.

        Returns
        -------
        pd.DataFrame
            A Pandas DataFrame with one row per term.
            Has columns: term_id, term_name, term_description, glossary_id, glossary_name, term_parent, category_id.
        """
        parent = f"projects/{self.project_id}/locations/{self.dataplex_location}"

        records = []

        try:
            glossaries = self.glossary_client.list_glossaries(parent=parent)
        except Exception as e:
            print(f"Error listing glossaries: {e}")
            return []

        for glossary in glossaries:
            glossary_id = glossary.name.split("/")[-1]
            glossary_name = glossary.display_name or glossary_id

            try:
                terms = self.glossary_client.list_glossary_terms(parent=glossary.name)
            except Exception as e:
                print(f"Error listing terms for glossary {glossary_id}: {e}")
                continue

            for term in terms:
                records.append(
                    GlossaryInfoResponse(
                        term_id=term.name,
                        term_name=term.display_name or term.name.split("/")[-1],
                        term_description=term.description or "",
                        glossary_id=glossary_id,
                        glossary_name=glossary_name,
                        term_parent=term.parent,
                        category_id=term.parent,
                    )
                )

        # TODO: Handle caching duplicate glossary information if method run multiple times for same glossary.
        df = pd.DataFrame(records)
        if cache:
            self._cache["glossary_info"] = pd.concat([self._cache.get("glossary_info", pd.DataFrame()), df], ignore_index=True)

        return df


