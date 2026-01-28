@echo off
chcp 936 >nul
title Port Cleaner

:menu
cls
echo.
echo  ============================================
echo        Port Cleaner v1.0
echo  ============================================
echo.
echo   [1] Kill port 3001 (NovaProxy default)
echo   [2] Kill custom port
echo   [3] List all listening ports
echo   [0] Exit
echo.

set /p choice=Select (0-3): 

if "%choice%"=="1" goto kill3001
if "%choice%"=="2" goto customport
if "%choice%"=="3" goto listall
if "%choice%"=="0" exit
goto menu

:kill3001
set port=3001
goto killport

:customport
echo.
set /p port=Enter port number: 
if "%port%"=="" goto menu
goto killport

:killport
echo.
echo Finding process on port %port%...
echo.

set pid=
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%port% " ^| findstr "LISTENING"') do set pid=%%a

if "%pid%"=="" (
    echo [OK] Port %port% is not in use
) else (
    echo [!] Found PID: %pid% using port %port%
    echo.
    tasklist /fi "PID eq %pid%"
    echo.
    set /p confirm=Kill this process? (Y/N): 
    if /i "%confirm%"=="Y" (
        taskkill /F /PID %pid%
        echo [OK] Process killed, port %port% is now free
    ) else (
        echo Cancelled
    )
)
echo.
pause
goto menu

:listall
echo.
echo Listening ports:
echo --------------------------------------------
netstat -ano | findstr "LISTENING"
echo --------------------------------------------
echo.
pause
goto menu
