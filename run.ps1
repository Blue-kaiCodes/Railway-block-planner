# Railway Block Planning Platform (SIH 2026 PS 26027)
# Run directly in PowerShell: .\run.ps1 or powershell -ExecutionPolicy Bypass -File .\run.ps1

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Indian Railways Corridor Block Planning & Optimization   " -ForegroundColor Green
Write-Host " SIH 2026 Problem Statement: PS 26027                     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not (Test-Path "\node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm.cmd install
}

Write-Host "Launching Railway Block Planner on http://localhost:3000..." -ForegroundColor Green
Start-Process "http://localhost:3000"

node "\server.js"
