[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PythonExe,
    [Parameter(Mandatory=$true)][string]$Owner,
    [Parameter(Mandatory=$true)][string]$CommitEmail,
    [string]$RepoName = 'event-curator-app',
    [switch]$PublishMain
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) { throw 'Expliziten Python-Pfad angeben.' }
if ($Owner -notmatch '^[A-Za-z0-9-]+$' -or $RepoName -notmatch '^[A-Za-z0-9_.-]+$') { throw 'Owner/Repository-Name ungültig.' }
function Invoke-Git { & git @args; if ($LASTEXITCODE -ne 0) { throw 'Git-Befehl fehlgeschlagen.' } }
function Invoke-Gh { & gh @args; if ($LASTEXITCODE -ne 0) { throw 'GitHub-Befehl fehlgeschlagen.' } }
Get-Command git, gh -ErrorAction Stop | Out-Null
if (-not (Test-Path -LiteralPath '.git')) { Invoke-Git init -b develop }
$branch = (& git branch --show-current).Trim()
if ($branch -ne 'develop') { throw 'Bitte zuerst den Arbeitsstand auf develop klären. Das Skript wechselt keine vorhandenen Branches.' }
# Authentifizierung interaktiv; Schlüssel werden vom GitHub-Credential-Store verwaltet.
& gh auth status
if ($LASTEXITCODE -ne 0) { Invoke-Gh auth login --hostname github.com --git-protocol https --web }
$actualOwner = (& gh api user --jq .login).Trim()
if ($LASTEXITCODE -ne 0 -or $actualOwner -ne $Owner) { throw 'Angemeldeter Account stimmt nicht mit Owner überein.' }
Invoke-Gh auth setup-git
$remoteUrl = "https://github.com/$Owner/$RepoName.git"
$remoteNames = @(& git remote)
if ($remoteNames -contains 'origin') {
    $existing = (& git remote get-url origin).Trim()
    if ($existing -ne $remoteUrl) { throw 'Origin zeigt auf ein anderes Repository; bitte prüfen.' }
    Invoke-Git fetch origin
    $tracking = & git rev-parse --verify origin/develop 2>$null
    if ($LASTEXITCODE -eq 0) {
        $behind = & git rev-list --count HEAD..origin/develop
        if ($LASTEXITCODE -ne 0 -or [int]$behind -gt 0) { throw 'Remote enthält neue Commits. Vor Setup synchronisieren.' }
    }
}
Invoke-Git config --local user.email $CommitEmail
$name = & git config user.name
if (-not $name) { Invoke-Git config --local user.name $actualOwner }
& $PythonExe -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests fehlgeschlagen.' }
& $PythonExe scripts/check_privacy.py
if ($LASTEXITCODE -ne 0) { throw 'Datenschutzprüfung fehlgeschlagen.' }
# Bewusste Auswahl; niemals git add . für den initialen Upload.
Invoke-Git add -- .gitignore .env.example AGENTS.md README.md CHANGELOG.md LICENSE requirements.txt config.py main.py event_curator scripts tests data/sample_artists.csv
& $PythonExe scripts/check_privacy.py
if ($LASTEXITCODE -ne 0) { throw 'Datenschutzprüfung des Index fehlgeschlagen.' }
& git diff --cached --quiet
if ($LASTEXITCODE -eq 1) { Invoke-Git commit -m 'Build local event curator with private data storage and modular sources' }
elseif ($LASTEXITCODE -ne 0) { throw 'Indexprüfung fehlgeschlagen.' }
if ($remoteNames -notcontains 'origin') {
    # Ein bereits existierendes Repository wird nicht stillschweigend übernommen.
    Invoke-Gh repo create "$Owner/$RepoName" --public --description 'Local event and party curator with private user data'
    Invoke-Git remote add origin $remoteUrl
}
Invoke-Git push -u origin develop
if ($PublishMain) {
    # Explizite Freigabe ausschließlich für den allerersten Main-Stand.
    $mainRemote = & git ls-remote --heads origin main
    if ($LASTEXITCODE -ne 0) { throw 'Main-Status konnte nicht geprüft werden.' }
    if ($mainRemote) { throw 'Main existiert bereits. Für weitere Releases den vereinbarten PR-Workflow nutzen.' }
    Invoke-Git push origin develop:main
    Invoke-Gh repo edit "$Owner/$RepoName" --default-branch main
}
Write-Host "Fertig: https://github.com/$Owner/$RepoName (Entwicklung bleibt auf develop)."

