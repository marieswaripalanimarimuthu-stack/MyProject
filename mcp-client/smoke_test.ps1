# Run MCP server in mock mode and query a sample project
$env:JIRA_MOCK = "1"
Start-Job -ScriptBlock { python -m mcp_server } | Out-Null
Start-Sleep -Seconds 2
python -m mcp_client --project ABC --max 5
