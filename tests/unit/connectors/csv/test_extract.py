import pytest

from semantic_graph.connectors.csv.extract import NODE_ENTITIES, REL_ENTITIES, CSVExtractor

# ---------------------------------------------------------------------------
# Fix #1 — csv_directory validation
# ---------------------------------------------------------------------------


class TestCsvDirectoryValidation:
    def test_nonexistent_directory_raises(self, tmp_path):
        missing = tmp_path / "does_not_exist"
        with pytest.raises(ValueError, match="does not exist"):
            CSVExtractor(str(missing))

    def test_file_path_raises(self, tmp_path):
        f = tmp_path / "not_a_dir.csv"
        f.write_text("a,b\n1,2\n")
        with pytest.raises(ValueError, match="not a directory"):
            CSVExtractor(str(f))

    def test_valid_directory_does_not_raise(self, csv_dir):
        extractor = CSVExtractor(str(csv_dir))
        assert extractor.csv_directory == csv_dir

    def test_path_object_accepted(self, csv_dir):
        extractor = CSVExtractor(csv_dir)  # Path, not str
        assert extractor.csv_directory == csv_dir


# ---------------------------------------------------------------------------
# Fix #2 — include_nodes / include_relationships validation in extract_all
# ---------------------------------------------------------------------------


class TestIncludeValidation:
    def test_invalid_include_nodes_raises(self, csv_dir):
        extractor = CSVExtractor(str(csv_dir))
        with pytest.raises(ValueError, match="Unknown node types"):
            extractor.extract_all(include_nodes=["databse"])  # typo

    def test_invalid_include_relationships_raises(self, csv_dir):
        extractor = CSVExtractor(str(csv_dir))
        with pytest.raises(ValueError, match="Unknown relationship types"):
            extractor.extract_all(include_relationships=["has_schema_rel"])  # wrong name

    def test_multiple_invalid_include_nodes_raises(self, csv_dir):
        extractor = CSVExtractor(str(csv_dir))
        with pytest.raises(ValueError, match="Unknown node types"):
            extractor.extract_all(include_nodes=["foo", "bar", "database"])

    def test_multiple_invalid_include_relationships_raises(self, csv_dir):
        extractor = CSVExtractor(str(csv_dir))
        with pytest.raises(ValueError, match="Unknown relationship types"):
            extractor.extract_all(include_relationships=["foo", "has_schema"])

    def test_error_message_lists_invalid_values(self, csv_dir):
        extractor = CSVExtractor(str(csv_dir))
        with pytest.raises(ValueError, match="typo_node"):
            extractor.extract_all(include_nodes=["typo_node"])

    def test_error_message_lists_valid_values(self, csv_dir):
        extractor = CSVExtractor(str(csv_dir))
        with pytest.raises(ValueError) as exc_info:
            extractor.extract_all(include_nodes=["bad"])
        assert "database" in str(exc_info.value)

    def test_all_valid_node_types_accepted(self, csv_dir):
        extractor = CSVExtractor(str(csv_dir))
        extractor.extract_all(include_nodes=list(NODE_ENTITIES.keys()))
        # No error; missing files are silently skipped

    def test_all_valid_relationship_types_accepted(self, csv_dir):
        extractor = CSVExtractor(str(csv_dir))
        extractor.extract_all(include_relationships=list(REL_ENTITIES.keys()))

    def test_none_include_nodes_extracts_all(self, csv_dir):
        extractor = CSVExtractor(str(csv_dir))
        extractor.extract_all(include_nodes=None, include_relationships=None)
        # No error; empty dir simply produces no cached data

    def test_empty_include_nodes_list_extracts_nothing(self, csv_dir):
        """An empty list is valid but results in no files being read."""
        extractor = CSVExtractor(str(csv_dir))
        extractor.extract_all(include_nodes=[], include_relationships=[])
        assert extractor.database_info.empty
        assert extractor.schema_info.empty

    def test_selective_extract_only_reads_needed_files(self, csv_dir_with_files):
        """Requesting only 'database' does not populate other caches."""
        extractor = CSVExtractor(str(csv_dir_with_files))
        extractor.extract_all(include_nodes=["database"])
        assert not extractor.database_info.empty
        assert extractor.schema_info.empty  # not requested
        assert extractor.table_info.empty  # not requested

    def test_relationship_include_reads_shared_csv(self, csv_dir_with_files):
        """has_schema reuses schema_info.csv, so schema_info cache is populated."""
        extractor = CSVExtractor(str(csv_dir_with_files))
        extractor.extract_all(include_relationships=["has_schema"])
        assert not extractor.schema_info.empty

    def test_references_include_reads_column_references_csv(self, csv_dir_with_files):
        extractor = CSVExtractor(str(csv_dir_with_files))
        extractor.extract_all(include_relationships=["references"])
        assert not extractor.column_references_info.empty
        assert extractor.schema_info.empty  # not requested


# ---------------------------------------------------------------------------
# Core extraction behaviour
# ---------------------------------------------------------------------------


class TestExtraction:
    def test_extract_database_info_row_count(self, csv_dir_with_files):
        extractor = CSVExtractor(str(csv_dir_with_files))
        df = extractor.extract_database_info()
        assert df is not None
        assert len(df) == 1
        assert extractor.database_info["database_id"].iloc[0] == "my_db"

    def test_extract_schema_info_row_count(self, csv_dir_with_files):
        extractor = CSVExtractor(str(csv_dir_with_files))
        df = extractor.extract_schema_info()
        assert df is not None
        assert len(df) == 2

    def test_extract_missing_file_returns_none(self, csv_dir):
        """A file that doesn't exist returns None and leaves the cache empty."""
        extractor = CSVExtractor(str(csv_dir))
        df = extractor.extract_database_info()
        assert df is None
        assert extractor.database_info.empty

    def test_extract_missing_required_column_raises(self, tmp_path):
        """A file present but missing required columns raises ValueError."""
        (tmp_path / "schema_info.csv").write_text(
            "schema_id,name\nsales,Sales\n"  # missing database_id
        )
        extractor = CSVExtractor(str(tmp_path))
        with pytest.raises(ValueError, match="missing required columns"):
            extractor.extract_schema_info()

    def test_null_string_values_normalised(self, tmp_path):
        """'NULL', 'null', and 'NaN' string values in optional columns are treated as null."""
        import pandas as pd

        (tmp_path / "database_info.csv").write_text(
            "database_id,description\ndb1,NULL\ndb2,null\ndb3,NaN\ndb4,real description\n"
        )
        extractor = CSVExtractor(str(tmp_path))
        df = extractor.extract_database_info()
        assert pd.isna(df["description"].iloc[0])
        assert pd.isna(df["description"].iloc[1])
        assert pd.isna(df["description"].iloc[2])
        assert df["description"].iloc[3] == "real description"
