"""Neocarta library root package."""

from importlib.metadata import version

from .enums import NodeLabel, RelationshipType

__version__ = version("neocarta")

__all__ = ["NodeLabel", "RelationshipType", "__version__"]
