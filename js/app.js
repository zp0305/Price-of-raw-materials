// 全局数据存储
let priceData = null;
let chartInstance = null;
let currentMaterial = null;
let currentRange = 7;
let currentFilter = 'all';

// 材料分类
const materialCategories = {
    'CU': 'cu', 'ADC12': 'cu', 'AL6063': 'cu',
    'B35A300': 'sife', 'B50A310': 'sife', 'B50A350': 'sife', 'B50A470': 'sife', 'B50A600': 'sife',
    'REO': 'rare', 'REN': 'rare', 'TB': 'rare', 'CE': 'rare', 'DYFE': 'rare'
};

// 稀土材料编码集合（用于判断显示单位）
const rareEarthCodes = new Set(['REO', 'REN', 'TB', 'CE', 'DYFE']);

// 初始化
async function init() {
    await loadData();
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
        
        if (priceData.today.length > 0) {
            currentMaterial = priceData.today[0].code;
        }
        
        populateSelectors();
    } catch (error) {
        console.error('加载数据失败:', error);
        showError('数据加载失败，请刷新页面重试');
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
        document.getElementById('material-select').value = currentMaterial;
        updateChart();
        renderHistoryTable();
        highlightCard(currentMaterial);
    });
}

// 初始化日期输入框
function initDateInputs() {
    const today = new Date().toISOString().split('T')[0];
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    
    document.getElementById('export-start').value = thirtyDaysAgo;
    document.getElementById('export-end').value = today;
}

