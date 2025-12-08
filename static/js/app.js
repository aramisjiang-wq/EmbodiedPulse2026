// 全局状态
let currentTab = null;
let papersData = {};
let statsData = {};
let lastFetchUpdate = null; // 记录上次抓取完成时间，避免重复刷新
let statusPollingInterval = null; // 轮询定时器

// 研究方向配置（统一管理）
const RESEARCH_CATEGORIES = {
    // 研究方向顺序（按流程）
    order: ['Perception', 'VLM', 'Planning', 'RL/IL', 'Manipulation', 'Locomotion', 'Dexterous', 'VLA', 'Humanoid'],
    // 数据库类别到显示类别的映射（所有研究方向）
    dbToDisplay: {
        'Perception': 'Perception',
        'VLM': 'VLM',
        'Planning': 'Planning',
        'RL/IL': 'RL/IL',
        'Manipulation': 'Manipulation',
        'Locomotion': 'Locomotion',
        'Dexterous': 'Dexterous',
        'VLA': 'VLA',
        'Humanoid': 'Humanoid'
    },
    // 图标映射
    icons: {
        'Perception': 'fas fa-camera',
        'VLM': 'fas fa-eye',
        'Planning': 'fas fa-route',
        'RL/IL': 'fas fa-graduation-cap',
        'Manipulation': 'fas fa-hand-paper',
        'Locomotion': 'fas fa-running',
        'Dexterous': 'fas fa-fingerprint',
        'VLA': 'fas fa-brain',
        'Humanoid': 'fas fa-walking'
    }
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadPapers();
    loadCategories();
    setupEventListeners();
    startStatusPolling();
});

// 设置事件监听器
function setupEventListeners() {
    document.getElementById('refreshBtn').addEventListener('click', () => {
        loadStats();
        loadPapers();
        hideSearchResults();
    });

    document.getElementById('fetchBtn').addEventListener('click', () => {
        openFetchModal();
    });

    // 搜索功能
    document.getElementById('searchBtn').addEventListener('click', performSearch);
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    // 清除搜索功能
    document.getElementById('clearSearchBtn').addEventListener('click', clearSearch);
}

// 加载统计信息
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const result = await response.json();
        
        if (result.success) {
            statsData = result.stats;
            // 确保total是数字类型
            let total = typeof result.total === 'number' ? result.total : parseInt(result.total) || 0;
            
            // 如果total为0，尝试从stats计算总和
            if (total === 0 && result.stats) {
                total = Object.values(result.stats).reduce((sum, count) => sum + (typeof count === 'number' ? count : parseInt(count) || 0), 0);
            }
            
            renderStats(result.stats, total);
            console.log('统计信息已更新，总论文数:', total, '各类别:', result.stats);
        } else {
            console.error('加载统计信息失败:', result.error);
        }
    } catch (error) {
        console.error('加载统计信息失败:', error);
    }
}

// 更新最后更新时间
function updateLastUpdateTime(timestamp) {
    const timeElement = document.getElementById('lastUpdateTime');
    if (timeElement && timestamp) {
        const date = new Date(timestamp);
        const formatted = date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        timeElement.textContent = formatted;
    }
}

// 渲染统计信息 - 总论文数+柱状图
let barChart = null;

function renderStats(stats, total) {
    // 更新总论文数
    const totalElement = document.getElementById('totalPapersValue');
    if (totalElement) {
        totalElement.textContent = total.toLocaleString();
    }
    
    // 准备柱状图数据
    const labels = [];
    const data = [];
    const colors = [
        '#667eea', '#764ba2', '#3b82f6', '#8b5cf6', '#ec4899',
        '#f59e0b', '#10b981', '#06b6d4', '#f97316'
    ];
    
    RESEARCH_CATEGORIES.order.forEach((displayCategory, index) => {
        const dbCategory = Object.keys(RESEARCH_CATEGORIES.dbToDisplay).find(
            db => RESEARCH_CATEGORIES.dbToDisplay[db] === displayCategory
        );
        const count = dbCategory && stats[dbCategory] !== undefined ? stats[dbCategory] : 0;
        labels.push(displayCategory);
        data.push(count);
    });
    
    // 渲染柱状图
    renderBarChart(labels, data, colors);
}

