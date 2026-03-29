@echo off
REM Jarvis Daemon — "Hey Jarvis" voice-activated PC control for VOLAURA
REM Run this file to start listening in the background.
REM
REM First-time setup (run once):
REM   pip install openwakeword faster-whisper pyaudio pyautogui groq python-dotenv loguru numpy
REM   If pyaudio fails: pip install pipwin && pipwin install pyaudio

cd /d "%~dp0\.."

echo Starting Jarvis daemon...
echo Say "Hey Jarvis" after startup completes.
echo Press Ctrl+C to stop.
echo.

python -m packages.swarm.jarvis_daemon

pause
