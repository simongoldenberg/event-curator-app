param([Parameter(Mandatory=$true)][string]$PythonExe, [switch]$Bandsintown, [switch]$Discover)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) { throw 'Python-Interpreter nicht gefunden.' }
$cliArgs = @('main.py', '--live', '--monthly')
if ($Bandsintown) { $cliArgs += '--include-bandsintown' }
if ($Discover) { $cliArgs += '--discover' }
& $PythonExe @cliArgs
$digestCode = $LASTEXITCODE
if ($Discover) {
    & $PythonExe 'scripts/scan_artist_pages.py'
    $scanCode = $LASTEXITCODE
    if ($scanCode -ne 0) { exit $scanCode }
}
exit $digestCode