function renderBarChart(labels, data, colors) {
    const ctx = document.getElementById('barChart');
    if (!ctx) return;
    
    if (barChart) {
        barChart.destroy();
    }
    
    barChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '论文数量',
                data: data,
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('0.8', '1')),
                borderWidth: 1,
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 0  // 禁用动画以提高性能
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 13
                    },
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${context.label}: ${value.toLocaleString()} 篇 (${percentage}%)`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString();
                        },
                        font: {
                            size: 11
                        },
                        color: '#64748b'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                        drawBorder: false
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: 10
                        },
                        color: '#64748b',
                        maxRotation: 45,
                        minRotation: 0
                    },
                    grid: {
                        display: false,
                        drawBorder: false
                    }
                }
            },
            // 确保背景为纯白色
            backgroundColor: '#ffffff',
            // 图表画布背景
            onResize: function(chart, size) {
                // 确保图表背景为白色
                chart.canvas.style.backgroundColor = '#ffffff';
            }
        }
    });
    
    // 监听窗口大小变化，重新调整图表
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            if (barChart) {
                barChart.resize();
            }
        }, 250);
    });
}

// 创建统计卡片
function createStatCard(label, value, icon, categoryClass = '') {
    const card = document.createElement('div');
    const count = typeof value === 'number' ? value : parseInt(value) || 0;
    
    // 如果数量为0，添加特殊样式类
    if (count === 0) {
        card.className = `stat-card ${categoryClass} zero-count`;
    } else {
        card.className = `stat-card ${categoryClass}`;
    }
    
    // 格式化数字（添加千位分隔符）
    const formattedValue = count.toLocaleString('zh-CN');
    
    card.innerHTML = `
        <div class="stat-value">${formattedValue}</div>
        <div class="stat-label">
            <i class="${icon}"></i> ${label}
        </div>
    `;
    return card;
}

// 加载论文数据
async function loadPapers() {
    const container = document.getElementById('papersContainer');
    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin fa-3x"></i><p>加载论文数据中...</p></div>';

    try {
        const response = await fetch('/api/papers');
        const result = await response.json();
        
        if (result.success) {
            papersData = result.data;
            renderPapers(result.data);
            
            // 更新最后更新时间
            if (result.last_update) {
                updateLastUpdateTime(result.last_update);
            }
        } else {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>加载失败: ' + result.error + '</p></div>';
        }
    } catch (error) {
        console.error('加载论文数据失败:', error);
        container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>加载失败，请刷新重试</p></div>';
    }
}

// 渲染论文列表
function renderPapers(data) {
    const tabs = document.getElementById('tabs');
    const container = document.getElementById('papersContainer');
    
    // 清空
    tabs.innerHTML = '';
    container.innerHTML = '';

    const keywords = Object.keys(data);
    
    if (keywords.length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-inbox"></i><p>暂无论文数据</p><p style="margin-top: 10px; font-size: 0.9rem;">点击"抓取新论文"按钮开始抓取</p></div>';
        return;
    }

    // 按研究方向顺序创建标签页（显示所有研究方向，即使数据为0）
    let activeIndex = 0;
    RESEARCH_CATEGORIES.order.forEach(displayCategory => {
        // 找到对应的数据库类别
        const dbCategory = Object.keys(RESEARCH_CATEGORIES.dbToDisplay).find(
            db => RESEARCH_CATEGORIES.dbToDisplay[db] === displayCategory
        );
        
        // 获取该类别的论文数量（如果不存在则为0）
        const papers = dbCategory && data[dbCategory] ? data[dbCategory] : [];
        const count = papers.length;
        
        // 显示所有研究方向，即使数据为0
        const tab = document.createElement('button');
        tab.className = 'tab' + (activeIndex === 0 ? ' active' : '');
        if (count === 0) {
            tab.classList.add('zero-count');
        }
        tab.textContent = `${displayCategory} (${count})`;
        tab.dataset.keyword = dbCategory || displayCategory; // 使用数据库类别名或显示名称
        tab.dataset.displayName = displayCategory; // 保存显示名称
        tab.addEventListener('click', () => switchTab(dbCategory || displayCategory));
        tabs.appendChild(tab);
        activeIndex++;
    });

    // 创建论文列表（按研究方向顺序，显示所有研究方向）
    let listIndex = 0;
    RESEARCH_CATEGORIES.order.forEach(displayCategory => {
        const dbCategory = Object.keys(RESEARCH_CATEGORIES.dbToDisplay).find(
            db => RESEARCH_CATEGORIES.dbToDisplay[db] === displayCategory
        );
        
        // 获取该类别的论文（如果不存在则为空数组）
        const papers = dbCategory && data[dbCategory] ? data[dbCategory] : [];
        
        // 创建论文列表容器（即使为空也创建）
        const paperList = document.createElement('div');
        paperList.className = 'paper-list' + (listIndex === 0 ? ' active' : '');
        paperList.id = `list-${dbCategory || displayCategory}`;

        if (papers.length > 0) {
            papers.forEach(paper => {
                const paperItem = createPaperItem(paper);
                paperList.appendChild(paperItem);
            });
        } else {
            // 如果没有论文，显示空状态
            paperList.innerHTML = '<div class="empty-state"><i class="fas fa-inbox"></i><p>该类别暂无论文</p></div>';
        }

        container.appendChild(paperList);
        listIndex++;
    });

    // 设置默认标签页（选择第一个有数据的，如果没有则选择第一个）
    let firstDbCategory = null;
    for (const displayCategory of RESEARCH_CATEGORIES.order) {
        const dbCat = Object.keys(RESEARCH_CATEGORIES.dbToDisplay).find(
            db => RESEARCH_CATEGORIES.dbToDisplay[db] === displayCategory
        );
        if (dbCat && data[dbCat] && data[dbCat].length > 0) {
            firstDbCategory = dbCat;
            break;
        }
    }
    // 如果没有有数据的，选择第一个研究方向
    if (!firstDbCategory) {
        const firstDisplay = RESEARCH_CATEGORIES.order[0];
        firstDbCategory = Object.keys(RESEARCH_CATEGORIES.dbToDisplay).find(
            db => RESEARCH_CATEGORIES.dbToDisplay[db] === firstDisplay
        ) || firstDisplay;
    }
    if (firstDbCategory) {
        currentTab = firstDbCategory;
    }
}

// 创建论文项
function createPaperItem(paper) {
    const item = document.createElement('div');
    item.className = 'paper-item';
    
    const codeLink = paper.code_url 
        ? `<a href="${paper.code_url}" target="_blank" class="paper-link code"><i class="fas fa-code"></i> 代码</a>`
        : '<span class="paper-link disabled"><i class="fas fa-code"></i> 无代码</span>';
    
    item.innerHTML = `
        <div class="paper-header">
            <div class="paper-title">
                <a href="${paper.pdf_url}" target="_blank">${paper.title}</a>
            </div>
            <div class="paper-date">${paper.date}</div>
        </div>
        <div class="paper-meta">
            <div class="paper-authors">
                <i class="fas fa-users"></i> ${paper.authors}
            </div>
            <div class="paper-links">
                <a href="${paper.pdf_url}" target="_blank" class="paper-link pdf">
                    <i class="fas fa-file-pdf"></i> PDF
                </a>
                ${codeLink}
            </div>
        </div>
    `;
    
    return item;
}

// 切换标签页
function switchTab(keyword) {
    // 更新标签页状态
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.keyword === keyword) {
            tab.classList.add('active');
        }
    });

    // 更新论文列表显示
    document.querySelectorAll('.paper-list').forEach(list => {
        list.classList.remove('active');
        if (list.id === `list-${keyword}`) {
            list.classList.add('active');
        }
    });

    currentTab = keyword;
    
    // 更新标签页文本（保持数量显示和显示名称）
    if (papersData[keyword]) {
        const activeTab = document.querySelector(`.tab[data-keyword="${keyword}"]`);
        if (activeTab) {
            const count = papersData[keyword].length;
            const displayName = activeTab.dataset.displayName || keyword;
            activeTab.textContent = `${displayName} (${count})`;
        }
    }
}

// 打开抓取模态框
function openFetchModal() {
    document.getElementById('fetchModal').classList.remove('hidden');
}

// 关闭抓取模态框
function closeFetchModal() {
    document.getElementById('fetchModal').classList.add('hidden');
}

// 确认抓取
async function confirmFetch() {
    const maxResults = parseInt(document.getElementById('maxResults').value) || 20;
    const configPath = document.getElementById('configPath').value || 'config.yaml';

    closeFetchModal();

    // 显示抓取状态
    const statusDiv = document.getElementById('fetchStatus');
    statusDiv.classList.remove('hidden');
    
    // 重置lastFetchUpdate，确保抓取完成后能刷新
    lastFetchUpdate = null;

    try {
        console.log('开始抓取论文，参数:', { maxResults, configPath });
        const response = await fetch('/api/fetch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                max_results: maxResults,
                config_path: configPath
            })
        });

        const result = await response.json();
        console.log('抓取API响应:', result);
        
        if (result.success) {
            updateFetchStatus('抓取任务已启动，请稍候...');
            console.log('抓取任务已启动，开始轮询状态...');
            // 确保轮询已启动（立即启动，不等待）
            if (statusPollingInterval) {
                clearInterval(statusPollingInterval);
            }
            startStatusPolling();
            // 立即检查一次状态
            setTimeout(async () => {
                try {
                    const response = await fetch('/api/fetch-status');
                    const status = await response.json();
                    console.log('立即检查状态:', status);
                    const statusDiv = document.getElementById('fetchStatus');
                    const messageSpan = document.getElementById('statusMessage');
                    const progressFill = document.getElementById('progressFill');
                    if (status.running) {
                        statusDiv.classList.remove('hidden');
                        messageSpan.textContent = status.message || '正在抓取论文...';
                        if (status.total > 0) {
                            const progress = Math.min((status.progress / status.total) * 100, 100);
                            progressFill.style.width = progress + '%';
                        }
                    }
                } catch (error) {
                    console.error('立即检查状态失败:', error);
                }
            }, 500);
        } else {
            updateFetchStatus('启动失败: ' + result.message);
            setTimeout(() => {
                statusDiv.classList.add('hidden');
            }, 5000);
        }
    } catch (error) {
        console.error('启动抓取失败:', error);
        updateFetchStatus('启动失败: ' + error.message);
        setTimeout(() => {
            statusDiv.classList.add('hidden');
        }, 5000);
    }
}

// 更新抓取状态
function updateFetchStatus(message) {
    const messageSpan = document.getElementById('statusMessage');
    messageSpan.textContent = message;
}

// 轮询抓取状态
function startStatusPolling() {
    // 清除之前的定时器
    if (statusPollingInterval) {
        clearInterval(statusPollingInterval);
    }
    
    statusPollingInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/fetch-status');
            const status = await response.json();
            
            const statusDiv = document.getElementById('fetchStatus');
            const messageSpan = document.getElementById('statusMessage');
            const progressFill = document.getElementById('progressFill');
            
            // 调试日志
            if (status.running || status.progress > 0) {
                console.log('抓取状态:', status);
            }
            
            if (status.running) {
                statusDiv.classList.remove('hidden');
                messageSpan.textContent = status.message || '正在抓取论文...';
                
                if (status.total > 0) {
                    const progress = Math.min((status.progress / status.total) * 100, 100);
                    progressFill.style.width = progress + '%';
                    console.log(`抓取进度: ${status.progress}/${status.total} (${progress.toFixed(1)}%) - ${status.message}`);
                } else {
                    progressFill.style.width = '0%';
                    console.log('等待抓取任务启动...');
                }
            } else {
                // 只在抓取刚完成时刷新一次（避免重复刷新）
                if (status.last_update && status.last_update !== lastFetchUpdate) {
                    lastFetchUpdate = status.last_update;
                    // 抓取完成，刷新数据
                    setTimeout(() => {
                        statusDiv.classList.add('hidden');
                        // 强制刷新统计和论文数据
                        loadStats();
                        loadPapers();
                        loadCategories(); // 重新加载类别筛选器
                        if (status.last_update) {
                            updateLastUpdateTime(status.last_update);
                        }
                    }, 2000);
                } else if (!status.running) {
                    // 没有任务运行时，隐藏状态栏
                    statusDiv.classList.add('hidden');
                }
            }
        } catch (error) {
            console.error('获取抓取状态失败:', error);
        }
    }, 5000); // 改为每5秒轮询一次，减少请求频率
}

// 点击模态框外部关闭
document.getElementById('fetchModal')?.addEventListener('click', (e) => {
    if (e.target.id === 'fetchModal') {
        closeFetchModal();
    }
});

// 搜索功能
async function performSearch() {
    const query = document.getElementById('searchInput').value.trim();
    const category = document.getElementById('categoryFilter').value;
    
    if (!query && !category) {
        alert('请输入搜索关键词或选择类别');
        return;
    }

    const resultsDiv = document.getElementById('searchResults');
    const clearBtn = document.getElementById('clearSearchBtn');
    const papersContainer = document.getElementById('papersContainer');
    const tabs = document.getElementById('tabs');
    
    // 隐藏原有的论文列表和标签页
    papersContainer.style.display = 'none';
    tabs.style.display = 'none';
    
    // 显示搜索结果区域和清除按钮
    resultsDiv.classList.remove('hidden');
    clearBtn.classList.remove('hidden');
    resultsDiv.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin fa-2x"></i><p>搜索中...</p></div>';

    try {
        const params = new URLSearchParams();
        if (query) params.append('q', query);
        if (category) params.append('category', category);

        const response = await fetch(`/api/search?${params}`);
        const result = await response.json();

        if (result.success) {
            displaySearchResults(result.data, result.count, query, category);
        } else {
            resultsDiv.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>搜索失败: ${result.error}</p></div>`;
        }
    } catch (error) {
        console.error('搜索失败:', error);
        resultsDiv.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>搜索失败，请重试</p></div>';
    }
}

