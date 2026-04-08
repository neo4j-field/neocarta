
from pydantic import BaseModel, Field


class JoinContext(BaseModel):
    """Model representing context for a join."""

    table_name: str = Field(..., description="The name of the table")
    column_names: list[str] = Field(..., description="The names of the columns a table joins on")


# class ReferenceContext(BaseModel):
#     """Model representing context for a column referencing a column in a different table"""

#     table_name: str = Field(..., description="The name of the table")
#     column_name: str = Field(..., description="The name of the column")


class ColumnContext(BaseModel):
    """Model representing context for a column."""

    column_name: str = Field(..., description="The name of the column")
    column_description: str = Field(..., description="The description of the column")
    data_type: str = Field(..., description="The data type of the column")
    nullable: bool | None = Field(default=None, description="Whether the column can be null")
    examples: list[str] | None = Field(default=None, description="Example values for the column")
    key_type: str | None = Field(default=None, description="The key type of the column")
    references: list[str] = Field(
        default=[],
        description="The referenced columns from another table of the column. Have format of 'table_name.column_name'",
    )


class TableContext(BaseModel):
    """Model representing context for a table."""

    table_name: str = Field(..., description="The name of the table")
    table_description: str = Field(..., description="The description of the table")
    database_name: str = Field(..., description="The name of the database")
    schema_name: str = Field(..., description="The name of the schema")
    columns: list[ColumnContext] = Field(..., description="The relevant columns of the table")
    joins: list[JoinContext] = Field(
        default=[], description="The relevant join tables of the table"
    )


class ListSchemaRecord(BaseModel):
    """Model representing a record for a schema in the list_schemas tool."""

    schema_name: str = Field(..., description="The name of the schema")
    database_name: str = Field(..., description="The name of the database")


class ListTablesBySchemaRecord(BaseModel):
    """Model representing a record for a table in the list_tables_by_schema tool."""

    schema_name: str = Field(..., description="The name of the schema")
    table_names: list[str] = Field(..., description="The names of the tables in the schema")
