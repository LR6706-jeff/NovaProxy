content = r'''@echo off
chcp 936 >nul
title 端口清理工具

:menu
cls
echo.
echo  ============================================
echo           端口清理工具 v1.0
echo  ============================================
echo.
echo   [1] 清理端口 3001 (NovaProxy 默认)
echo   [2] 清理自定义端口
echo   [3] 查看所有监听端口
echo   [0] 退出
echo.

set /p choice=请选择 (0-3): 

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
set /p port=请输入端口号: 
if "%port%"=="" goto menu
goto killport

:killport
echo.
echo 正在查找占用端口 %port% 的进程...
echo.

set pid=
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%port% " ^| findstr "LISTENING"') do set pid=%%a

if "%pid%"=="" (
    echo [OK] 端口 %port% 未被占用
) else (
    echo [!] 发现 PID: %pid% 占用端口 %port%
    echo.
    tasklist /fi "PID eq %pid%"
    echo.
    set /p confirm=是否终止该进程? (Y/N): 
    if /i "%confirm%"=="Y" (
        taskkill /F /PID %pid%
        echo [OK] 进程已终止，端口 %port% 已释放
    ) else (
        echo 已取消
    )
)
echo.
pause
goto menu

:listall
echo.
echo 当前监听的端口:
echo --------------------------------------------
netstat -ano | findstr "LISTENING"
echo --------------------------------------------
echo.
pause
goto menu
'''

with open('端口清理.bat', 'w', encoding='gbk', newline='\r\n') as f:
    f.write(content)
print('端口清理.bat 创建成功!')
