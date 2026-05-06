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

---

## 🔧 配置手动刷新

网页上点击 **"刷新数据"** 按钮可手动触发数据更新，首次需要配置：

### 1. 获取GitHub Token

1. 访问 https://github.com/settings/tokens
2. 点击 **Generate new token (classic)**
3. 勾选以下权限：
   - ✅ `repo`（仓库访问）
   - ✅ `workflow`（工作流操作）
4. 点击 **Generate token**
5. **复制生成的token**（以 `ghp_` 开头）

### 2. 网页上配置

1. 打开网站，点击顶部 **⚙️ 配置** 按钮
2. 输入GitHub仓库路径，格式：`用户名/仓库名`
   - 例如：`zhangsan/raw-material-prices`
3. 粘贴刚才复制的GitHub Token
4. 点击确定保存

### 3. 使用手动刷新

配置完成后，点击 **🔄 刷新数据** 按钮即可手动触发数据更新。

---

## 📊 功能介绍

| 功能 | 说明 |
|:---|:---|
| **今日价格概览** | 11种材料实时价格卡片，涨跌一目了然 |
| **价格走势图** | 支持7天/30天/90天/半年/一年/全部历史走势 |
| **行业资讯** | 稀土、硅钢、有色市场动态 |
| **历史数据表** | 完整历史价格表格，支持CSV导出 |
| **手动刷新** | 点击按钮立即触发数据更新 |

---

## 📁 文件结构

```
github-repo/
├── .github/workflows/
│   └── daily-update.yml    # GitHub Actions配置
├── css/
│   └── style.css           # 样式文件
├── data/
│   ├── prices.json         # 价格数据（自动更新）
│   └── industry.json       # 行业资讯
├── industry/               # 行业资讯图片
├── js/
│   └── app.js              # 主逻辑（含手动刷新功能）
├── scripts/
│   └── crawl_prices.py     # 爬虫脚本
├── index.html              # 网站首页
└── README.md               # 本文件
```

---

## 🔧 常见问题

### Q: 为什么有些材料抓取失败？
A: 上海有色网可能有反爬虫机制，或页面结构变化。系统会记录成功抓取的材料，失败的在下次重试。

### Q: 如何修改定时时间？
A: 编辑 `.github/workflows/daily-update.yml` 中的 `cron` 表达式：
```yaml
# 每天11:30 UTC+8
- cron: '30 3 * * *'
```

### Q: Token安全吗？
A: Token只保存在浏览器本地存储中，不会上传到服务器。建议设置token有效期（如90天），到期后重新生成。

### Q: 不配置Token能用吗？
A: 可以。定时任务会自动运行（每天11:30），只是不能手动触发刷新。

---

## 📞 维护

- **自动更新**：每天11:30自动抓取并部署
- **监控日志**：在 GitHub Actions 中查看每次运行的日志
- **手动触发**：可随时在网页或GitHub Actions页面手动运行

---

星辰科技供应链管理中心