# 原材料价格监控面板

星辰科技供应链管理中心 - 原材料价格实时监控网页

## 功能

- **今日价格概览**：11种关键材料实时价格卡片，涨跌一目了然
- **价格走势图**：支持7天/30天/90天历史走势查看
- **历史数据查询**：完整历史价格表格，支持CSV导出
- **行业资讯**：稀土、硅钢、有色市场动态

## 技术栈

- HTML5 + Tailwind CSS（响应式布局）
- Chart.js（数据可视化）
- 纯前端实现，无需后端服务

## 数据更新

数据每日自动更新：
1. 11:30 自动抓取SMM最新价格
2. 导出JSON数据文件
3. 推送至GitHub Pages自动部署

## 部署

### GitHub Pages（推荐）

1. 将 `website/` 目录内容推送至GitHub仓库
2. 启用 GitHub Pages（Settings → Pages → Source: Deploy from a branch）
3. 选择 `main` 分支，`/ (root)` 目录
4. 访问 `https://[username].github.io/[repo-name]/`

### 本地预览

```bash
cd website
python3 -m http.server 8080
# 访问 http://localhost:8080
```

## 文件结构

```
website/
├── index.html          # 主页面
├── css/
│   └── style.css       # 样式文件
├── js/
│   └── app.js          # 主逻辑
├── data/
│   ├── prices.json     # 价格数据（自动更新）
│   └── industry.json   # 行业资讯
└── README.md
```

## 材料清单

| 代码 | 名称 | 类别 |
|:---|:---|:---|
| CU | 电解铜 | 有色 |
| ADC12 | 铝合金锭 | 有色 |
| B35A300 | 硅钢B35A300 | 硅钢 |
| B50A350 | 硅钢B50A350 | 硅钢 |
| B50A470 | 硅钢B50A470 | 硅钢 |
| B50A600 | 硅钢B50A600 | 硅钢 |
| REO | 镨钕氧化物 | 稀土 |
| REN | 镨钕金属 | 稀土 |
| TB | 金属铽 | 稀土 |
| CE | 铈金属 | 稀土 |
| DYFE | 镝铁合金 | 稀土 |

## 数据来源

- 上海有色网 (SMM): https://hq.smm.cn

## 更新日志

- 2026-04-08: v1.0 初始版本，11种材料价格监控
