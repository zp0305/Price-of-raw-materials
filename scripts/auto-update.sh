#!/bin/bash
# -*- coding: utf-8 -*-
# 原材料价格监控 - 自动更新脚本
# 每日11:30执行：抓取价格 → 导出数据 → 推送到GitHub

set -e  # 遇到错误立即退出

# 配置
PROJECT_DIR="/root/.openclaw/workspace/projects/原材料价格监控"
GITHUB_REPO_DIR="$PROJECT_DIR/github-repo"
LOG_FILE="$PROJECT_DIR/logs/auto-update.log"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)

# 确保日志目录存在
mkdir -p "$PROJECT_DIR/logs"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========================================"
log "开始自动更新: $DATE $TIME"
log "========================================"

# 1. 进入项目目录
cd "$PROJECT_DIR"

# 2. 运行爬虫抓取最新价格
log "[1/4] 抓取最新价格数据..."
if python3 scripts/crawl_prices.py >> "$LOG_FILE" 2>&1; then
    log "✓ 价格抓取完成"
else
    log "✗ 价格抓取失败，尝试浏览器补充..."
    # 可以在这里添加浏览器抓取的备用逻辑
fi

# 3. 导出网页数据
log "[2/4] 导出网页数据..."
if python3 scripts/export_web_data.py >> "$LOG_FILE" 2>&1; then
    log "✓ 数据导出完成"
else
    log "✗ 数据导出失败"
    exit 1
fi

# 4. 复制到GitHub仓库目录
log "[3/4] 同步到GitHub仓库..."
cp "$PROJECT_DIR/website/data/prices.json" "$GITHUB_REPO_DIR/data/prices.json"
cp "$PROJECT_DIR/website/data/industry.json" "$GITHUB_REPO_DIR/data/industry.json"

# 5. 推送到GitHub
cd "$GITHUB_REPO_DIR"

# 检查是否有变更
if git diff --quiet; then
    log "✓ 数据无变化，跳过提交"
else
    log "[4/4] 推送到GitHub..."
    git add data/
    git commit -m "Update prices $DATE

- Auto update at $TIME
- Data source: SMM Shanghai" >> "$LOG_FILE" 2>&1
    
    if git push origin main >> "$LOG_FILE" 2>&1; then
        log "✓ 推送完成"
        log "✓ 网站将在2分钟后自动更新"
    else
        log "✗ 推送失败，请检查网络或认证"
        exit 1
    fi
fi

log "========================================"
log "自动更新完成"
log "========================================"
