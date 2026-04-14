"""Expanded RDBMS data model nodes and relationships (glossary, queries, values)."""

from typing import Any

from pandas import isna
from pydantic import BaseModel, Field, field_validator


class Value(BaseModel):
    """A Column Value node representing a unqiue value in a column."""

    id: str = Field(..., description="The unique identifier for the value")
    value: str = Field(..., description="The value cast to a string")

    @field_validator("value", mode="before")
    def cast_to_string(cls, v: Any) -> str:
        """Cast the value to a string."""
        # return empty string for NaN values
        if v is None or isna(v):
            return ""
        return str(v)


class HasValue(BaseModel):
    """
    A relationship between a column and a value.
    (Column)-[:HAS_VALUE]->(Value).
    """

    column_id: str = Field(..., description="The unique identifier for the column")
    value_id: str = Field(..., description="The unique identifier for the value")


class Glossary(BaseModel):
    """A Glossary node representing a glossary of business terms in a data catalog."""

    id: str = Field(..., description="The unique identifier for the glossary")
    name: str = Field(..., description="The name of the glossary")
    description: str | None = Field(default=None, description="The description of the glossary")


class Category(BaseModel):
    """A Category node representing a category in a glossary."""

    id: str = Field(..., description="The unique identifier for the category")
    name: str = Field(..., description="The name of the category")
    description: str | None = Field(default=None, description="The description of the category")


class BusinessTerm(BaseModel):
    """A Business Term node representing a business term in a glossary."""

    id: str = Field(..., description="The unique identifier for the business term")
    name: str = Field(..., description="The name of the business term")
    description: str | None = Field(
        default=None, description="The description of the business term"
    )
    embedding: list[float] | None = Field(
        default=None, description="The embedding of the business term description"
    )


class HasCategory(BaseModel):
    """
    A relationship between a Glossary and a Category
    (Glossary)-[:HAS_CATEGORY]->(Category).
    """

    glossary_id: str = Field(..., description="The unique identifier for the glossary")
    category_id: str = Field(..., description="The unique identifier for the category")


class HasBusinessTerm(BaseModel):
    """
    A relationship between a Category and a Business Term
    (Category)-[:HAS_BUSINESS_TERM]->(BusinessTerm).
    """

    category_id: str = Field(..., description="The unique identifier for the category")
    business_term_id: str = Field(..., description="The unique identifier for the business term")


class Query(BaseModel):
    """A Query node representing a query in a query log."""

    id: str = Field(..., description="The unique identifier for the query")
    content: str = Field(..., description="The content of the query")
    description: str | None = Field(default=None, description="The description of the query")
    embedding: list[float] | None = Field(
        default=None, description="The embedding of the query description"
    )


class UsesTable(BaseModel):
    """
    A relationship between a query and a table
    (Query)-[:USES_TABLE]->(Table).
    """

    query_id: str = Field(..., description="The unique identifier for the query")
    table_id: str = Field(..., description="The unique identifier for the table")


class UsesColumn(BaseModel):
    """
    A relationship between a query and a column
    (Query)-[:USES_COLUMN]->(Column).
    """

    query_id: str = Field(..., description="The unique identifier for the query")
    column_id: str = Field(..., description="The unique identifier for the column")
