from pathlib import Path

import pytest


@pytest.fixture
def csv_dir(tmp_path) -> Path:
    """An empty temporary directory that satisfies the csv_directory existence check."""
    return tmp_path


@pytest.fixture
def csv_dir_with_files(tmp_path) -> Path:
    """A temporary directory with a minimal set of valid CSV files."""
    (tmp_path / "database_info.csv").write_text(
        "database_id,name,description\nmy_db,My Database,A test database\n"
    )
    (tmp_path / "schema_info.csv").write_text(
        "database_id,schema_id,name,description\n"
        "my_db,sales,Sales,Sales schema\n"
        "my_db,analytics,Analytics,Analytics schema\n"
    )
    (tmp_path / "table_info.csv").write_text(
        "database_id,schema_id,table_name,description\n"
        "my_db,sales,orders,Order transactions\n"
        "my_db,sales,customers,Customer data\n"
    )
    (tmp_path / "column_info.csv").write_text(
        "database_id,schema_id,table_name,column_name,data_type,is_nullable,is_primary_key,is_foreign_key\n"
        "my_db,sales,orders,order_id,STRING,false,true,false\n"
        "my_db,sales,orders,customer_id,STRING,false,false,true\n"
        "my_db,sales,customers,customer_id,STRING,false,true,false\n"
    )
    (tmp_path / "column_references_info.csv").write_text(
        "source_database_id,source_schema_id,source_table_name,source_column_name,"
        "target_database_id,target_schema_id,target_table_name,target_column_name,criteria\n"
        "my_db,sales,orders,customer_id,my_db,sales,customers,customer_id,"
        "orders.customer_id = customers.customer_id\n"
    )
    return tmp_path
