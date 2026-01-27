from pydantic import BaseModel, Field

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
