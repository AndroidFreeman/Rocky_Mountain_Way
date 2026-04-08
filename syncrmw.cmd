@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

for /f "tokens=*" %%i in ('git symbolic-ref --short -q HEAD') do set CURRENT_BRANCH=%%i
if "!CURRENT_BRANCH!"=="" set CURRENT_BRANCH=main

echo [1/3] 正在暂存并提交本地更改...
git add .
:: 检查是否有更改需要提交，避免 commit 报错导致脚本中断
git diff-index --quiet HEAD -- || git commit -m "Sync by %USERNAME% at %date% %time%"

echo [2/3] 正在从远程拉取更新 (Rebase)...
:: 此时本地已提交，工作区干净，可以安全执行 rebase
git pull origin !CURRENT_BRANCH! --rebase

if %errorlevel% neq 0 (
    echo [警告] 自动合并失败，可能存在代码冲突。
    echo 请手动解决冲突后再提交。
    pause
    exit /b
)

echo [3/3] 正在推送到远程仓库...
git push origin !CURRENT_BRANCH!

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo 同步成功！
    echo ========================================
) else (
    echo [错误] 推送失败，请检查网络或权限。
)

pause