from neo4j import Driver

from connectors.query_log.extract import QueryLogExtractor
from connectors.query_log.transform import QueryLogTransformer
from connectors.load import Neo4jLoader

class QueryLogWorkflow:
    """
    A workflow for extracting, transforming, and loading query log data into Neo4j.
    """

    def __init__(self, neo4j_driver: Driver, database_name: str = "neo4j"):
        """
        Initialize the query log workflow.
        """

        self.neo4j_driver = neo4j_driver
        self.database_name = database_name

        self.extractor = QueryLogExtractor()
        self.transformer = QueryLogTransformer()
        self.loader = Neo4jLoader(neo4j_driver, database_name)

    def extract_metadata(self, query_log_file: str, source: str = "bigquery") -> None:
        """
        Extract and cache metadata from a query log file.

        Parameters
        ----------
        query_log_file: str
            The path to the query log file.
        source: str = "bigquery"
            The source of the query log file.

        Returns
        -------
        None
            The metadata is extracted and cached.
        """
        self.extractor.extract_info_from_query_log_json(query_log_file, source, cache=True)
    
    def transform_metadata(self) -> None:
        """
        Transform and cache metadata from a query log file.

        Returns
        -------
        None
            The metadata is transformed and cached.
        """

        # transform nodes
        self.transformer.transform_to_database_nodes(self.extractor.database_info, cache=True)
        self.transformer.transform_to_schema_nodes(self.extractor.schema_info, cache=True)
        self.transformer.transform_to_table_nodes(self.extractor.table_info, cache=True)
        self.transformer.transform_to_column_nodes(self.extractor.column_info, cache=True)
        self.transformer.transform_to_query_nodes(self.extractor.query_info, cache=True)

        # transform relationships
        self.transformer.transform_to_has_schema_relationships(self.extractor.schema_info, cache=True)
        self.transformer.transform_to_has_table_relationships(self.extractor.table_info, cache=True)
        self.transformer.transform_to_has_column_relationships(self.extractor.column_info, cache=True)
        self.transformer.transform_to_references_relationships(self.extractor.column_references_info, cache=True)
        self.transformer.transform_to_uses_table_relationships(self.extractor.table_info, cache=True)
        self.transformer.transform_to_uses_column_relationships(self.extractor.column_info, cache=True)
    
    def load_metadata(self) -> None:
        """
        Load metadata into Neo4j.

        Returns
        -------
        None
            The metadata is loaded into Neo4j.
        """
        
        # load nodes
        print(self.loader.load_database_nodes(self.transformer.database_nodes))
        print(self.loader.load_schema_nodes(self.transformer.schema_nodes))
        print(self.loader.load_table_nodes(self.transformer.table_nodes))
        print(self.loader.load_column_nodes(self.transformer.column_nodes))
        print(self.loader.load_query_nodes(self.transformer.query_nodes))

        # load relationships
        print(self.loader.load_has_schema_relationships(self.transformer.has_schema_relationships))
        print(self.loader.load_has_table_relationships(self.transformer.has_table_relationships))
        print(self.loader.load_has_column_relationships(self.transformer.has_column_relationships))
        print(self.loader.load_references_relationships(self.transformer.references_relationships))
        print(self.loader.load_uses_table_relationships(self.transformer.uses_table_relationships))
        print(self.loader.load_uses_column_relationships(self.transformer.uses_column_relationships))

    def run(self, query_log_file: str, source: str = "bigquery") -> None:
        """
        Run the query log workflow.

        Parameters
        ----------
        query_log_file: str
            The path to the query log file.
        source: str = "bigquery"
            The source of the query log file.
        
        Returns
        -------
        None
            The metadata is extracted, transformed, and loaded into Neo4j.
        """
        print("Extracting metadata from query log...")
        self.extract_metadata(query_log_file, source)
        print("Transforming metadata from query log...")
        self.transform_metadata()
        print("Loading metadata into Neo4j...")
        self.load_metadata()
        print("Query log workflow completed successfully!")