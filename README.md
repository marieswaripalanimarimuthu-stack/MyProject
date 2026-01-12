# MyProject

A simple MCP (Model Context Protocol) client/server setup for querying Jira issues, with a small web UI. This repository contains:

- `mcp-server/`: Python server that builds JQL queries and fetches issues from Jira.
- `mcp-client/`: Python client CLI to query the server.
- `mcp-client/ui/`: Simple HTML views for queue snapshots and order status mapping.

## Quick Start

### Server
```powershell
cd mcp-server
pip install -r requirements.txt
# Set environment variables (example values; replace with your own)
$env:JIRA_BASE_URL = "https://onejira.verizon.com"
$env:JIRA_EMAIL = "you@company.com"
$env:JIRA_API_TOKEN = "<your_token>"
$env:JIRA_API_VERSION = "2"
# Start server
python -m mcp_server
```
Server runs on `http://127.0.0.1:8765`.

### Client
```powershell
cd mcp-client
python -m mcp_client --project "Your Project" --assigned me --type Bug --max 25
```

## Development
- Python 3.11 recommended.
- Lint: flake8, Format: black, Types: mypy.
- Basic unit tests ensure modules import correctly.

## CI
GitHub Actions workflow runs on every push/PR to `main`:
- Installs `mcp-server` dependencies.
- Runs flake8 and black checks (non-blocking for now).
- Runs mypy (non-blocking for now).
- Runs `python -m unittest`.

## Security
- Do not commit real secrets. Use placeholders in examples (see `mcp-server/.env.example`).
- GitHub Push Protection is enabled to detect secrets; remove/redact any detected values.

## License
Internal use. Update this section if you plan to publish.
