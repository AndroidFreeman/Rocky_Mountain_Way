@echo off
:: 设置编码为UTF-8防止中文乱码
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 自动获取当前分支名称 (master 或 main)
for /f "tokens=*" %%i in ('git symbolic-ref --short -q HEAD') do set CURRENT_BRANCH=%%i
if "!CURRENT_BRANCH!"=="" set CURRENT_BRANCH=main

echo [1/4] 正在检查远程更新 (Pull) 分支: !CURRENT_BRANCH!...

:: 尝试拉取。如果是新项目，即便远程没分支也不会直接崩溃
git pull origin !CURRENT_BRANCH! --rebase

echo [2/4] 正在添加更改...
git add .

echo [3/4] 正在提交更改...
set commit_msg=Sync by %USERNAME% at %date% %time%
git commit -m "%commit_msg%"

echo [4/4] 正在推送到远程仓库...
:: 第一次推送时强制关联分支，确保后续不再报错
git push -u origin !CURRENT_BRANCH!

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo 同步成功！代码已同步至 !CURRENT_BRANCH!
    echo ========================================
) else (
    echo [错误] 同步过程中出现问题，请检查权限或网络。
)

pause