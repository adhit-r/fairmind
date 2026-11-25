# Installs the FairMind notifier for every person who signs in to this laptop. Run as SYSTEM from device management.
# Expects fairmind-notifier.exe beside this script and C:\ProgramData\FairMind\notifier.json from Shadow AI.
$dir = 'C:\Program Files\FairMind'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
Copy-Item -Force (Join-Path $PSScriptRoot 'fairmind-notifier.exe') $dir
$action = New-ScheduledTaskAction -Execute (Join-Path $dir 'fairmind-notifier.exe')
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -GroupId 'BUILTIN\Users' -RunLevel Limited
Register-ScheduledTask -TaskName 'FairMind notifier' -Action $action -Trigger $trigger -Principal $principal -Force | Out-Null
