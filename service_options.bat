@echo off
:: Check for administrative permissions
:: If not running as administrator, prompt to run as administrator
openfiles >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrative privileges...
    powershell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

setlocal

:: Define the service name
set "SERVICE_NAME=EJMonitoringService"

:: Set service to start automatically
echo Configuring service to start automatically...
sc config %SERVICE_NAME% start= auto
if %errorlevel% equ 0 (
    echo [SC] ChangeServiceConfig SUCCESS
    echo Service configured to start automatically.
) else (
    echo Failed to configure the service to start automatically.
)

:: Set service recovery options
echo Configuring service recovery options...
sc failure %SERVICE_NAME% reset= 0 actions= restart/5000
if %errorlevel% equ 0 (
    echo [SC] ChangeServiceConfig2 SUCCESS
    echo Service recovery options configured successfully.
) else (
    echo Failed to configure the service recovery options.
)

echo All tasks completed successfully.
pause
