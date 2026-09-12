@echo off
echo Starting Railway Block Planning Platform (SIH 2026 PS 26027)...
if not exist node_modules (
    echo Installing dependencies...
    call npm.cmd install
)
start http://localhost:3000
node server.js
pause
