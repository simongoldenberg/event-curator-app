param([Parameter(Mandatory=$true)][string]$PythonExe, [switch]$Bandsintown, [switch]$Discover)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = (Resolve-Path -LiteralPath $PythonExe).Path
$runner = Join-Path $PSScriptRoot 'run_monthly.ps1'
if ($PythonExe.Contains('"') -or $runner.Contains('"')) { throw 'Ungültiges Anführungszeichen im Pfad.' }
$arguments = '-NoProfile -NonInteractive -File "{0}" -PythonExe "{1}"' -f $runner, $PythonExe
if ($Bandsintown) { $arguments += ' -Bandsintown' }
if ($Discover) { $arguments += ' -Discover' }
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arguments -WorkingDirectory $projectRoot
# Täglich nachholen, bis der Monat erfolgreich erfasst wurde. Keine Passwörter speichern.
$trigger = New-ScheduledTaskTrigger -Daily -At '09:00'
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'EventCurator-Monthly' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Lokaler Monatsdigest; erfolgreiche Monate werden übersprungen.'
Write-Host 'Aufgabe angelegt. Ausführung bei angemeldetem Benutzer; kein Cloud-Upload.'

