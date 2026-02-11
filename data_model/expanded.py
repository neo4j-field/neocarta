from pydantic import BaseModel, Field
from typing import Optional


class Value(BaseModel):
    """A Column Value node representing a unqiue value in a column"""

    id: str = Field(..., description="The unique identifier for the value")
    value: str = Field(..., description="The value cast to a string")


class HasValue(BaseModel):
    """
    A relationship between a column and a value.
    (Column)-[:HAS_VALUE]->(Value)
    """

    column_id: str = Field(..., description="The unique identifier for the column")
    value_id: str = Field(..., description="The unique identifier for the value")

class Glossary(BaseModel):
    """A Glossary node representing a glossary of business terms in a data catalog"""
    id: str = Field(..., description="The unique identifier for the glossary")
    name: str = Field(..., description="The name of the glossary")
    description: Optional[str] = Field(default=None, description="The description of the glossary")

class Category(BaseModel):
    """A Category node representing a category in a glossary"""
    id: str = Field(..., description="The unique identifier for the category")
    name: str = Field(..., description="The name of the category")
    description: Optional[str] = Field(default=None, description="The description of the category")

class BusinessTerm(BaseModel):
    """A Business Term node representing a business term in a glossary"""
    id: str = Field(..., description="The unique identifier for the business term")
    name: str = Field(..., description="The name of the business term")
    description: Optional[str] = Field(default=None, description="The description of the business term")

class HasCategory(BaseModel):
    """
    A relationship between a Glossary and a Category
    (Glossary)-[:HAS_CATEGORY]->(Category)
    """
    glossary_id: str = Field(..., description="The unique identifier for the glossary")
    category_id: str = Field(..., description="The unique identifier for the category")

class HasBusinessTerm(BaseModel):
    """
    A relationship between a Category and a Business Term
    (Glossary)-[:HAS_BUSINESS_TERM]->(BusinessTerm)
    """
    glossary_id: str = Field(..., description="The unique identifier for the glossary")
    business_term_id: str = Field(..., description="The unique identifier for the business term")


