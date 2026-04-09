// 全局数据存储
let priceData = null;
let industryData = null;
let chartInstance = null;
let currentMaterial = null;
let currentRange = 7;
let currentFilter = 'all';
let currentNewsFilter = 'all';

// 材料分类
const materialCategories = {
    'CU': 'cu',
    'ADC12': 'cu',
    'AL6063': 'cu',
    'B35A300': 'sife',
    'B50A310': 'sife',
    'B50A350': 'sife',
    'B50A470': 'sife',
    'B50A600': 'sife',
    'REO': 'rare',
    'REN': 'rare',
    'TB': 'rare',
    'CE': 'rare'
};

// 分类名称映射
const categoryNames = {
    'rare-earth': '稀土',
    'sife': '硅钢',
    'metal': '有色',
    'policy': '政策',
    'supply-chain': '供应链'
};

// 初始化
async function init() {
    await loadData();
    await loadIndustryData();
    renderCards();
    renderChart();
    renderHistoryTable();
    initDateInputs();
    updateTimestamp();
}

// 加载价格数据
async function loadData() {
    try {
        const response = await fetch('data/prices.json');
        priceData = await response.json();
        
        // 设置默认选中的材料
        if (priceData.today.length > 0) {
            currentMaterial = priceData.today[0].code;
        }
        
        // 填充选择器
        populateSelectors();
    } catch (error) {
        console.error('加载数据失败:', error);
        showError('数据加载失败，请刷新页面重试');
    }
}

// 加载行业资讯数据
async function loadIndustryData() {
    try {
        const response = await fetch('data/industry.json');
        industryData = await response.json();
        renderIndustryNews();
    } catch (error) {
        console.error('加载行业资讯失败:', error);
        // 使用备用数据
        industryData = null;
        renderIndustryNews();
    }
}

// 填充下拉选择器
function populateSelectors() {
    const materialSelect = document.getElementById('material-select');
    const historyMaterial = document.getElementById('history-material');
    
    const options = priceData.today.map(m => 
        `<option value="${m.code}">${m.name} (${m.code})</option>`
    ).join('');
    
    materialSelect.innerHTML = options;
    historyMaterial.innerHTML = options;
    
    materialSelect.value = currentMaterial;
    historyMaterial.value = currentMaterial;
    
    materialSelect.addEventListener('change', (e) => {
        currentMaterial = e.target.value;
        updateChart();
        renderHistoryTable();
        highlightCard(currentMaterial);
    });
    
    historyMaterial.addEventListener('change', (e) => {
        currentMaterial = e.target.value;
        updateChart();
        renderHistoryTable();
        highlightCard(currentMaterial);
        document.getElementById('material-select').value = currentMaterial;
    });
}

// 初始化日期输入框
function initDateInputs() {
    const today = new Date().toISOString().split('T')[0];
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    
    const startInput = document.getElementById('export-start');
    const endInput = document.getElementById('export-end');
    
    if (startInput && endInput) {
        startInput.value = thirtyDaysAgo;
        endInput.value = today;
    }
}

