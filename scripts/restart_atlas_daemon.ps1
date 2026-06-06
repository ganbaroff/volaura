# scripts/restart_atlas_daemon.ps1
# Canonical lock-aware daemon status/restart/start/stop wrapper.
# Replaces ad-hoc `Stop-Process; Start-Process python ...` operator commands.
#
# Usage:
#   pwsh scripts\restart_atlas_daemon.ps1 -Action status
#   pwsh scripts\restart_atlas_daemon.ps1 -Action restart -WaitSeconds 300
#   pwsh scripts\restart_atlas_daemon.ps1 -Action start
#   pwsh scripts\restart_atlas_daemon.ps1 -Action stop
#
# Safety contract:
#   - Only stops python.exe processes whose CommandLine contains atlas_swarm_daemon.py
#   - Waits for current_task_id to clear (up to -WaitSeconds) before stopping
#   - Never touches queue files
#   - Never deletes daemon lock manually
#   - Never runs git commands

[CmdletBinding()]
param(
    [ValidateSet('status','restart','start','stop')]
    [string]$Action = 'status',
    [int]$WaitSeconds = 180,
    [int]$PollSeconds = 5
)

$ErrorActionPreference = 'Stop'
$RepoRoot   = 'C:\Projects\VOLAURA'
$HealthFile = Join-Path $RepoRoot 'memory\atlas\runtime\daemon-health.json'

function Get-DaemonProcesses {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine -match 'atlas_swarm_daemon\.py' }
}

function Read-Health {
    if (-not (Test-Path $HealthFile)) { return $null }
    try {
        return (Get-Content $HealthFile -Raw -Encoding UTF8 | ConvertFrom-Json)
    } catch {
        return $null
    }
}

function Print-Status {
    $procs = @(Get-DaemonProcesses)
    $health = Read-Health
    Write-Host '=== Atlas Swarm Daemon Status ==='
    Write-Host ("Process count: {0}" -f $procs.Count)
    foreach ($p in $procs) {
        Write-Host ("  PID {0} parent {1} started {2}" -f $p.ProcessId, $p.ParentProcessId, $p.CreationDate)
    }
    if ($health) {
        Write-Host ("Health pid:           {0}" -f $health.pid)
        Write-Host ("Health status:        {0}" -f $health.status)
        Write-Host ("Current task:         {0}" -f $health.current_task_id)
        Write-Host ("Last completed task:  {0}" -f $health.last_completed_task_id)
        Write-Host ("Git commit:           {0}" -f $health.git_commit)
        if ($health.queue_counts) {
            $qc = $health.queue_counts
            Write-Host ("Queue counts:         pending={0} in_progress={1} done={2} failed={3}" -f $qc.pending, $qc.in_progress, $qc.done, $qc.failed)
        }
    } else {
        Write-Host 'Health file: missing or unreadable'
    }
    if ($procs.Count -ne 1) {
        Write-Host ("STATUS: NOT_OK ({0} processes)" -f $procs.Count)
        return 1
    }
    if (-not $health -or $health.pid -ne $procs[0].ProcessId) {
        Write-Host 'STATUS: PID_MISMATCH (lock/health vs live process)'
        return 2
    }
    Write-Host 'STATUS: OK'
    return 0
}

function Wait-DaemonIdle {
    param([int]$Timeout)
    $deadline = (Get-Date).AddSeconds($Timeout)
    while ((Get-Date) -lt $deadline) {
        $h = Read-Health
        if (-not $h) { return $false }
        if (-not $h.current_task_id) { return $true }
        $remaining = [int]($deadline - (Get-Date)).TotalSeconds
        Write-Host ("Daemon busy on {0} -- waiting ({1}s remaining)..." -f $h.current_task_id, $remaining)
        Start-Sleep -Seconds $PollSeconds
    }
    return $false
}

function Stop-Daemon {
    param([int]$Timeout)
    $h = Read-Health
    if ($h -and $h.current_task_id) {
        Write-Host ("Daemon currently processing {0}; will wait up to {1}s" -f $h.current_task_id, $Timeout)
        if (-not (Wait-DaemonIdle -Timeout $Timeout)) {
            Write-Host 'Daemon still processing after wait -- refusing to stop'
            return 1
        }
    }
    $procs = @(Get-DaemonProcesses)
    foreach ($p in $procs) {
        if ($p.Name -eq 'python.exe' -and $p.CommandLine -match 'atlas_swarm_daemon\.py') {
            Write-Host ("Stopping PID {0}" -f $p.ProcessId)
            Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        }
    }
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline) {
        $remaining = @(Get-DaemonProcesses)
        if ($remaining.Count -eq 0) {
            Write-Host 'All daemon processes stopped.'
            return 0
        }
        Start-Sleep -Seconds 1
    }
    Write-Host 'Some daemon processes still alive after 30s'
    return 1
}

function Start-Daemon {
    $env:ATLAS_DAEMON_START_REASON = 'operator_restart_script'
    Write-Host 'Starting daemon (Hidden window, ATLAS_DAEMON_START_REASON=operator_restart_script)...'
    Start-Process -FilePath python -ArgumentList 'scripts\atlas_swarm_daemon.py' `
        -WorkingDirectory $RepoRoot -WindowStyle Hidden | Out-Null
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 2
        $procs = @(Get-DaemonProcesses)
        $h = Read-Health
        if ($procs.Count -eq 1 -and $h -and $h.pid -eq $procs[0].ProcessId) {
            Write-Host ("Daemon started: PID {0}, health.git_commit {1}" -f $h.pid, $h.git_commit)
            return 0
        }
    }
    Write-Host 'Daemon did not converge (lock+health match) within 30s'
    return 1
}

switch ($Action) {
    'status' {
        exit (Print-Status)
    }
    'stop' {
        exit (Stop-Daemon -Timeout $WaitSeconds)
    }
    'start' {
        $procs = @(Get-DaemonProcesses)
        if ($procs.Count -ge 1) {
            Write-Host 'Daemon already running.'
            exit (Print-Status)
        }
        exit (Start-Daemon)
    }
    'restart' {
        $stopCode = Stop-Daemon -Timeout $WaitSeconds
        if ($stopCode -ne 0) {
            Write-Host ("Stop failed (rc={0}), aborting restart" -f $stopCode)
            exit $stopCode
        }
        Start-Sleep -Seconds 2
        exit (Start-Daemon)
    }
}
