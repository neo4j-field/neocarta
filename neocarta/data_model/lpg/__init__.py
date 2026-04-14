"""LPG (Labeled Property Graph) data model nodes and relationships."""

import warnings

from .core import (
    Database,
    HasNode,
    HasRelationship,
    HasSchema,
    HasSourceNode,
    HasTargetNode,
    Node,
    NodeHasProperty,
    Property,
    Relationship,
    RelationshipHasProperty,
    Schema,
)
from .expanded import (
    HasValue,
    Value,
)

warnings.warn(
    "LPG data model components are an in-progress feature. There is no application in the current library version.",
    stacklevel=2,
)

__all__ = [
    # LPG Core nodes
    "Database",
    "HasNode",
    "HasRelationship",
    # LPG Core relationships
    "HasSchema",
    "HasSourceNode",
    "HasTargetNode",
    # LPG Value relationships
    "HasValue",
    "Node",
    "NodeHasProperty",
    "Property",
    "Relationship",
    "RelationshipHasProperty",
    "Schema",
    # LPG Value nodes
    "Value",
]
