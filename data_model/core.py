"""
The core components of the RDBMS metadata graph data model.
"""

from pydantic import BaseModel, Field, ValidationInfo, field_validator
from typing import Optional


class Database(BaseModel):
    """A Database node"""

    id: str = Field(..., description="The unique identifier for the database")
    name: str = Field(..., description="The name of the database")
    platform: Optional[str] = Field(default=None, description="The platform of the database", examples=["GCP"])
    service: Optional[str] = Field(default=None, description="The service running the database", examples=["BIGQUERY"])
    description: Optional[str] = Field(
        default=None, description="The description of the database"
    )
    embedding: Optional[list[float]] = Field(
        default=None, description="The embedding of the database description"
    )

    @field_validator("platform", "service", mode="after")
    def validate_string_uppercase(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate that the string is in uppercase.
        """
        return v.upper() if v is not None else None


class Schema(BaseModel):
    """A Schema node (represents a BigQuery dataset)"""

    id: str = Field(..., description="The unique identifier for the schema")
    name: str = Field(..., description="The name of the schema")
    description: Optional[str] = Field(
        default=None, description="The description of the schema"
    )
    embedding: Optional[list[float]] = Field(
        default=None, description="The embedding of the schema description"
    )


class Table(BaseModel):
    """A Table node"""

    id: str = Field(..., description="The unique identifier for the table")
    name: str = Field(..., description="The name of the table")
    description: Optional[str] = Field(
        default=None, description="The description of the table"
    )
    embedding: Optional[list[float]] = Field(
        default=None, description="The embedding of the table description"
    )


class Column(BaseModel):
    """A Column node"""

    id: str = Field(..., description="The unique identifier for the column")
    name: str = Field(..., description="The name of the column")
    description: Optional[str] = Field(
        default=None, description="The description of the column"
    )
    embedding: Optional[list[float]] = Field(
        default=None, description="The embedding of the column description"
    )
    type: Optional[str] = Field(default=None, description="The data type of the column. Data types may be unavailable in source data such as query logs.")
    nullable: bool = Field(default=True, description="Whether the column can be null")
    is_primary_key: bool = Field(
        default=False, description="Whether the column is a primary key"
    )
    is_foreign_key: bool = Field(
        default=False, description="Whether the column is a foreign key"
    )

    @field_validator("is_foreign_key", mode="after")
    def validate_not_both_pk_and_fk(cls, v: bool, info: ValidationInfo) -> bool:
        """
        Validate that a column cannot be both a primary key and a foreign key.
        We only need to validate `is_foreign_key` since it is defined after `is_primary_key`.
        """
        if v and info.data["is_primary_key"]:
            raise ValueError("Column cannot be both a primary key and a foreign key")
        return v


class HasSchema(BaseModel):
    """
    A relationship between a database and a schema
    (Database)-[:HAS_SCHEMA]->(Schema)
    """

    database_id: str = Field(..., description="The unique identifier for the database")
    schema_id: str = Field(..., description="The unique identifier for the schema")


class HasTable(BaseModel):
    """
    A relationship between a schema and a table
    (Schema)-[:HAS_TABLE]->(Table)
    """

    schema_id: str = Field(..., description="The unique identifier for the schema")
    table_id: str = Field(..., description="The unique identifier for the table")


class HasColumn(BaseModel):
    """
    A relationship between a table and a column
    (Table)-[:HAS_COLUMN]->(Column)
    """

    table_id: str = Field(..., description="The unique identifier for the table")
    column_id: str = Field(..., description="The unique identifier for the column")


class References(BaseModel):
    """
    A relationship between two columns
    (Column)-[:REFERENCES]->(Column)
    """

    source_column_id: str = Field(
        ..., description="The unique identifier for the source column"
    )
    target_column_id: str = Field(
        ..., description="The unique identifier for the target column"
    )
    criteria: Optional[str] = Field(
        default=None, description="The criteria for the references relationship. This is the join condition for the two columns."
    )
