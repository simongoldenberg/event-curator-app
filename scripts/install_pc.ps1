$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runner = Join-Path $PSScriptRoot 'start_pc.ps1'
$userId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
if ($runner.Contains('"')) { throw 'Ungültiges Anführungszeichen im Skriptpfad.' }

$arguments = '-NoProfile -NonInteractive -WindowStyle Hidden -File "{0}" -ServerOnly' -f $runner
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arguments -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $userId
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -Hidden
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'EventCurator-Web' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Lokalen Event Curator nach der Windows-Anmeldung bereitstellen.' -Force | Out-Null

$desktop = [Environment]::GetFolderPath('Desktop')
if (-not (Test-Path -LiteralPath $desktop -PathType Container)) { throw 'Desktop-Ordner nicht gefunden.' }
$shell = New-Object -ComObject WScript.Shell
foreach ($item in @(
    @{ Name = 'Event Curator.lnk'; Extra = ''; Description = 'Aktuellen Event-Bericht öffnen' },
    @{ Name = 'Event Curator - Jetzt suchen.lnk'; Extra = ' -SearchNow'; Description = 'Neue Eventsuche starten und Bericht öffnen' }
)) {
    $shortcut = $shell.CreateShortcut((Join-Path $desktop $item.Name))
    $shortcut.TargetPath = 'powershell.exe'
    $shortcut.Arguments = ('-NoProfile -File "{0}"{1}' -f $runner, $item.Extra)
    $shortcut.WorkingDirectory = $projectRoot
    $shortcut.Description = $item.Description
    $shortcut.Save()
}
Write-Host "PC-Start eingerichtet. Desktop-Verknüpfungen: $desktop"
