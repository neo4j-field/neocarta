from pydantic import BaseModel, Field
from typing import Optional

class Database(BaseModel):
    
    id: str = Field(..., description="The unique identifier for the database")
    name: str = Field(..., description="The name of the database")
    description: str = Field(..., description="The description of the database")
    embedding: Optional[list[float]] = Field(..., description="The embedding of the database description")

class Table(BaseModel):
    id: str = Field(..., description="The unique identifier for the table")
    name: str = Field(..., description="The name of the table")
    description: str = Field(..., description="The description of the table")
    embedding: Optional[list[float]] = Field(..., description="The embedding of the table description")

class Column(BaseModel):
    id: str = Field(..., description="The unique identifier for the column")
    name: str = Field(..., description="The name of the column")
    description: str = Field(..., description="The description of the column")
    embedding: Optional[list[float]] = Field(..., description="The embedding of the column description")
    type: str = Field(..., description="The data type of the column")
    nullable: bool = Field(..., description="Whether the column can be null")
    key_type: Optional[str] = Field(..., description="The type of key the column is")

class ContainsTable(BaseModel):
    database_id: str = Field(..., description="The unique identifier for the database")
    table_id: str = Field(..., description="The unique identifier for the table")

class HasColumn(BaseModel):
    table_id: str = Field(..., description="The unique identifier for the table")
    column_id: str = Field(..., description="The unique identifier for the column")

class References(BaseModel):
    source_column_id: str = Field(..., description="The unique identifier for the source column")
    target_column_id: str = Field(..., description="The unique identifier for the target column")