// 渲染价格卡片
function renderCards() {
    const container = document.getElementById('price-cards');
    
    const cards = priceData.today.map(m => {
        const category = materialCategories[m.code] || 'all';
        const changeClass = m.change > 0 ? 'price-up' : m.change < 0 ? 'price-down' : 'price-neutral';
        const bgClass = m.change > 0 ? 'bg-up' : m.change < 0 ? 'bg-down' : 'bg-neutral';
        const arrow = m.change > 0 ? '↑' : m.change < 0 ? '↓' : '-';
        const isActive = m.code === currentMaterial ? 'active ring-2 ring-blue-500' : '';
        
        return `
            <div class="price-card ${bgClass} ${isActive} rounded-xl p-4 border border-gray-200" 
                 data-category="${category}" data-code="${m.code}"
                 onclick="selectMaterial('${m.code}')">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-gray-600">${m.name}</span>
                    <span class="text-xs text-gray-400">${m.code}</span>
                </div>
                <div class="text-2xl font-bold text-gray-900 mb-1 price-value">
                    ${formatPrice(m.price)}
                </div>
                <div class="flex items-center justify-between">
                    <span class="text-sm ${changeClass} font-semibold">
                        ${arrow} ${Math.abs(m.change).toLocaleString()}
                    </span>
                    <span class="text-xs text-gray-400">元/吨</span>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = cards;
}

// 选择材料
function selectMaterial(code) {
    currentMaterial = code;
    document.getElementById('material-select').value = code;
    document.getElementById('history-material').value = code;
    updateChart();
    renderHistoryTable();
    highlightCard(code);
}

// 高亮卡片
function highlightCard(code) {
    document.querySelectorAll('.price-card').forEach(card => {
        if (card.dataset.code === code) {
            card.classList.add('active', 'ring-2', 'ring-blue-500');
        } else {
            card.classList.remove('active', 'ring-2', 'ring-blue-500');
        }
    });
}

// 筛选材料
function filterMaterials(category) {
    currentFilter = category;
    
    // 更新按钮状态
    document.querySelectorAll('.filter-btn').forEach(btn => {
        if (btn.dataset.filter === category) {
            btn.classList.add('active', 'bg-blue-500', 'text-white');
            btn.classList.remove('bg-gray-200', 'text-gray-700');
        } else {
            btn.classList.remove('active', 'bg-blue-500', 'text-white');
            btn.classList.add('bg-gray-200', 'text-gray-700');
        }
    });
    
    // 显示/隐藏卡片
    document.querySelectorAll('.price-card').forEach(card => {
        if (category === 'all' || card.dataset.category === category) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// 渲染图表
function renderChart() {
    const ctx = document.getElementById('price-chart').getContext('2d');
    
    chartInstance = new Chart(ctx, {
        type: 'line',
        data: getChartData(),
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y.toLocaleString() + ' 元/吨';
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// 更新图表
function updateChart() {
    if (chartInstance) {
        chartInstance.data = getChartData();
        chartInstance.update();
    }
}

// 获取图表数据
function getChartData() {
    const history = priceData.history[currentMaterial] || [];
    let filtered = history;
    
    // 如果是0，显示全部数据；否则取最近N天
    if (currentRange > 0) {
        filtered = history.slice(0, currentRange);
    }
    
    // 数据点过多时进行采样（超过60个点时）
    const dataPoints = filtered.length;
    let sampled = filtered;
    if (dataPoints > 60) {
        const step = Math.ceil(dataPoints / 60);
        sampled = filtered.filter((_, index) => index % step === 0);
    }
    
    // 反转顺序（从早到晚）
    const sorted = [...sampled].reverse();
    
    const material = priceData.today.find(m => m.code === currentMaterial);
    
    // 根据时间范围决定标签格式
    const labels = sorted.map(h => {
        if (currentRange >= 365 || currentRange === 0) {
            // 长期显示 年-月
            return h.date.slice(0, 7);
        } else if (currentRange >= 90) {
            // 中期显示 月-日
            return h.date.slice(5);
        } else {
            // 短期显示 月-日
            return h.date.slice(5);
        }
    });
    
    return {
        labels: labels,
        datasets: [{
            label: material ? material.name : currentMaterial,
            data: sorted.map(h => h.price),
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.3,
            pointRadius: dataPoints > 60 ? 0 : 3, // 数据点多时不显示圆点
            pointHoverRadius: 5
        }]
    };
}

// 设置图表时间范围
function setChartRange(days) {
    currentRange = days;
    
    // 更新按钮状态
    document.querySelectorAll('.range-btn').forEach(btn => {
        if (parseInt(btn.dataset.range) === days) {
            btn.classList.add('active', 'bg-blue-500', 'text-white');
            btn.classList.remove('bg-gray-200', 'text-gray-700');
        } else {
            btn.classList.remove('active', 'bg-blue-500', 'text-white');
            btn.classList.add('bg-gray-200', 'text-gray-700');
        }
    });
    
    updateChart();
}

// 渲染历史数据表
function renderHistoryTable() {
    const tbody = document.getElementById('history-table');
    const history = priceData.history[currentMaterial] || [];
    
    const rows = history.slice(0, 30).map((h, index) => {
        const prev = history[index + 1];
        const change = prev ? h.price - prev.price : 0;
        const changePercent = prev ? ((change / prev.price) * 100).toFixed(2) : '0.00';
        const changeClass = change > 0 ? 'price-up' : change < 0 ? 'price-down' : 'price-neutral';
        const sign = change > 0 ? '+' : '';
        
        return `
            <tr class="hover:bg-gray-50">
                <td class="px-4 py-3 text-gray-700">${h.date}</td>
                <td class="px-4 py-3 text-right font-mono font-semibold">${h.price.toLocaleString()}</td>
                <td class="px-4 py-3 text-right ${changeClass}">${sign}${change.toLocaleString()}</td>
                <td class="px-4 py-3 text-right ${changeClass}">${sign}${changePercent}%</td>
            </tr>
        `;
    }).join('');
    
    tbody.innerHTML = rows || '<tr><td colspan="4" class="px-4 py-8 text-center text-gray-500">暂无历史数据</td></tr>';
}

// 渲染行业资讯
function renderIndustryNews() {
    const container = document.getElementById('industry-news');
    
    // 使用加载的JSON数据或备用数据
    let news = [];
    if (industryData && industryData.news) {
        news = industryData.news;
    } else {
        // 备用数据
        news = [
            { title: 'SMM分析：稀土价格短期震荡偏弱运行', date: '2026-04-08', category: 'rare-earth', summary: '下游磁材企业按需采购，市场观望情绪浓厚。' },
            { title: '上海市场无取向硅钢报价持稳', date: '2026-04-08', category: 'sife', summary: 'B35A300、B50A350等主流规格价格维持不变。' },
            { title: '电解铜价格上涨1080元/吨', date: '2026-04-08', category: 'metal', summary: '受宏观情绪提振，铜价延续反弹走势。' }
        ];
    }
    
    // 筛选
    if (currentNewsFilter !== 'all') {
        news = news.filter(n => n.category === currentNewsFilter);
    }
    
    const items = news.map(n => {
        const categoryName = categoryNames[n.category] || '其他';
        const hasDetail = n.detail && n.detail.length > n.summary.length;
        return `
            <div class="news-item p-3 rounded-lg hover:bg-gray-50 transition-colors ${n.category}"
                 onclick="toggleNewsDetail(this)"
                 data-expanded="false">
                <div class="flex items-start justify-between mb-1">
                    <h3 class="text-sm font-medium text-gray-800 line-clamp-2 flex-1 mr-2">${n.title}</h3>
                    ${hasDetail ? '<span class="text-blue-500 text-xs expand-icon">展开▼</span>' : ''}
                </div>
                <p class="text-xs text-gray-600 mb-1 summary">${n.summary}</p>
                ${n.detail ? `<p class="text-xs text-gray-500 mt-2 hidden detail border-t border-gray-100 pt-2">${n.detail}</p>` : ''}
                <div class="flex items-center justify-between mt-2">
                    <span class="text-xs text-gray-400">${n.date} · ${n.source || 'SMM'}</span>
                    <span class="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-600">${categoryName}</span>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = items || '<div class="text-center text-gray-500 py-8">暂无相关资讯</div>';
}

// 切换资讯详情显示
function toggleNewsDetail(element) {
    const detail = element.querySelector('.detail');
    const icon = element.querySelector('.expand-icon');
    const summary = element.querySelector('.summary');
    
    if (!detail) return;
    
    const isExpanded = element.dataset.expanded === 'true';
    
    if (isExpanded) {
        detail.classList.add('hidden');
        summary.classList.remove('hidden');
        if (icon) icon.textContent = '展开▼';
        element.dataset.expanded = 'false';
    } else {
        detail.classList.remove('hidden');
        summary.classList.add('hidden');
        if (icon) icon.textContent = '收起▲';
        element.dataset.expanded = 'true';
    }
}

// 筛选行业资讯
function filterNews() {
    const select = document.getElementById('news-filter');
    currentNewsFilter = select.value;
    renderIndustryNews();
}

// 导出CSV（支持时间范围）
function exportCSV() {
    const history = priceData.history[currentMaterial] || [];
    const material = priceData.today.find(m => m.code === currentMaterial);
    
    // 获取时间范围
    const startInput = document.getElementById('export-start');
    const endInput = document.getElementById('export-end');
    
    let startDate = null;
    let endDate = null;
    
    if (startInput && startInput.value) {
        startDate = new Date(startInput.value);
    }
    if (endInput && endInput.value) {
        endDate = new Date(endInput.value);
        endDate.setHours(23, 59, 59, 999); // 包含结束日期全天
    }
    
    // 筛选数据
    let filteredHistory = history;
    if (startDate || endDate) {
        filteredHistory = history.filter(h => {
            const hDate = new Date(h.date);
            if (startDate && hDate < startDate) return false;
            if (endDate && hDate > endDate) return false;
            return true;
        });
    }
    
    if (filteredHistory.length === 0) {
        alert('选定时间范围内无数据');
        return;
    }
    
    let csv = '\uFEFF日期,价格,涨跌,涨跌幅\n';
    
    filteredHistory.forEach((h, index) => {
        const prev = filteredHistory[index + 1];
        const change = prev ? h.price - prev.price : 0;
        const changePercent = prev ? ((change / prev.price) * 100).toFixed(2) : '0.00';
        csv += `${h.date},${h.price},${change},${changePercent}%\n`;
    });
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    
    // 文件名包含时间范围
    const startStr = startInput && startInput.value ? startInput.value : 'all';
    const endStr = endInput && endInput.value ? endInput.value : 'all';
    const dateRange = startStr !== 'all' ? `_${startStr}_to_${endStr}` : '';
    
    link.download = `${material ? material.name : currentMaterial}_历史价格${dateRange}.csv`;
    link.click();
}

// 格式化价格
function formatPrice(price) {
    if (price >= 10000) {
        return (price / 10000).toFixed(2) + '万';
    }
    return price.toLocaleString();
}

// 更新时间戳
function updateTimestamp() {
    const el = document.getElementById('update-time');
    if (priceData && priceData.update_time) {
        el.textContent = priceData.update_time;
    }
}

// 显示错误
function showError(msg) {
    alert(msg);
}

// 启动
init();

// ========== GitHub Actions 手动刷新功能 ==========

// 从URL或localStorage获取仓库路径
function getRepoPath() {
    const hostname = window.location.hostname;
    if (hostname.endsWith('github.io')) {
        const pathParts = window.location.pathname.split('/').filter(p => p);
        if (pathParts.length > 0) {
            return hostname.replace('.github.io', '') + '/' + pathParts[0];
        }
    }
    return localStorage.getItem('github_repo') || '';
}

// 手动刷新数据
async function refreshData() {
    const repo = getRepoPath();
    const token = localStorage.getItem('github_token');
    
    if (!token || !repo) {
        if (confirm('首次使用需要配置GitHub信息才能手动触发数据更新。\n\n是否现在配置？')) {
            showConfig();
        }
        return;
    }
    
    if (!confirm('确定要手动触发数据更新吗？\n这会启动GitHub Actions工作流，约1-2分钟后完成。')) {
        return;
    }
    
    try {
        const response = await fetch(`https://api.github.com/repos/${repo}/actions/workflows/daily-update.yml/dispatches`, {
            method: 'POST',
            headers: {
                'Authorization': `token ${token}`,
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ref: 'main' })
        });
        
        if (response.ok) {
            alert('✅ 数据更新已触发！\n\n约1-2分钟后，请刷新页面查看最新数据。');
        } else if (response.status === 401) {
            alert('❌ Token无效，请重新配置');
            localStorage.removeItem('github_token');
        } else if (response.status === 404) {
            alert('❌ 工作流未找到，请检查仓库路径');
        } else {
            alert(`❌ 触发失败: ${response.status}\n请检查GitHub Actions是否已启用。`);
        }
    } catch (e) {
        alert('❌ 网络错误，请检查网络连接');
        console.error(e);
    }
}

// 显示配置对话框
function showConfig() {
    const currentRepo = getRepoPath();
    const currentToken = localStorage.getItem('github_token') ? '已配置（隐藏）' : '未配置';
    
    const repo = prompt(
        '配置GitHub仓库路径（格式：用户名/仓库名）：\n\n' +
        '例如：zhangsan/raw-material-prices',
        currentRepo
    );
    
    if (repo === null) return; // 用户取消
    
    if (repo && repo.includes('/')) {
        localStorage.setItem('github_repo', repo);
    }
    
    const token = prompt(
        '配置GitHub Personal Access Token：\n\n' +
        '1. 访问 https://github.com/settings/tokens\n' +
        '2. 点击 Generate new token (classic)\n' +
        '3. 勾选 repo 和 workflow 权限\n' +
        '4. 生成后复制token粘贴到这里\n\n' +
        `当前状态：${currentToken}`
    );
    
    if (token && token.startsWith('ghp_')) {
        localStorage.setItem('github_token', token);
        alert('✅ 配置已保存！现在可以点击"刷新数据"按钮了。');
    } else if (token) {
        alert('⚠️ Token格式不正确，应以 ghp_ 开头');
    }
}

// 打开GitHub Actions页面
function openGitHubActions() {
    const repo = getRepoPath();
    if (repo) {
        window.open(`https://github.com/${repo}/actions`, '_blank');
    } else {
        alert('请先配置GitHub仓库路径');
    }
}