function displaySearchResults(papers, count, query, category) {
    const resultsDiv = document.getElementById('searchResults');
    
    if (papers.length === 0) {
        resultsDiv.innerHTML = '<div class="empty-state"><i class="fas fa-search"></i><p>未找到相关论文</p></div>';
        return;
    }

    // 构建搜索条件说明
    let searchInfo = '';
    if (query && category) {
        const displayCategory = RESEARCH_CATEGORIES.dbToDisplay[category] || category;
        searchInfo = `关键词"${query}"，类别"${displayCategory}"`;
    } else if (query) {
        searchInfo = `关键词"${query}"`;
    } else if (category) {
        const displayCategory = RESEARCH_CATEGORIES.dbToDisplay[category] || category;
        searchInfo = `类别"${displayCategory}"`;
    }

    let html = `
        <div class="search-results-header">
            <div>
                <h3><i class="fas fa-search"></i> 搜索结果</h3>
                <div class="search-info">搜索条件: ${searchInfo}</div>
            </div>
            <div class="search-results-count">找到 ${count} 篇论文</div>
        </div>
        <div class="paper-list active">
    `;

    papers.forEach(paper => {
        const codeLink = paper.code_url 
            ? `<a href="${paper.code_url}" target="_blank" class="paper-link code"><i class="fas fa-code"></i> 代码</a>`
            : '<span class="paper-link disabled"><i class="fas fa-code"></i> 无代码</span>';
        
        html += `
            <div class="paper-item">
                <div class="paper-header">
                    <div class="paper-title">
                        <a href="${paper.pdf_url}" target="_blank">${paper.title}</a>
                    </div>
                    <div class="paper-date">${paper.date}</div>
                </div>
                <div class="paper-meta">
                    <div class="paper-authors">
                        <i class="fas fa-users"></i> ${paper.authors}
                    </div>
                    <div class="paper-links">
                        <a href="${paper.pdf_url}" target="_blank" class="paper-link pdf">
                            <i class="fas fa-file-pdf"></i> PDF
                        </a>
                        ${codeLink}
                    </div>
                </div>
            </div>
        `;
    });

    html += '</div>';
    resultsDiv.innerHTML = html;
}

