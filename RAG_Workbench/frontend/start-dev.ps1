#!/usr/bin/env pwsh
# Quick Start Script for RAG Workbench Frontend

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   RAG Workbench Frontend Launcher   " -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if node_modules exists
if (-not (Test-Path ".\node_modules")) {
    Write-Host "[INFO] node_modules not found. Installing dependencies..." -ForegroundColor Yellow
    npm install

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] npm install failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "[SUCCESS] Dependencies installed!" -ForegroundColor Green
} else {
    Write-Host "[INFO] Dependencies already installed." -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting Vite development server..." -ForegroundColor Cyan
Write-Host ""
Write-Host "The app will be available at: http://localhost:5173" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the dev server
npm run dev

