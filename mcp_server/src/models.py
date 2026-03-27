from pydantic import BaseModel, Field
from typing import Optional


class JoinContext(BaseModel):
    """Model representing context for a join"""

    table_name: str = Field(..., description="The name of the table")
    column_names: list[str] = Field(
        ..., description="The names of the columns a table joins on"
    )


class ReferenceContext(BaseModel):
    """Model representing context for a column referencing a column in a different table"""

    table_name: str = Field(..., description="The name of the table")
    column_name: str = Field(..., description="The name of the column")


class ColumnContext(BaseModel):
    """Model representing context for a column"""

    column_name: str = Field(..., description="The name of the column")
    column_description: Optional[str] = Field(default=None, description="The description of the column")
    data_type: Optional[str] = Field(default=None, description="The data type of the column")
    nullable: Optional[bool] = Field(default=None, description="Whether the column can be null")
    examples: Optional[list[str]] = Field(
        default=None, description="Example values for the column"
    )
    key_type: Optional[str] = Field(
        default=None, description="The key type of the column"
    )
    references: list[ReferenceContext] = Field(
        default=list(),
        description="The referenced columns from another table of the column",
    )


class TableContext(BaseModel):
    """Model representing context for a table"""

    table_name: str = Field(..., description="The name of the table")
    table_description: Optional[str] = Field(default=None, description="The description of the table")
    database_name: Optional[str] = Field(default=None, description="The name of the database")
    schema_name: Optional[str] = Field(default=None, description="The name of the schema")
    columns: list[ColumnContext] = Field(
        ..., description="The relevant columns of the table"
    )
    joins: list[JoinContext] = Field(
        default=list(), description="The relevant join tables of the table"
    )
