@echo off
echo ===================================================
echo        TETHERGUARD HACKATHON LAUNCHER
echo ===================================================
echo.
echo Starting the central Relay Server in the background...
start "TetherGuard Relay Router" /MIN cmd /c ".\venv\Scripts\python.exe relay_server.py"

:: Give the relay server a second to bind to the port
timeout /t 2 /nobreak > NUL

echo Starting the Desktop Agent (UI)...
start "TetherGuard Desktop Agent" cmd /c ".\venv\Scripts\python.exe -m tetherguard.app --demo"

echo.
echo Both systems are running! You can close this window.
exit
