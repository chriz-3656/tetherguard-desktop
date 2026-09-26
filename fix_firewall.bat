@echo off
echo ===================================================
echo     TETHERGUARD FIREWALL FIX (RUN AS ADMIN)
echo ===================================================
echo.
echo Allowing inbound connections to Relay Server on Port 8080...
netsh advfirewall firewall add rule name="TetherGuard Relay (Port 8080)" dir=in action=allow protocol=TCP localport=8080

echo.
echo Done! You can close this window and try the app again.
pause
