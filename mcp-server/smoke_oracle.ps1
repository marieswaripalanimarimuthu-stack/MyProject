param(
  [string]$Dsn = $env:ORACLE_DSN,
  [string]$User = $env:ORACLE_USER,
  [string]$Password = $env:ORACLE_PASSWORD
)

Write-Host "[Smoke] Oracle DSN: $Dsn"
Write-Host "[Smoke] Oracle User: $User"

if (-not $Dsn -or -not $User -or -not $Password) {
  Write-Error "Missing env vars. Set ORACLE_DSN, ORACLE_USER, ORACLE_PASSWORD or pass -Dsn/-User/-Password."
  exit 2
}

$env:ORACLE_DSN = $Dsn
$env:ORACLE_USER = $User
$env:ORACLE_PASSWORD = $Password

# Ensure dependencies
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Error "Python is required in PATH."
  exit 2
}

# Confirm oracledb is installed
try {
  python - <<'PY'
import importlib, sys
try:
    import oracledb
    print('python-oracledb version', oracledb.__version__)
except Exception as e:
    print('[ERROR] python-oracledb not installed:', e, file=sys.stderr)
    sys.exit(1)
PY
  if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing requirements from mcp-server/requirements.txt..."
    pip install -r "$PSScriptRoot/requirements.txt" | Out-Null
  }
}
catch {
  Write-Host "Installing requirements from mcp-server/requirements.txt..."
  pip install -r "$PSScriptRoot/requirements.txt" | Out-Null
}

# Run test
python "$PSScriptRoot/test_oracle_connection.py"
exit $LASTEXITCODE
