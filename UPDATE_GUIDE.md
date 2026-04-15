# 网站更新指南

## 需要新增/修改的文件

### 1. 新增文件
```
.github/workflows/daily-update.yml  ← GitHub Actions工作流（核心！）
requirements.txt                     ← Python依赖
```

### 2. 修改文件
```
scripts/crawl_prices.py     ← 增强版价格爬虫
scripts/crawl_industry.py   ← 增强版行业资讯爬虫
```

## 更新步骤

### 方法一：直接推送（推荐）

```bash
# 1. 进入仓库目录
cd /path/to/your/Price-of-raw-materials

# 2. 复制新文件到对应位置
# 创建 .github/workflows 目录
mkdir -p .github/workflows

# 3. 添加所有文件
git add .github/workflows/daily-update.yml
git add requirements.txt
git add scripts/crawl_prices.py
git add scripts/crawl_industry.py

# 4. 提交
git commit -m "feat: 添加自动更新功能

- 新增 GitHub Actions 工作流，每天11:30自动爬取数据
- 爬虫增加随机UA、随机延时、多轮重试机制
- 失败时自动使用上次数据作为降级方案"

# 5. 推送
git push origin main
```

### 方法二：GitHub网页上传

1. 打开 https://github.com/zp0305/Price-of-raw-materials
2. 点击 "Add file" → "Upload files"
3. 按目录结构上传文件（注意 .github/workflows 目录需要先创建）

## 工作流说明

- **执行时间**: 每天 11:30 (北京时间)
- **重试机制**: 失败后自动重试3次
- **数据检查**: 确保至少获取8种材料价格
- **失败通知**: 自动创建Issue提醒

## 首次测试

推送后，可以在 GitHub Actions 页面手动触发测试：
1. 进入仓库 → Actions 标签页
2. 选择 "Daily Price Update" 工作流
3. 点击 "Run workflow" 手动执行

## 注意事项

1. **首次运行可能需要授权**: GitHub Actions 需要有写入权限
   - Settings → Actions → General → Workflow permissions
   - 选择 "Read and write permissions"

2. **反爬机制**: 已添加随机UA和延时，但仍可能被拦截
   - 如持续失败，可能需要考虑其他数据源

3. **镝铁合金**: SMM网页端无此数据，目前使用历史数据
   - 建议从APP手动录入或寻找其他数据源