// 渲染价格卡片
function renderCards() {
    const container = document.getElementById('price-cards');

    const sorted = [...priceData.today].sort((a, b) => b.price - a.price);
    const cards = sorted.map(m => {
        const category = materialCategories[m.code] || 'all';
        const isRare = rareEarthCodes.has(m.code);
        const changeClass = m.change > 0 ? 'text-red-500' : m.change < 0 ? 'text-green-500' : 'text-gray-400';
        const bgClass = m.change > 0 ? 'border-l-red-400' : m.change < 0 ? 'border-l-green-400' : 'border-l-gray-300';
        const arrow = m.change > 0 ? '↑' : m.change < 0 ? '↓' : '—';
        const isActive = m.code === currentMaterial ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:shadow-md';
        const priceStr = isRare ? formatRarePrice(m.price) : m.price.toLocaleString();
        const unit = isRare ? '万元/吨' : '元/吨';
        const changeDisplay = isRare
            ? (m.change !== 0 ? Math.round(m.change / 10000).toLocaleString() : '0')
            : Math.abs(m.change).toLocaleString();
        
        return `
            <div class="price-card bg-white rounded-xl p-4 border-l-4 ${bgClass} shadow-sm cursor-pointer transition-all ${isActive}" 
                 data-category="${category}" data-code="${m.code}"
                 onclick="selectMaterial('${m.code}')">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-gray-600">${m.name}</span>
                    <span class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">${m.code}</span>
                </div>
                <div class="text-2xl font-bold text-gray-900 mb-1">
                    ${priceStr}
                </div>
                <div class="flex items-center justify-between">
                    <span class="text-sm ${changeClass} font-semibold">
                        ${arrow} ${changeDisplay}
                    </span>
                    <span class="text-xs text-gray-400">${unit}</span>
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
            card.classList.add('ring-2', 'ring-blue-500', 'bg-blue-50');
        } else {
            card.classList.remove('ring-2', 'ring-blue-500', 'bg-blue-50');
        }
    });
}

// 筛选材料
function filterMaterials(category) {
    currentFilter = category;

    document.querySelectorAll('.filter-btn').forEach(btn => {
        if (btn.dataset.filter === category) {
            btn.classList.add('bg-blue-500', 'text-white');
            btn.classList.remove('bg-white', 'text-gray-600', 'hover:bg-gray-100');
        } else {
            btn.classList.remove('bg-blue-500', 'text-white');
            btn.classList.add('bg-white', 'text-gray-600', 'hover:bg-gray-100');
        }
    });

    const visibleCards = [];
    document.querySelectorAll('.price-card').forEach(card => {
        const match = (category === 'all' || card.dataset.category === category);
        card.style.display = match ? 'block' : 'none';
        if (match) visibleCards.push(card);
    });

    if (visibleCards.length > 0) {
        selectMaterial(visibleCards[0].dataset.code);
    }
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
            interaction: { intersect: false, mode: 'index' },
            plugins: {
                legend: { display: true, position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatPrice(context.parsed.y, currentMaterial);
                        }
                    }
                }
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            if (currentMaterial && rareEarthCodes.has(currentMaterial)) {
                                return Math.round(value / 10000).toLocaleString();
                            }
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
    let filtered = currentRange > 0 ? history.slice(0, currentRange) : history;

    if (filtered.length > 60) {
        filtered = sampleData(filtered, 60);
    }

    const sorted = [...filtered].reverse();
    const material = priceData.today.find(m => m.code === currentMaterial);
    const labels = sorted.map(h => currentRange >= 365 ? h.date.slice(0, 7) : h.date.slice(5));

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
            pointRadius: sorted.length > 60 ? 0 : 3,
            pointHoverRadius: 5
        }]
    };
}

function sampleData(data, maxPoints) {
    if (data.length <= maxPoints) return data;
    const step = Math.ceil(data.length / maxPoints);
    const result = [];
    for (let i = 0; i < data.length; i += step) {
        const chunk = data.slice(i, Math.min(i + step, data.length));
        result.push({
            date: chunk[0].date,
            price: chunk[Math.floor(chunk.length / 2)].price,
        });
    }
    return result;
}

// 设置图表时间范围
function setChartRange(days) {
    currentRange = days;
    
    document.querySelectorAll('.range-btn').forEach(btn => {
        if (parseInt(btn.dataset.range) === days) {
            btn.classList.add('bg-blue-500', 'text-white');
            btn.classList.remove('text-gray-600', 'hover:bg-white');
        } else {
            btn.classList.remove('bg-blue-500', 'text-white');
            btn.classList.add('text-gray-600', 'hover:bg-white');
        }
    });
    
    updateChart();
}

// 渲染历史数据表
const pageSize = 50;
let currentPage = 0;

function renderHistoryTable(page = 0) {
    currentPage = page;
    const tbody = document.getElementById('history-table');
    const history = priceData.history[currentMaterial] || [];
    const isRare = rareEarthCodes.has(currentMaterial);

    document.getElementById('price-header').textContent =
        isRare ? '价格 (万元/吨)' : '价格 (元/吨)';

    const start = page * pageSize;
    const end = start + pageSize;
    const pageData = history.slice(start, end);

    const rows = pageData.map((h, index) => {
        const prev = history[index + 1 + start];
        const change = prev ? h.price - prev.price : 0;
        const changePercent = prev ? ((change / prev.price) * 100).toFixed(2) : '0.00';
        const changeClass = change > 0 ? 'text-red-500' : change < 0 ? 'text-green-500' : 'text-gray-400';
        const sign = change > 0 ? '+' : '';
        const priceStr = isRare ? formatRarePrice(h.price) : h.price.toLocaleString();
        const changeStr = isRare
            ? (change !== 0 ? Math.round(change / 10000).toLocaleString() : '0')
            : change.toLocaleString();

        return `
            <tr class="hover:bg-gray-50 transition-colors">
                <td class="px-4 py-3 text-gray-700">${h.date}</td>
                <td class="px-4 py-3 text-right font-mono font-semibold">${priceStr}</td>
                <td class="px-4 py-3 text-right ${changeClass}">${sign}${changeStr}</td>
                <td class="px-4 py-3 text-right ${changeClass}">${sign}${changePercent}%</td>
            </tr>
        `;
    }).join('');

    if (history.length > end) {
        tbody.innerHTML = rows + `
            <tr id="load-more-row">
                <td colspan="4" class="px-4 py-4 text-center">
                    <button onclick="loadMoreHistory()" class="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600">
                        加载更多 (${history.length - end} 条)
                    </button>
                </td>
            </tr>
        `;
    } else {
        tbody.innerHTML = rows || '<tr><td colspan="4" class="px-4 py-8 text-center text-gray-500">暂无历史数据</td></tr>';
    }
}

function loadMoreHistory() {
    renderHistoryTable(currentPage + 1);
}

function formatRarePrice(price) {
    return Math.round(price / 10000).toLocaleString();
}

// 导出CSV
function exportCSV() {
    const history = priceData.history[currentMaterial] || [];
    const material = priceData.today.find(m => m.code === currentMaterial);
    
    const startInput = document.getElementById('export-start');
    const endInput = document.getElementById('export-end');
    
    let startDate = startInput.value ? new Date(startInput.value) : null;
    let endDate = endInput.value ? new Date(endInput.value) : null;
    if (endDate) endDate.setHours(23, 59, 59, 999);
    
    let filtered = history.filter(h => {
        const hDate = new Date(h.date);
        if (startDate && hDate < startDate) return false;
        if (endDate && hDate > endDate) return false;
        return true;
    });
    
    if (!filtered.length) {
        alert('选定时间范围内无数据');
        return;
    }
    
    let csv = '\uFEFF日期,价格,涨跌,涨跌幅\n';
    filtered.forEach((h, i) => {
        const prev = filtered[i + 1];
        const change = prev ? h.price - prev.price : 0;
        const pct = prev ? ((change / prev.price) * 100).toFixed(2) : '0.00';
        csv += `${h.date},${h.price},${change},${pct}%\n`;
    });
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${material ? material.name : currentMaterial}_历史价格.csv`;
    link.click();
}

// 格式化价格（用于图表tooltip等通用场景）
function formatPrice(price, code) {
    if (code && rareEarthCodes.has(code)) {
        return Math.round(price / 10000).toLocaleString() + ' 万元/吨';
    }
    return Math.round(price).toLocaleString() + ' 元/吨';
}

// 更新时间戳
function updateTimestamp() {
    const el = document.getElementById('update-time');
    if (priceData && priceData.update_time) {
        el.textContent = priceData.update_time;
    }
}

function showError(msg) {
    alert(msg);
}

// 启动
init();

// ========== 手动刷新功能 ==========

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

async function refreshData() {
    const repo = getRepoPath();
    const token = localStorage.getItem('github_token');
    
    if (!token || !repo) {
        if (confirm('首次使用需要配置 GitHub Token 才能手动刷新数据。\n\n是否现在配置？')) {
            showConfig();
        }
        return;
    }
    
    if (!confirm('确定要手动触发数据更新吗？\n\n约1-2分钟后，请刷新页面查看最新数据。')) {
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
            alert('❌ Token 无效，请重新配置');
            localStorage.removeItem('github_token');
        } else {
            alert(`❌ 触发失败: ${response.status}`);
        }
    } catch (e) {
        alert('❌ 网络错误');
    }
}

function showConfig() {
    const currentRepo = getRepoPath();
    
    const repo = prompt('配置 GitHub 仓库路径（格式：用户名/仓库名）：', currentRepo);
    if (repo === null) return;
    if (repo && repo.includes('/')) {
        localStorage.setItem('github_repo', repo);
    }
    
    const token = prompt(
        '配置 GitHub Personal Access Token：\n\n' +
        '1. 访问 https://github.com/settings/tokens\n' +
        '2. 点击 Generate new token (classic)\n' +
        '3. 勾选 repo 和 workflow 权限\n' +
        '4. 生成后复制 token 粘贴到这里'
    );
    
    if (token && token.startsWith('ghp_')) {
        localStorage.setItem('github_token', token);
        alert('✅ 配置已保存！');
    } else if (token) {
        alert('⚠️ Token 格式不正确，应以 ghp_ 开头');
    }
}
