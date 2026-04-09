@echo off
chcp 65001 > nul
REM 原材料价格监控 - 自动更新脚本 (Windows版)
REM 每日11:30执行：抓取价格 → 导出数据 → 推送到GitHub

setlocal enabledelayedexpansion

REM 配置
set "PROJECT_DIR=%USERPROFILE%\Documents\price-monitor"
set "GITHUB_REPO_DIR=%PROJECT_DIR%\github-repo"
set "LOG_FILE=%PROJECT_DIR%\logs\auto-update.log"
set "DATE=%date:~0,4%-%date:~5,2%-%date:~8,2%"
set "TIME=%time:~0,5%"

REM 确保日志目录存在
if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"

echo =======================================
echo 开始自动更新: %DATE% %TIME%
echo =======================================
echo [%DATE% %TIME%] 开始自动更新 >> "%LOG_FILE%"

REM 1. 进入项目目录
cd /d "%PROJECT_DIR%"

REM 2. 运行爬虫抓取最新价格
echo [1/4] 抓取最新价格数据...
echo [%DATE% %TIME%] [1/4] 抓取最新价格数据... >> "%LOG_FILE%"

python3 scripts\crawl_prices.py >> "%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    echo ✗ 价格抓取失败
    echo [%DATE% %TIME%] ✗ 价格抓取失败 >> "%LOG_FILE%"
    exit /b 1
)
echo ✓ 价格抓取完成
echo [%DATE% %TIME%] ✓ 价格抓取完成 >> "%LOG_FILE%"

REM 3. 导出网页数据
echo [2/4] 导出网页数据...
echo [%DATE% %TIME%] [2/4] 导出网页数据... >> "%LOG_FILE%"

python3 scripts\export_web_data.py >> "%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    echo ✗ 数据导出失败
    echo [%DATE% %TIME%] ✗ 数据导出失败 >> "%LOG_FILE%"
    exit /b 1
)
echo ✓ 数据导出完成
echo [%DATE% %TIME%] ✓ 数据导出完成 >> "%LOG_FILE%"

REM 4. 复制到GitHub仓库目录
echo [3/4] 同步到GitHub仓库...
echo [%DATE% %TIME%] [3/4] 同步到GitHub仓库... >> "%LOG_FILE%"

copy /y "%PROJECT_DIR%\website\data\prices.json" "%GITHUB_REPO_DIR%\data\prices.json" > nul
copy /y "%PROJECT_DIR%\website\data\industry.json" "%GITHUB_REPO_DIR%\data\industry.json" > nul

REM 5. 推送到GitHub
cd /d "%GITHUB_REPO_DIR%"

git diff --quiet
if %errorlevel% equ 0 (
    echo ✓ 数据无变化，跳过提交
    echo [%DATE% %TIME%] ✓ 数据无变化，跳过提交 >> "%LOG_FILE%"
) else (
    echo [4/4] 推送到GitHub...
    echo [%DATE% %TIME%] [4/4] 推送到GitHub... >> "%LOG_FILE%"
    
    git add data\ >> "%LOG_FILE%" 2>&1
    git commit -m "Update prices %DATE%" >> "%LOG_FILE%" 2>&1
    git push origin main >> "%LOG_FILE%" 2>&1
    
    if %errorlevel% equ 0 (
        echo ✓ 推送完成
        echo ✓ 网站将在2分钟后自动更新
        echo [%DATE% %TIME%] ✓ 推送完成 >> "%LOG_FILE%"
    ) else (
        echo ✗ 推送失败，请检查网络或认证
        echo [%DATE% %TIME%] ✗ 推送失败 >> "%LOG_FILE%"
        exit /b 1
    )
)

echo =======================================
echo 自动更新完成
echo =======================================
echo [%DATE% %TIME%] 自动更新完成 >> "%LOG_FILE%"

endlocal
