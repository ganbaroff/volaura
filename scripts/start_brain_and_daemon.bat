@echo off
echo Starting VOLAURA Swarm Brain + Daemon...
echo.

cd /d C:\Projects\VOLAURA

echo [1/2] Starting Daemon (17-agent swarm executor)...
start /B pythonw scripts/atlas_swarm_daemon.py
echo       Daemon started.

echo [2/2] Starting Gemma4 Brain (strategy + task creation)...
start /B pythonw scripts/gemma4_brain.py
echo       Brain started.

echo.
echo Both processes running in background.
echo Brain thinks every 5 minutes. Daemon polls every 20 seconds.
echo Logs: memory/atlas/work-queue/daemon.log.jsonl
echo       memory/atlas/work-queue/brain.log.jsonl
echo.
echo Press any key to exit this window (processes keep running)...
pause >nul
