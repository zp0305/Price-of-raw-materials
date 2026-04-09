# 原材料价格监控 - GitHub Actions自动版

星辰科技供应链管理中心 - 原材料价格实时监控

## 🚀 快速部署指南

### 第一步：创建GitHub仓库

1. 访问 https://github.com/new
2. 仓库名称：`raw-material-prices`（或其他名称）
3. 选择 **Public**（公开）或 **Private**（私有）
4. 点击 **Create repository**

### 第二步：上传文件

将 `github-repo` 目录下的所有文件上传到仓库：

```bash
cd github-repo
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/你的用户名/raw-material-prices.git
git push -u origin main
```

或者在GitHub网页上直接上传文件。

### 第三步：启用GitHub Pages

1. 进入仓库 → **Settings** → **Pages**
2. **Source** 选择 **GitHub Actions**
3. 系统会自动识别 `.github/workflows/daily-update.yml`

### 第四步：测试运行

1. 进入仓库 → **Actions** 标签
2. 点击 **Daily Price Update**
3. 点击 **Run workflow** 手动触发一次
4. 等待运行完成（约1-2分钟）

### 第五步：访问网站

部署完成后，访问：
```
https://你的用户名.github.io/raw-material-prices/
```

## 📊 功能

- **自动抓取**：每天11:30自动抓取最新价格
- **实时监控**：16种关键材料价格卡片
- **涨跌显示**：直观显示价格变化趋势
- **无需服务器**：完全免费，使用GitHub基础设施

## 🛠️ 技术栈

- **GitHub Actions**：定时任务 + 自动部署
- **GitHub Pages**：静态网站托管（免费）
- **Python + Requests**：网页抓取
- **纯HTML/CSS/JS**：前端展示

## 📁 文件说明

```
github-repo/
├── .github/workflows/
│   └── daily-update.yml    # GitHub Actions配置
├── data/
│   ├── prices.json         # 历史价格数据
│   └── today.json          # 今日数据快照
├── scripts/
│   └── crawl_prices.py     # 爬虫脚本
├── index.html              # 网站首页
└── README.md               # 本文件
```

## 🔧 常见问题

### Q: 为什么有些材料抓取失败？
A: 上海有色网可能有反爬虫机制，或页面结构变化。系统会记录成功抓取的材料，失败的在下次重试。

### Q: 如何修改定时时间？
A: 编辑 `.github/workflows/daily-update.yml` 中的 `cron` 表达式：
```yaml
# 每天11:30 UTC+8
- cron: '30 3 * * *'
```

### Q: 可以添加更多材料吗？
A: 可以。编辑 `scripts/crawl_prices.py`，在 `SOURCES` 字典中添加新的URL和解析规则。

### Q: 数据存储在哪里？
A: 数据保存在 `data/prices.json` 中，作为仓库的一部分。保留90天历史数据。

## 📞 维护

- **自动更新**：无需人工干预
- **监控日志**：在 GitHub Actions 中查看每次运行的日志
- **手动触发**：可随时手动运行 workflow 测试

---

星辰科技供应链管理中心
