param([Parameter(Mandatory=$true)][string]$PythonExe, [switch]$Bandsintown, [switch]$Discover)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) { throw 'Python-Interpreter nicht gefunden.' }
$month = Get-Date -Format 'yyyy-MM'
$statePath = Join-Path 'data' 'user_monthly_state.json'
if (Test-Path -LiteralPath $statePath) {
    $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
    $entry = $state.PSObject.Properties[$month]
    if ($null -ne $entry -and $entry.Value.success -and $entry.Value.reports -and
        @($entry.Value.reports | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) }).Count -eq 0) {
        Write-Host "Monatslauf $month bereits erfolgreich."
        exit 0
    }
}
if ($Discover) {
    & $PythonExe 'scripts/scan_artist_pages.py' --month $month
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
$cliArgs = @('main.py', '--live', '--monthly')
if ($Bandsintown) { $cliArgs += '--include-bandsintown' }
if ($Discover) { $cliArgs += '--discover' }
& $PythonExe @cliArgs
exit $LASTEXITCODE
