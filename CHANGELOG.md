# Changelog of neocarta library

## Upcoming

### Fixed

### Changed
* Move MCP server to `neocarta` library
* Change MCP server name to `neocarta-mcp`
* Update MCP server imports in `eval/` module
* Deduplicate embedding code in MCP server. MCP server now uses `neocarta` embeddings class.
* Update Cypher queries in MCP server to follow same traversal patterns and return similar objects
* Update MCP tool documentation

### Added
* Add integration tests for MCP server compatibility with neocarta graph
* Add `get_metadata_schema_by_table_semantic_similarity` tool to MCP server

## v0.1.0

Initial release