param([switch]$SearchNow, [switch]$ServerOnly)
$ErrorActionPreference = 'Stop'
if ($SearchNow -and $ServerOnly) { throw 'SearchNow und ServerOnly schließen sich aus.' }

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
$exportDir = Join-Path $projectRoot 'exports'
$appPath = Join-Path $exportDir 'app.html'
$appUrl = 'http://127.0.0.1:8765/app.html'
if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) { throw 'Python-Umgebung .venv fehlt.' }
New-Item -ItemType Directory -Path $exportDir -Force | Out-Null

if ($SearchNow) {
    Set-Location -LiteralPath $projectRoot
    Write-Host 'Neue Eventsuche läuft. Das kann einige Minuten dauern.'
    & $pythonExe 'main.py' '--live' '--monthly' '--force' '--discover'
    if ($LASTEXITCODE -eq 2) { Write-Warning 'Einzelne Quellen waren nicht erreichbar; der Bericht zeigt die Hinweise.' }
    elseif ($LASTEXITCODE -ne 0) { throw 'Die Eventsuche ist fehlgeschlagen.' }
    if (-not (Test-Path -LiteralPath $appPath -PathType Leaf)) { throw 'Die Suche hat keinen Bericht erzeugt.' }
}

function Test-LocalApp {
    try {
        $request = [System.Net.HttpWebRequest]::Create($appUrl)
        $request.Proxy = $null
        $request.Timeout = 2000
        $response = $request.GetResponse()
        try { return [int]$response.StatusCode -eq 200 }
        finally { $response.Close() }
    } catch { return $false }
}

if (-not (Test-LocalApp)) {
    $directoryArgument = '"' + $exportDir + '"'
    Start-Process -FilePath $pythonExe -ArgumentList @('-m','http.server','8765','--bind','127.0.0.1','--directory',$directoryArgument) -WorkingDirectory $projectRoot -WindowStyle Hidden | Out-Null
    $ready = $false
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        Start-Sleep -Milliseconds 300
        if (Test-LocalApp) { $ready = $true; break }
    }
    if (-not $ready -and (Test-Path -LiteralPath $appPath -PathType Leaf)) {
        throw 'Der lokale Webserver auf Port 8765 antwortet nicht.'
    }
}

if (-not $ServerOnly) {
    if (-not (Test-Path -LiteralPath $appPath -PathType Leaf)) {
        throw 'Noch kein Live-Bericht vorhanden. Starte zuerst die Verknüpfung „Event Curator - Jetzt suchen“.'
    }
    Start-Process $appUrl
}
