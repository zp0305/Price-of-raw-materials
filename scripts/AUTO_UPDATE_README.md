# 自动更新设置指南

## 概述

自动更新脚本每日执行以下操作：
1. 抓取SMM最新价格数据
2. 导出网页所需的JSON文件
3. 推送到GitHub仓库
4. GitHub Pages自动部署更新

## 文件说明

| 文件 | 用途 | 适用系统 |
|:---|:---|:---|
| `auto-update.sh` | Linux/macOS自动更新脚本 | Linux/macOS |
| `auto-update.bat` | Windows自动更新脚本 | Windows |

## 前置条件

1. **Python 3** 已安装
2. **Git** 已安装并配置GitHub认证
3. **依赖包** 已安装：
   ```bash
   pip install requests
   ```

4. **GitHub仓库** 已创建并初始化

## 设置步骤

### Step 1：配置脚本路径

编辑脚本文件，修改 `PROJECT_DIR` 为你的实际项目路径：

**Linux/macOS (auto-update.sh)**:
```bash
PROJECT_DIR="/home/yourname/price-monitor"
```

**Windows (auto-update.bat)**:
```batch
set "PROJECT_DIR=C:\Users\yourname\Documents\price-monitor"
```

### Step 2：测试手动运行

先手动运行一次，确保无错误：

```bash
# Linux/macOS
chmod +x scripts/auto-update.sh
./scripts/auto-update.sh

# Windows
scripts\auto-update.bat
```

### Step 3：设置定时任务

#### Linux/macOS - Cron

```bash
# 编辑crontab
crontab -e

# 添加以下内容（每天11:30执行）
30 11 * * * /bin/bash /path/to/price-monitor/scripts/auto-update.sh

# 保存退出
```

#### Windows - 任务计划程序

1. 打开「任务计划程序」
2. 点击「创建基本任务」
3. **名称**: 价格监控自动更新
4. **触发器**: 每天 11:30
5. **操作**: 启动程序
   - 程序: `C:\Windows\System32\cmd.exe`
   - 参数: `/c "C:\path\to\price-monitor\scripts\auto-update.bat"`
6. 完成

#### macOS - launchd（推荐）

创建 `~/Library/LaunchAgents/com.xingchen.price-monitor.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.xingchen.price-monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/path/to/price-monitor/scripts/auto-update.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>11</integer>
        <key>Minute</key>
        <integer>30</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/path/to/price-monitor/logs/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/price-monitor/logs/launchd-error.log</string>
</dict>
</plist>
```

加载任务：
```bash
launchctl load ~/Library/LaunchAgents/com.xingchen.price-monitor.plist
```

## 日志查看

更新日志保存在 `logs/auto-update.log`：

```bash
# 查看最新日志
tail -f logs/auto-update.log

# 查看完整日志
cat logs/auto-update.log
```

## 故障排查

### 问题1：推送失败（认证错误）

**原因**: GitHub认证过期或未配置

**解决**:
```bash
# 使用SSH方式（推荐）
git remote set-url origin git@github.com:zp0305/price-monitor.git

# 或更新HTTPS凭证
git config --global credential.helper cache
```

### 问题2：爬虫抓取失败

**原因**: 网站结构变化或网络问题

**解决**:
- 检查网络连接
- 查看 `crawl_prices.py` 是否需要更新解析规则

### 问题3：定时任务未执行

**原因**: 路径错误或权限问题

**解决**:
```bash
# 检查脚本权限
chmod +x scripts/auto-update.sh

# 测试手动执行
./scripts/auto-update.sh

# Linux检查cron日志
grep CRON /var/log/syslog
```

## 手动触发更新

如需立即更新（不等待定时任务）：

```bash
./scripts/auto-update.sh
```

更新完成后，访问 `https://zp0305.github.io/price-monitor/` 查看最新数据。
