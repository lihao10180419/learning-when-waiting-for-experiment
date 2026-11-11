$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskPython = (Get-Command python.exe -ErrorAction Stop).Source
$taskPaths = (& $taskPython -X utf8 (Join-Path $taskRoot 'settings.py')) | ConvertFrom-Json
$taskConfigPath = $taskPaths.config
$taskRuntime = $taskPaths.runtime
$taskWatcherPath = Join-Path $taskRoot 'codex_autostart.py'
$taskPythonPath = (& $taskPython -c 'import sys; print(sys.executable)').Trim()
$taskPythonW = Join-Path (Split-Path -Parent $taskPythonPath) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $taskPythonW)) { throw 'Existing pythonw.exe was not found.' }
$taskConfig = Get-Content -LiteralPath $taskConfigPath -Raw -Encoding utf8 | ConvertFrom-Json
if (-not $taskConfig.connection_verified) { throw 'A verified learning-thread connection is required.' }
$taskStartup = [Environment]::GetFolderPath('Startup')
if (-not $taskStartup) { throw 'Current-user Windows Startup folder is unavailable.' }
$taskShortcutPath = Join-Path $taskStartup 'Codex Experiment Learning Plugin.lnk'
$taskShell = New-Object -ComObject WScript.Shell
if (Test-Path -LiteralPath $taskShortcutPath) {
    $taskOld = $taskShell.CreateShortcut($taskShortcutPath)
    if (-not $taskOld.Arguments.Contains($taskWatcherPath) -or -not $taskOld.Arguments.Contains($taskPaths.home)) {
        throw 'Another installation or profile owns this Startup entry. Disable it using that installation before replacing it.'
    }
}
New-Item -ItemType Directory -Path $taskStartup -Force | Out-Null
New-Item -ItemType Directory -Path $taskRuntime -Force | Out-Null
$taskShortcut = $taskShell.CreateShortcut($taskShortcutPath)
$taskShortcut.TargetPath = $taskPythonW
$taskShortcut.Arguments = '-X utf8 "' + $taskWatcherPath + '" --home "' + $taskPaths.home + '"'
$taskShortcut.WorkingDirectory = $taskRoot
$taskShortcut.WindowStyle = 7
$taskShortcut.Description = 'Local Codex-open watcher; no model calls while watching.'
$taskShortcut.Save()
$taskConfig | Add-Member -NotePropertyName auto_start_on_codex_open -NotePropertyValue $true -Force
$taskConfig | Add-Member -NotePropertyName autostart_watcher_on_windows_logon -NotePropertyValue $true -Force
[IO.File]::WriteAllText($taskConfigPath, (($taskConfig | ConvertTo-Json -Depth 20) + "`n"), [Text.UTF8Encoding]::new($false))
$taskCurrent = & $taskPythonPath -X utf8 $taskWatcherPath --status | ConvertFrom-Json
if (-not $taskCurrent.watcher_running) {
    Start-Process -FilePath $taskPythonW -ArgumentList @('-X','utf8',('"' + $taskWatcherPath + '"'),'--home',('"' + $taskPaths.home + '"')) -WorkingDirectory $taskRoot -WindowStyle Hidden | Out-Null
}
$taskReceipt = [ordered]@{
    shortcut = $taskShortcutPath
    target = $taskPythonW
    arguments = $taskShortcut.Arguments
    shortcut_sha256 = (Get-FileHash -LiteralPath $taskShortcutPath -Algorithm SHA256).Hash.ToLowerInvariant()
    profile = $taskPaths.home
    installed_at = (Get-Date -Format o)
    user_only = $true
    starts_codex = $false
}
[IO.File]::WriteAllText((Join-Path $taskRuntime 'autostart-install.json'), ($taskReceipt | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
$taskReceipt | ConvertTo-Json
