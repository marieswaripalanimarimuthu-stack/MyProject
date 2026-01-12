# Sets environment variables for onejira.verizon.com and starts MCP Server
param(
    [string]$Username = "v776133",
    [string]$Secret = "",
    [string]$Project = "B6VV_CXP Operations",
    # Optional Oracle configuration
    [string]$OracleDsn = "tpalpbrhvd00-scan.verizon.com:1532/couser_srv01",
    [string]$OracleUser = "Tier_Ops",
    [string]$OraclePassword = "QWEqwe##00"
)

if ([string]::IsNullOrWhiteSpace($Secret)) {
    Write-Host "Enter your Jira password (or PAT):" -ForegroundColor Cyan
    $Secure = Read-Host -AsSecureString
    $Secret = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
    )
}

$env:JIRA_BASE_URL = "https://onejira.verizon.com"
$env:JIRA_API_VERSION = "2"
$env:JIRA_USERNAME = $Username
$env:JIRA_API_TOKEN = $Secret
# Optional email (server prefers USERNAME when set)
$env:JIRA_EMAIL = "$Username@verizon.com"

# Ensure mock mode off
Remove-Item Env:JIRA_MOCK -ErrorAction SilentlyContinue

# Optional Oracle envs
if (-not [string]::IsNullOrWhiteSpace($OracleDsn)) { $env:ORACLE_DSN = $OracleDsn }
if (-not [string]::IsNullOrWhiteSpace($OracleUser)) { $env:ORACLE_USER = $OracleUser }
if ([string]::IsNullOrWhiteSpace($OraclePassword) -and -not [string]::IsNullOrWhiteSpace($OracleUser)) {
    Write-Host "Enter Oracle password for user '$OracleUser':" -ForegroundColor Cyan
    $opw = Read-Host -AsSecureString
    $OraclePassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($opw)
    )
}
if (-not [string]::IsNullOrWhiteSpace($OraclePassword)) { $env:ORACLE_PASSWORD = $OraclePassword }

Write-Host "Starting MCP Server with:" -ForegroundColor Green
Write-Host "  BASE_URL=$env:JIRA_BASE_URL"
Write-Host "  API_VERSION=$env:JIRA_API_VERSION"
Write-Host "  USERNAME=$env:JIRA_USERNAME"
Write-Host "  EMAIL=$env:JIRA_EMAIL"
if ($env:ORACLE_DSN -or $env:ORACLE_USER) {
    Write-Host "  ORACLE_DSN=$env:ORACLE_DSN"
    Write-Host "  ORACLE_USER=$env:ORACLE_USER"
}

# Change to script directory and start server
Push-Location $PSScriptRoot
python -m mcp_server
Pop-Location
