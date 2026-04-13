"""Shared enum types for the semantic graph schema."""

from enum import Enum


class NodeLabel(str, Enum):
    """Node labels for the semantic graph."""

    DATABASE = "Database"
    SCHEMA = "Schema"
    TABLE = "Table"
    COLUMN = "Column"
    VALUE = "Value"
    GLOSSARY = "Glossary"
    CATEGORY = "Category"
    BUSINESS_TERM = "BusinessTerm"
    QUERY = "Query"

    def __str__(self) -> str:
        return self.value

    def __format__(self, format_spec: str) -> str:
        return self.value.__format__(format_spec)


class RelationshipType(str, Enum):
    """Relationship types for the semantic graph."""

    HAS_SCHEMA = "HAS_SCHEMA"
    HAS_TABLE = "HAS_TABLE"
    HAS_COLUMN = "HAS_COLUMN"
    HAS_VALUE = "HAS_VALUE"
    HAS_CATEGORY = "HAS_CATEGORY"
    HAS_BUSINESS_TERM = "HAS_BUSINESS_TERM"
    REFERENCES = "REFERENCES"
    USES_TABLE = "USES_TABLE"
    USES_COLUMN = "USES_COLUMN"

    def __str__(self) -> str:
        return self.value

    def __format__(self, format_spec: str) -> str:
        return self.value.__format__(format_spec)
