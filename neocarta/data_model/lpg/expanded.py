"""Extended components of the LPG (Labeled Property Graph) metadata graph data model."""

from typing import Any

from pydantic import BaseModel, Field


class Value(BaseModel):
    """A Property Value node representing a distinct value for a property."""

    id: str = Field(..., description="The unique identifier for the value")
    value: Any = Field(..., description="The actual value")
    type: str = Field(..., description="The data type of the value")
    count: int = Field(default=1, description="The number of times this value appears")
    embedding: list[float] | None = Field(default=None, description="The embedding of the value")


class HasValue(BaseModel):
    """
    A relationship between a property and a value.
    (Property)-[:HAS_VALUE]->(Value).
    """

    property_id: str = Field(..., description="The unique identifier for the property")
    value_id: str = Field(..., description="The unique identifier for the value")
