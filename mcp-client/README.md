# MCP Client

Minimal Python client that calls the local MCP server to fetch Jira issues.

## Requirements
- Python 3.9+
- Windows PowerShell

## Usage
```
# Ensure the server is running first
python -m mcp_server

# In another terminal, call the client
# Assigned to you (defects/bugs only)
python -m mcp_client --project <KEY or Name with spaces> --assigned me --type Bug --status Open --max 25

# Example without filters
python -m mcp_client --project <KEY> --max 25
```