// 清除搜索，返回所有论文视图
function clearSearch() {
    const searchInput = document.getElementById('searchInput');
    const categoryFilter = document.getElementById('categoryFilter');
    const resultsDiv = document.getElementById('searchResults');
    const clearBtn = document.getElementById('clearSearchBtn');
    const papersContainer = document.getElementById('papersContainer');
    const tabs = document.getElementById('tabs');
    
    // 清空搜索条件
    searchInput.value = '';
    categoryFilter.value = '';
    
    // 隐藏搜索结果和清除按钮
    resultsDiv.classList.add('hidden');
    clearBtn.classList.add('hidden');
    
    // 显示原有的论文列表和标签页
    papersContainer.style.display = 'block';
    tabs.style.display = 'flex';
    
    // 平滑滚动到论文列表区域
    document.querySelector('.papers-list-section').scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
    });
}

function hideSearchResults() {
    clearSearch();
}

// 加载类别到筛选器（与研究方向保持一致，显示所有研究方向）
async function loadCategories() {
    try {
        const response = await fetch('/api/stats');
        const result = await response.json();
        
        if (result.success) {
            const categoryFilter = document.getElementById('categoryFilter');
            // 清空现有选项（保留"所有类别"）
            categoryFilter.innerHTML = '<option value="">所有类别</option>';
            
            // 按研究方向顺序添加，显示所有研究方向
            RESEARCH_CATEGORIES.order.forEach(displayCategory => {
                // 找到对应的数据库类别
                const dbCategory = Object.keys(RESEARCH_CATEGORIES.dbToDisplay).find(
                    db => RESEARCH_CATEGORIES.dbToDisplay[db] === displayCategory
                );
                
                // 获取该类别的论文数量（如果不存在则为0）
                const count = dbCategory && result.stats[dbCategory] !== undefined ? result.stats[dbCategory] : 0;
                
                // 显示所有研究方向，即使数据为0
                const option = document.createElement('option');
                option.value = dbCategory || displayCategory; // 使用数据库中的类别名作为value
                option.textContent = `${displayCategory} (${count})`; // 显示研究方向名称和数量
                option.dataset.displayName = displayCategory; // 保存显示名称
                if (count === 0) {
                    option.disabled = true; // 数据为0时禁用
                    option.style.color = '#9ca3af'; // 灰色显示
                }
                categoryFilter.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载类别失败:', error);
    }
}

