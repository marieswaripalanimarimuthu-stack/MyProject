# MCP Server

Minimal Python MCP-like server exposing a Jira endpoint without external dependencies.

## Requirements
- Python 3.9+
- Windows PowerShell

## Configuration
Set these environment variables:
- `JIRA_BASE_URL` (e.g., `https://your-domain.atlassian.net`)
- `JIRA_EMAIL`
- `JIRA_API_TOKEN`

Optional:
- `JIRA_MOCK=1` to return stubbed data without calling Jira.
- `JIRA_API_VERSION` set to `2` for on-prem/server Jira instances; defaults to `3` for Jira Cloud.

## Run
```
# Optionally set environment variables for Jira
$env:JIRA_BASE_URL = "https://your-domain.atlassian.net"
$env:JIRA_EMAIL = "you@example.com"
$env:JIRA_API_TOKEN = "your_api_token"
# For on-prem Jira (e.g., onejira.verizon.com), you may need API v2:
# $env:JIRA_BASE_URL = "https://onejira.verizon.com"
# $env:JIRA_API_VERSION = "2"
# To use mock data, uncomment:
# $env:JIRA_MOCK = "1"

python -m mcp_server
```
Server starts on `http://127.0.0.1:8765`.

## Endpoint
- `GET /jira/issues?project=<KEY>&maxResults=<N>`

Returns JSON issues for the project.

### Query Builder
- `POST /query/build`

Builds a parameterized Oracle SQL SELECT from a JSON spec and returns `{ sql, params }` without executing it. You can then pass the result to `POST /oracle/query` to run it.

Example spec:
```
{
	"tables": ["ORDERS", "ORDER_ITEMS"],
	"from": "ORDERS",
	"alias": {"ORDERS":"o","ORDER_ITEMS":"i"},
	"select": ["o.ORDER_ID", "o.CUSTOMER_ID", {"expr":"COUNT(*)","as":"item_count"}],
	"joins": [{"type":"inner","left":"o.ORDER_ID","right":"i.ORDER_ID"}],
	"filters": [
		{"col":"o.STATUS","op":"=","value":"OPEN"},
		{"col":"o.CREATED_DATE","op":"between","value":["2025-01-01","2025-12-31"],"join":"AND"}
	],
	"groupBy": ["o.ORDER_ID", "o.CUSTOMER_ID"],
	"orderBy": [{"expr":"o.CREATED_DATE","dir":"DESC"}],
	"limit": 100
}
```

PowerShell example to build and execute:
```
$spec = '{
	"tables": ["ORDERS", "ORDER_ITEMS"],
	"from": "ORDERS",
	"alias": {"ORDERS":"o","ORDER_ITEMS":"i"},
	"select": ["o.ORDER_ID", {"expr":"COUNT(*)","as":"item_count"}],
	"joins": [{"type":"inner","left":"o.ORDER_ID","right":"i.ORDER_ID"}],
	"groupBy": ["o.ORDER_ID"],
	"limit": 10
}'

$build = Invoke-WebRequest -Uri 'http://127.0.0.1:8765/query/build' -Method POST -Body $spec -ContentType 'application/json' -UseBasicParsing | ConvertFrom-Json

$body = @{ sql = $build.sql; params = $build.params; maxRows = 500 } | ConvertTo-Json -Depth 5
Invoke-WebRequest -Uri 'http://127.0.0.1:8765/oracle/query' -Method POST -Body $body -ContentType 'application/json' -UseBasicParsing | Select-Object -ExpandProperty Content
```

### Quick Query
- `POST /query/quick`

Builds a SELECT from a single table and a simple filter string (e.g., `workobjectstatus="pending-ActivationNotification"`). Good for fast, user-driven lookups.

Request body:
```
{
	"table": "YOUR_TABLE",
	"ask": "workobjectstatus=\"pending-ActivationNotification\"",
	"select": ["*"],
	"limit": 100
}
```

PowerShell example:
```
$spec = '{
	"table": "YOUR_TABLE",
	"ask": "workobjectstatus=\"pending-ActivationNotification\"",
	"limit": 50
}'
$build = Invoke-WebRequest -Uri 'http://127.0.0.1:8765/query/quick' -Method POST -Body $spec -ContentType 'application/json' -UseBasicParsing | ConvertFrom-Json
$body = @{ sql = $build.sql; params = $build.params; maxRows = 500 } | ConvertTo-Json -Depth 5
Invoke-WebRequest -Uri 'http://127.0.0.1:8765/oracle/query' -Method POST -Body $body -ContentType 'application/json' -UseBasicParsing | Select-Object -ExpandProperty Content
```

Supported quick filters:
- `col = value`, `!=`, `<>`, `>`, `>=`, `<`, `<=`
- `col like "%text%"`
- `col in (v1, v2, "v 3")`
- `col between a and b`
- `col is null`, `col is not null`
- Combine with `AND` / `OR` (e.g., `status="OPEN" AND id > 100`)

## OneJira Shortcut
Use the helper script to set envs and start the server:
```
cd C:\Users\v776133\Downloads\JiraAgent\mcp-server
./start_server_onejira.ps1 -Username v776133
```
You will be prompted for your Jira password (or PAT). The server will start with `JIRA_API_VERSION=2` and `JIRA_BASE_URL=https://onejira.verizon.com`.
