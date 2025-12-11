// 全局状态
let currentTab = null;
let papersData = {};
let statsData = {};
let lastFetchUpdate = null; // 记录上次抓取完成时间，避免重复刷新
let statusPollingInterval = null; // 轮询定时器
let refreshStatusInterval = null; // 刷新状态轮询定时器

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
    console.log('页面加载完成，开始初始化...');
    try {
        loadStats();
        // 初始化时，如果没有上次查看时间，设置为当前时间（避免显示所有论文为新论文）
        if (!localStorage.getItem('papersLastViewed')) {
            localStorage.setItem('papersLastViewed', new Date().toISOString());
        }
        loadPapers(true); // 初始化时检查新论文
        loadCategories();
        loadJobs();
        loadDatasets();
        loadNews();
        initFortuneWidget();
        setupEventListeners();
        setupFilterSortListeners();
        startStatusPolling();
        console.log('初始化完成');
    } catch (error) {
        console.error('初始化失败:', error);
    }
    
    // 页面卸载时清理所有定时器
    window.addEventListener('beforeunload', () => {
        if (statusPollingInterval) {
            clearInterval(statusPollingInterval);
            statusPollingInterval = null;
        }
        if (refreshStatusInterval) {
            clearInterval(refreshStatusInterval);
            refreshStatusInterval = null;
        }
    });
});

// 设置事件监听器
function setupEventListeners() {
    // 刷新所有数据按钮（一键刷新论文、招聘、新闻）
    const refreshAllBtn = document.getElementById('refreshAllBtn');
    if (refreshAllBtn) {
        refreshAllBtn.addEventListener('click', refreshAllData);
    }

    document.getElementById('fetchBtn').addEventListener('click', () => {
        openFetchModal();
    });
    
    // 注意：红点现在在"全量"标签旁边，点击事件在创建标签时绑定
    // 如果页面加载时红点已存在（从HTML），也需要绑定事件
    const existingBadge = document.getElementById('newPapersBadge');
    if (existingBadge && !existingBadge.hasAttribute('data-event-bound')) {
        existingBadge.addEventListener('click', (e) => {
            e.stopPropagation();
            clearNewPapersBadge();
        });
        existingBadge.setAttribute('data-event-bound', 'true');
    }

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
    console.log('开始加载统计信息...');
    try {
        const response = await fetch('/api/stats');
        console.log('统计API响应状态:', response.status, response.statusText);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const result = await response.json();
        console.log('统计API返回数据:', result);
        
        if (result.success) {
            statsData = result.stats;
            // 确保total是数字类型
            let total = typeof result.total === 'number' ? result.total : parseInt(result.total) || 0;
            
            // 如果total为0，尝试从stats计算总和
            if (total === 0 && result.stats) {
                total = Object.values(result.stats).reduce((sum, count) => sum + (typeof count === 'number' ? count : parseInt(count) || 0), 0);
            }
            
            console.log('准备渲染统计信息，总论文数:', total, '各类别:', result.stats);
            renderStats(result.stats, total);
            console.log('统计信息渲染完成');
        } else {
            console.error('加载统计信息失败:', result.error);
            // 显示错误提示
            const totalElement = document.getElementById('totalPapersValue');
            if (totalElement) {
                totalElement.textContent = '加载失败';
            }
        }
    } catch (error) {
        console.error('加载统计信息失败:', error);
        console.error('错误堆栈:', error.stack);
        // 显示错误提示
        const totalElement = document.getElementById('totalPapersValue');
        if (totalElement) {
            totalElement.textContent = '加载失败: ' + error.message;
        }
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

// 渲染统计信息 - 总论文数+环形图
let donutChart = null;

function renderStats(stats, total) {
    console.log('renderStats 被调用，stats:', stats, 'total:', total);
    // 更新总论文数
    const totalElement = document.getElementById('totalPapersValue');
    if (totalElement) {
        totalElement.textContent = total.toLocaleString();
        console.log('总论文数已更新:', total.toLocaleString());
    } else {
        console.error('找不到totalPapersValue元素');
    }
    
    // 准备环形图数据
    const labels = [];
    const data = [];
    const colors = [
        '#667eea', '#764ba2', '#3b82f6', '#8b5cf6', '#ec4899',
        '#f59e0b', '#10b981', '#06b6d4', '#f97316'
    ];
    
    // 保存类别映射，用于点击跳转
    const categoryMap = {};
    
    RESEARCH_CATEGORIES.order.forEach((displayCategory, index) => {
        const dbCategory = Object.keys(RESEARCH_CATEGORIES.dbToDisplay).find(
            db => RESEARCH_CATEGORIES.dbToDisplay[db] === displayCategory
        );
        const count = dbCategory && stats[dbCategory] !== undefined ? stats[dbCategory] : 0;
        labels.push(displayCategory);
        data.push(count);
        categoryMap[displayCategory] = dbCategory || displayCategory;
    });
    
    console.log('准备渲染环形图，labels:', labels, 'data:', data);
    // 渲染环形图
    renderDonutChart(labels, data, colors, total, categoryMap);
}

function renderDonutChart(labels, data, colors, total, categoryMap) {
    const ctx = document.getElementById('barChart');
    if (!ctx) {
        console.error('找不到barChart元素');
        return;
    }
    
    // 检查Chart.js是否已加载
    if (typeof Chart === 'undefined') {
        console.error('Chart.js未加载');
        return;
    }
    
    if (donutChart) {
        donutChart.destroy();
    }
    
    donutChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 3,
                borderColor: '#ffffff',
                hoverBorderWidth: 4,
                hoverBorderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',  // 环形宽度（稍微调小，让图表更饱满）
            animation: {
                animateRotate: true,
                duration: 1000,
                easing: 'easeOutQuart'
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    align: 'center',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: {
                            size: 12,
                            family: "'Noto Serif SC', 'Source Han Serif SC', serif"
                        },
                        color: '#1e293b',
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map((label, i) => {
                                    const value = data.datasets[0].data[i];
                                    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                    return {
                                        text: `${label} (${percentage}%)`,
                                        fillStyle: data.datasets[0].backgroundColor[i],
                                        hidden: false,
                                        index: i
                                    };
                                });
                            }
                            return [];
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.85)',
                    padding: 14,
                    titleFont: {
                        size: 14,
                        weight: 'bold',
                        family: "'Noto Serif SC', 'Source Han Serif SC', serif"
                    },
                    bodyFont: {
                        size: 13,
                        family: "'Noto Serif SC', 'Source Han Serif SC', serif"
                    },
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value.toLocaleString()} 篇 (${percentage}%)`;
                        }
                    },
                    displayColors: true,
                    boxPadding: 6
                }
            },
            // 点击交互：跳转到对应类别
            onClick: function(event, elements) {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const displayCategory = labels[index];
                    const dbCategory = categoryMap[displayCategory];
                    
                    // 滚动到论文列表区域
                    const papersSection = document.querySelector('.papers-list-section');
                    if (papersSection) {
                        papersSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                    
                    // 延迟切换标签，确保滚动完成
                    setTimeout(() => {
                        switchTab(dbCategory);
                    }, 500);
                }
            },
            // 确保背景为纯白色
            onResize: function(chart, size) {
                chart.canvas.style.backgroundColor = '#ffffff';
            }
        }
    });
    
    // 监听窗口大小变化，重新调整图表
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            if (donutChart) {
                donutChart.resize();
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
async function loadPapers(showNewBadge = true) {
    console.log('开始加载论文数据...');
    const container = document.getElementById('papersContainer');
    if (!container) {
        console.error('找不到papersContainer元素');
        return;
    }
    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin fa-3x"></i><p>加载论文数据中...</p></div>';

    try {
        // 获取上次查看时间
        const lastViewed = localStorage.getItem('papersLastViewed');
        let url = '/api/papers';
        if (lastViewed && showNewBadge) {
            url += `?last_viewed=${encodeURIComponent(lastViewed)}`;
        }
        
        console.log('请求论文API:', url);
        const response = await fetch(url);
        console.log('论文API响应状态:', response.status, response.statusText);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const result = await response.json();
        console.log('论文API返回数据，success:', result.success, 'data keys:', result.data ? Object.keys(result.data) : 'no data');
        
        if (result.success) {
            if (!result.data || typeof result.data !== 'object') {
                throw new Error('返回的数据格式不正确: ' + typeof result.data);
            }
            papersData = result.data;
            console.log('准备渲染论文，数据类别数:', Object.keys(result.data).length);
            renderPapers(result.data);
            
            // 更新最后更新时间
            if (result.last_update) {
                updateLastUpdateTime(result.last_update);
            }
            
            // 更新新论文红点提示
            if (showNewBadge && result.new_papers_count !== undefined) {
                updateNewPapersBadge(result.new_papers_count);
            }
            console.log('论文数据加载完成');
        } else {
            console.error('论文API返回失败:', result.error);
            container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>加载失败: ' + (result.error || '未知错误') + '</p></div>';
        }
    } catch (error) {
        console.error('加载论文数据失败:', error);
        console.error('错误堆栈:', error.stack);
        container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>加载失败: ' + error.message + '</p><p style="margin-top: 10px; font-size: 0.9rem;">请检查网络连接或刷新页面重试</p></div>';
    }
}

// 更新新论文红点提示
function updateNewPapersBadge(count) {
    const badge = document.getElementById('newPapersBadge');
    const countElement = document.getElementById('newPapersCount');
    
    if (!badge || !countElement) {
        console.warn('红点提示元素未找到');
        return;
    }
    
    console.log('更新红点提示，新论文数量:', count);
    
    if (count > 0) {
        countElement.textContent = count > 99 ? '99+' : count.toString();
        badge.classList.remove('hidden');
        console.log('红点提示已显示，数量:', countElement.textContent);
    } else {
        badge.classList.add('hidden');
        console.log('红点提示已隐藏（无新论文）');
    }
}

// 清除新论文提示（点击红点时调用）
function clearNewPapersBadge() {
    const badge = document.getElementById('newPapersBadge');
    if (badge) {
        badge.classList.add('hidden');
        console.log('红点提示已清除');
    }
    // 更新上次查看时间为当前时间
    const now = new Date().toISOString();
    localStorage.setItem('papersLastViewed', now);
    console.log('已更新上次查看时间:', now);
}

// 渲染论文列表
// 筛选和排序的全局状态
let currentFilter = {
    venue: '' // 只保留发表场所筛选
};
let currentSort = 'date';

// 设置筛选和排序事件监听
function setupFilterSortListeners() {
    const venueFilter = document.getElementById('venueFilter');
    const sortBy = document.getElementById('sortBy');
    
    if (venueFilter) {
        venueFilter.addEventListener('change', (e) => {
            currentFilter.venue = e.target.value;
            applyFiltersAndSort();
        });
    }
    
    if (sortBy) {
        sortBy.addEventListener('change', (e) => {
            currentSort = e.target.value;
            applyFiltersAndSort();
        });
    }
}

// 应用筛选和排序
function applyFiltersAndSort() {
    if (!papersData || Object.keys(papersData).length === 0) {
        return;
    }
    
    // 重新渲染论文列表（应用筛选和排序）
    renderPapers(papersData);
}

// 填充筛选选项
function populateFilters(data) {
    const venues = new Set();
    
    // 收集所有发表场所
    Object.values(data).forEach(categoryPapers => {
        if (Array.isArray(categoryPapers)) {
            categoryPapers.forEach(paper => {
                if (paper.venue && paper.venue.trim()) {
                    venues.add(paper.venue.trim());
                }
            });
        }
    });
    
    // 填充发表场所筛选
    const venueFilter = document.getElementById('venueFilter');
    if (venueFilter) {
        const currentValue = venueFilter.value;
        venueFilter.innerHTML = '<option value="">所有发表场所</option>';
        Array.from(venues).sort().forEach(venue => {
            const option = document.createElement('option');
            option.value = venue;
            option.textContent = venue;
            venueFilter.appendChild(option);
        });
        if (currentValue) {
            venueFilter.value = currentValue;
        }
    }
}

// 筛选论文
function filterPapers(papers) {
    if (!papers || !Array.isArray(papers)) return [];
    
    return papers.filter(paper => {
        // 发表场所筛选
        if (currentFilter.venue) {
            if (!paper.venue || !paper.venue.includes(currentFilter.venue)) {
                return false;
            }
        }
        
        return true;
    });
}

// 排序论文
function sortPapers(papers) {
    if (!papers || !Array.isArray(papers)) return [];
    
    const sorted = [...papers];
    
    switch (currentSort) {
        case 'citations':
            sorted.sort((a, b) => {
                const aCitations = a.citation_count || 0;
                const bCitations = b.citation_count || 0;
                return bCitations - aCitations; // 降序
            });
            break;
        case 'title':
            sorted.sort((a, b) => {
                const aTitle = (a.title || '').toLowerCase();
                const bTitle = (b.title || '').toLowerCase();
                return aTitle.localeCompare(bTitle, 'zh-CN');
            });
            break;
        case 'date':
        default:
            sorted.sort((a, b) => {
                const aDate = a.date || '';
                const bDate = b.date || '';
                return bDate.localeCompare(aDate); // 降序（最新在前）
            });
            break;
    }
    
    return sorted;
}

function renderPapers(data) {
    console.log('renderPapers 被调用，数据:', data);
    const tabs = document.getElementById('tabs');
    const container = document.getElementById('papersContainer');
    
    if (!tabs) {
        console.error('找不到tabs元素');
        return;
    }
    if (!container) {
        console.error('找不到papersContainer元素');
        return;
    }
    
    // 填充筛选选项
    populateFilters(data);
    
    // 清空
    tabs.innerHTML = '';
    container.innerHTML = '';

    const keywords = Object.keys(data);
    console.log('论文数据类别:', keywords);
    
    if (keywords.length === 0) {
        console.warn('没有论文数据');
        container.innerHTML = '<div class="empty-state"><i class="fas fa-inbox"></i><p>暂无论文数据</p><p style="margin-top: 10px; font-size: 0.9rem;">点击"抓取新论文"按钮开始抓取</p></div>';
        return;
    }

    // 首先创建"全量"标签（默认选项）
    let totalCount = 0;
    Object.values(data).forEach(categoryPapers => {
        if (Array.isArray(categoryPapers)) {
            totalCount += categoryPapers.length;
        }
    });
    
    const allTab = document.createElement('button');
    allTab.className = 'tab active'; // 默认选中
    allTab.dataset.keyword = 'all'; // 使用特殊标识
    allTab.dataset.displayName = '全量';
    allTab.addEventListener('click', () => switchTab('all'));
    
    // 创建全量标签的文本容器（包含数字）
    const allTabText = document.createElement('span');
    allTabText.className = 'tab-text';
    allTabText.textContent = `全量 (${totalCount})`;
    allTab.appendChild(allTabText);
    
    // 创建红点提示（放在全量标签旁边，不挡住数字）
    const badge = document.createElement('span');
    badge.id = 'newPapersBadge';
    badge.className = 'new-papers-badge hidden';
    badge.title = '点击清除新论文提示';
    badge.innerHTML = '<span class="badge-dot"></span><span class="badge-count" id="newPapersCount">0</span>';
    
    // 绑定点击事件（清除红点）
    badge.addEventListener('click', (e) => {
        e.stopPropagation(); // 阻止事件冒泡，避免触发标签切换
        clearNewPapersBadge();
    });
    
    allTab.appendChild(badge);
    tabs.appendChild(allTab);
    
    // 按研究方向顺序创建标签页（显示所有研究方向，即使数据为0）
    let activeIndex = 1; // 从1开始，因为全量标签是第一个
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
        tab.className = 'tab'; // 不再默认选中
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

    // 首先创建"全量"论文列表（默认显示）
    const allPapers = [];
    Object.values(data).forEach(categoryPapers => {
        if (Array.isArray(categoryPapers)) {
            allPapers.push(...categoryPapers);
        }
    });
    
    // 应用筛选和排序
    let filteredAllPapers = filterPapers(allPapers);
    filteredAllPapers = sortPapers(filteredAllPapers);
    
    const allPaperList = document.createElement('div');
    allPaperList.className = 'paper-list active'; // 默认显示
    allPaperList.id = 'list-all';
    
    if (filteredAllPapers.length > 0) {
        filteredAllPapers.forEach(paper => {
            const paperItem = createPaperItem(paper);
            allPaperList.appendChild(paperItem);
        });
    } else {
        allPaperList.innerHTML = '<div class="empty-state"><i class="fas fa-inbox"></i><p>暂无论文数据</p><p style="margin-top: 10px; font-size: 0.9rem;">点击"抓取新论文"按钮开始抓取</p></div>';
    }
    container.appendChild(allPaperList);
    
    // 创建各研究方向的论文列表
    let listIndex = 1; // 从1开始，因为全量列表是第一个
    RESEARCH_CATEGORIES.order.forEach(displayCategory => {
        const dbCategory = Object.keys(RESEARCH_CATEGORIES.dbToDisplay).find(
            db => RESEARCH_CATEGORIES.dbToDisplay[db] === displayCategory
        );
        
        // 获取该类别的论文（如果不存在则为空数组）
        let papers = dbCategory && data[dbCategory] ? data[dbCategory] : [];
        
        // 应用筛选和排序
        papers = filterPapers(papers);
        papers = sortPapers(papers);
        
        // 创建论文列表容器（即使为空也创建）
        const paperList = document.createElement('div');
        paperList.className = 'paper-list'; // 不再默认显示
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

    // 设置默认标签页为"全量"
    currentTab = 'all';
}

// 创建论文项
function createPaperItem(paper) {
    const item = document.createElement('div');
    item.className = 'paper-item';
    
    const codeLink = paper.code_url 
        ? `<a href="${paper.code_url}" target="_blank" class="paper-link code"><i class="fas fa-code"></i> 代码</a>`
        : '<span class="paper-link disabled"><i class="fas fa-code"></i> 无代码</span>';
    
    // 构建被引用数量显示
    let citationInfo = '';
    // 调试：检查数据
    if (paper.citation_count !== undefined && paper.citation_count !== null) {
        // 即使为0也显示（用于调试）
        const influentialBadge = (paper.influential_citation_count && paper.influential_citation_count > 0)
            ? `<span class="citation-badge influential" title="高影响力引用数">⭐ ${paper.influential_citation_count}</span>`
            : '';
        citationInfo = `
            <div class="paper-citations">
                <i class="fas fa-quote-left"></i>
                <span class="citation-count">${paper.citation_count || 0}</span>
                ${influentialBadge}
            </div>
        `;
    }
    
    // 构建机构信息显示
    let affiliationInfo = '';
    if (paper.author_affiliations && Array.isArray(paper.author_affiliations) && paper.author_affiliations.length > 0) {
        const affiliations = paper.author_affiliations.slice(0, 3); // 最多显示3个机构
        const moreCount = paper.author_affiliations.length > 3 ? ` +${paper.author_affiliations.length - 3}` : '';
        affiliationInfo = `
            <div class="paper-affiliations">
                <i class="fas fa-building"></i>
                <span class="affiliations-text">${affiliations.join(', ')}${moreCount}</span>
            </div>
        `;
    }
    
    // 构建发表信息显示
    let venueInfo = '';
    if (paper.venue || paper.publication_year !== undefined) {
        const venueText = paper.venue || '';
        const yearText = paper.publication_year ? ` (${paper.publication_year})` : '';
        venueInfo = `
            <div class="paper-venue">
                <i class="fas fa-book"></i>
                <span>${venueText}${yearText}</span>
            </div>
        `;
    }
    
    // 构建摘要显示（悬停显示）
    let abstractInfo = '';
    if (paper.abstract && paper.abstract.trim()) {
        const abstractShort = paper.abstract.length > 150 
            ? paper.abstract.substring(0, 150) + '...' 
            : paper.abstract;
        abstractInfo = `
            <div class="paper-abstract" title="${paper.abstract.replace(/"/g, '&quot;')}">
                <i class="fas fa-align-left"></i>
                <span class="abstract-text">${abstractShort}</span>
                <span class="abstract-full" style="display:none;">${paper.abstract}</span>
            </div>
        `;
    }
    
    item.innerHTML = `
        <div class="paper-header">
            <div class="paper-title">
                <a href="${paper.pdf_url}" target="_blank">${paper.title}</a>
                ${paper.abstract ? `<i class="fas fa-info-circle abstract-icon" title="${paper.abstract.replace(/"/g, '&quot;')}"></i>` : ''}
            </div>
            <div class="paper-date">${paper.date}</div>
        </div>
        ${abstractInfo}
        <div class="paper-meta">
            <div class="paper-authors">
                <i class="fas fa-users"></i> ${paper.authors}
            </div>
            ${affiliationInfo}
            ${venueInfo}
            ${citationInfo}
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
        if (keyword === 'all') {
            // 如果是"全量"，显示全量列表
            if (list.id === 'list-all') {
                list.classList.add('active');
            }
        } else {
            // 否则显示对应类别的列表
            if (list.id === `list-${keyword}`) {
                list.classList.add('active');
            }
        }
    });

    currentTab = keyword;
    
    // 更新标签页文本（保持数量显示和显示名称）
    if (keyword === 'all') {
        // 更新全量标签的数量（不更新红点，红点由updateNewPapersBadge单独管理）
        const activeTab = document.querySelector(`.tab[data-keyword="all"]`);
        if (activeTab) {
            const tabText = activeTab.querySelector('.tab-text');
            if (tabText) {
                let totalCount = 0;
                Object.values(papersData).forEach(categoryPapers => {
                    if (Array.isArray(categoryPapers)) {
                        totalCount += categoryPapers.length;
                    }
                });
                tabText.textContent = `全量 (${totalCount})`;
            }
        }
    } else if (papersData[keyword]) {
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
    
    // 获取按钮并添加加载状态
    const fetchBtn = document.querySelector('.btn-fetch-primary');
    const originalBtnContent = fetchBtn.innerHTML;
    
    // 添加加载状态
    fetchBtn.classList.add('loading');
    fetchBtn.innerHTML = '<i class="fas fa-spinner"></i> 抓取中...';
    fetchBtn.disabled = true;

    // 延迟关闭弹窗，让用户看到加载状态
    setTimeout(() => {
        closeFetchModal();
        
        // 显示抓取状态
        const statusDiv = document.getElementById('fetchStatus');
        statusDiv.classList.remove('hidden');
        
        // 重置lastFetchUpdate，确保抓取完成后能刷新
        lastFetchUpdate = null;
    }, 300);

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
    } finally {
        // 恢复按钮状态（如果弹窗还在）
        const fetchBtn = document.querySelector('.btn-fetch-primary');
        if (fetchBtn && !fetchBtn.disabled) {
            // 如果按钮还在弹窗中且未被禁用，说明可能出错或弹窗未关闭
            const originalBtnContent = '<i class="fas fa-rocket"></i> 开始抓取';
            fetchBtn.classList.remove('loading');
            fetchBtn.innerHTML = originalBtnContent;
            fetchBtn.disabled = false;
        }
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
                        // 强制刷新统计和论文数据（显示新论文提示）
                        loadStats();
                        loadPapers(true); // 传入true以显示新论文提示
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

// 加载招聘信息
async function loadJobs() {
    const container = document.getElementById('jobsContainer');
    const countElement = document.getElementById('jobsCount');

    if (!container) {
        console.warn('loadJobs: 找不到jobsContainer元素，跳过加载');
        return; // 如果元素不存在，直接返回
    }

    try {
        console.log('loadJobs: 开始调用 /api/jobs API...');
        const response = await fetch('/api/jobs?limit=20');
        console.log('loadJobs: API响应状态:', response.status, response.statusText);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (result.success && result.jobs) {
            // 更新总数
            if (countElement) {
                countElement.textContent = result.total || result.jobs.length;
            }
            
            // 渲染招聘信息
            if (result.jobs.length === 0) {
                container.innerHTML = '<div class="loading-spinner-small"><p>暂无招聘信息</p></div>';
            } else {
                // 在前端再次排序，确保从近到远（最新的在前）
                const sortedJobs = [...result.jobs].sort((a, b) => {
                    const dateA = parseJobDate(a.update_date || a.source_date || '');
                    const dateB = parseJobDate(b.update_date || b.source_date || '');
                    // 降序排列（最新的在前）
                    if (dateB.year !== dateA.year) return dateB.year - dateA.year;
                    if (dateB.month !== dateA.month) return dateB.month - dateA.month;
                    return dateB.day - dateA.day;
                });
                
                container.innerHTML = sortedJobs.map(job => createJobItem(job)).join('');
            }
        } else {
            const errorMsg = result.error || '未知错误';
            console.error('API返回错误:', errorMsg);
            container.innerHTML = `<div class="loading-spinner-small"><p>加载失败: ${errorMsg}</p></div>`;
        }
    } catch (error) {
        console.error('加载招聘信息失败:', error);
        if (container) {
            const errorMsg = error.message || '网络错误，请检查服务器是否运行';
            container.innerHTML = `<div class="loading-spinner-small"><p>加载失败: ${errorMsg}</p><p style="font-size:0.75rem;color:#999;margin-top:8px;">提示: 请重启Flask服务器以加载新的API路由</p></div>`;
        }
    }
}

// 解析招聘日期字符串为可比较的对象（必须在loadJobs之前定义）
function parseJobDate(dateStr) {
    if (!dateStr) {
        return { year: 0, month: 0, day: 0 };
    }
    try {
        const parts = dateStr.split('.');
        if (parts.length === 3) {
            return {
                year: parseInt(parts[0], 10) || 0,
                month: parseInt(parts[1], 10) || 0,
                day: parseInt(parts[2], 10) || 0
            };
        }
    } catch (e) {
        console.warn('日期解析失败:', dateStr, e);
    }
    return { year: 0, month: 0, day: 0 };
}

// 创建招聘信息项
function createJobItem(job) {
    const date = job.update_date || job.source_date || '';
    const title = job.title || '未知职位';
    const link = job.link || '#';
    const company = job.company || '';
    const location = job.location || '';
    const jobType = job.job_type || '';
    
    let metaHtml = '';
    if (company || location || jobType) {
        const metaItems = [];
        if (company) metaItems.push(`<span>${company}</span>`);
        if (location) metaItems.push(`<span>${location}</span>`);
        if (jobType) metaItems.push(`<span>${jobType}</span>`);
        metaHtml = `<div class="job-item-meta">${metaItems.join('')}</div>`;
    }
    
    const onClick = link && link !== '#' ? `onclick="window.open('${link}', '_blank')"` : '';
    
    return `
        <div class="job-item" ${onClick}>
            <div class="job-item-date">${date}</div>
            <div class="job-item-title">${title}</div>
            ${metaHtml}
        </div>
    `;
}

// 加载数据集信息
async function loadDatasets() {
    const container = document.getElementById('datasetsContainer');
    const countElement = document.getElementById('datasetsCount');
    
    if (!container) {
        return; // 如果元素不存在，直接返回
    }
    
    try {
        const response = await fetch('/api/datasets?limit=20');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (result.success && result.datasets) {
            // 更新总数
            if (countElement) {
                countElement.textContent = result.total || result.datasets.length;
            }
            
            // 渲染数据集信息
            if (result.datasets.length === 0) {
                container.innerHTML = '<div class="loading-spinner-small"><p>暂无数据集信息</p><p style="font-size:0.75rem;color:#999;margin-top:8px;">数据整理中...</p></div>';
            } else {
                container.innerHTML = result.datasets.map(dataset => createDatasetItem(dataset)).join('');
            }
        } else {
            const errorMsg = result.error || '未知错误';
            console.error('API返回错误:', errorMsg);
            container.innerHTML = `<div class="loading-spinner-small"><p>加载失败: ${errorMsg}</p></div>`;
        }
    } catch (error) {
        console.error('加载数据集信息失败:', error);
        if (container) {
            const errorMsg = error.message || '网络错误，请检查服务器是否运行';
            container.innerHTML = `<div class="loading-spinner-small"><p>加载失败: ${errorMsg}</p><p style="font-size:0.75rem;color:#999;margin-top:8px;">提示: 请重启Flask服务器以加载新的API路由</p></div>`;
        }
    }
}

// 创建数据集信息项
function createDatasetItem(dataset) {
    const name = dataset.name || '未知数据集';
    const description = dataset.description || '';
    const publisher = dataset.publisher || '';
    const publishDate = dataset.publish_date || '';
    const projectLink = dataset.project_link || '';
    const paperLink = dataset.paper_link || '';
    const datasetLink = dataset.dataset_link || dataset.link || '';
    const scale = dataset.scale || '';
    const category = dataset.category || '';
    const tags = dataset.tags || [];
    
    // 构建信息行
    let infoHtml = '';
    if (publisher || publishDate) {
        const infoParts = [];
        if (publisher) infoParts.push(`<strong>发布方:</strong> ${publisher}`);
        if (publishDate) infoParts.push(`<strong>发布时间:</strong> ${publishDate}`);
        if (infoParts.length > 0) {
            infoHtml = `<div class="dataset-item-info">${infoParts.join(' | ')}</div>`;
        }
    }
    
    if (scale) {
        infoHtml += `<div class="dataset-item-info"><strong>规模:</strong> ${scale}</div>`;
    }
    
    // 构建标签
    let tagsHtml = '';
    const allTags = [];
    if (category) allTags.push(category);
    if (Array.isArray(tags)) allTags.push(...tags);
    if (allTags.length > 0) {
        const tagItems = allTags.map(tag => `<span>${tag}</span>`).join('');
        tagsHtml = `<div class="dataset-item-meta">${tagItems}</div>`;
    }
    
    // 构建链接
    let linksHtml = '';
    const links = [];
    if (projectLink) {
        links.push(`<a href="${projectLink}" target="_blank" class="dataset-item-link" onclick="event.stopPropagation()"><i class="fas fa-globe"></i> 项目</a>`);
    }
    if (paperLink) {
        links.push(`<a href="${paperLink}" target="_blank" class="dataset-item-link" onclick="event.stopPropagation()"><i class="fas fa-file-pdf"></i> 论文</a>`);
    }
    if (datasetLink) {
        links.push(`<a href="${datasetLink}" target="_blank" class="dataset-item-link" onclick="event.stopPropagation()"><i class="fas fa-database"></i> 数据集</a>`);
    }
    if (links.length > 0) {
        linksHtml = `<div class="dataset-item-links">${links.join('')}</div>`;
    }
    
    const onClick = datasetLink && datasetLink !== '#' ? `onclick="window.open('${datasetLink}', '_blank')"` : '';
    
    return `
        <div class="dataset-item" ${onClick}>
            <div class="dataset-item-name">${name}</div>
            ${description ? `<div class="dataset-item-description">${description}</div>` : ''}
            ${infoHtml}
            ${tagsHtml}
            ${linksHtml}
        </div>
    `;
}

// 新闻自动滚动相关变量
let newsScrollResumeTimer = null;

// 加载新闻信息
async function loadNews() {
    const container = document.getElementById('newsContainer');
    const countElement = document.getElementById('newsCount');
    
    if (!container) {
        console.warn('loadNews: 找不到newsContainer元素，跳过加载');
        return; // 如果元素不存在，直接返回
    }
    
    try {
        console.log('loadNews: 开始调用 /api/news API...');
        const response = await fetch('/api/news?limit=30');  // 增加到30条
        console.log('loadNews: API响应状态:', response.status, response.statusText);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (result.success && result.news) {
            // 更新总数
            if (countElement) {
                countElement.textContent = result.total || result.news.length;
            }
            
            // 渲染新闻信息
            if (result.news.length === 0) {
                container.innerHTML = '<div class="loading-spinner-small"><p>暂无新闻信息</p></div>';
                container.classList.remove('scrolling');
            } else {
                // 确保新闻按发布时间从新到旧排序（后端已排序，这里再次确认）
                const sortedNews = [...result.news].sort((a, b) => {
                    const timeA = a.published_at || a.created_at || '';
                    const timeB = b.published_at || b.created_at || '';
                    if (!timeA && !timeB) return 0;
                    if (!timeA) return 1; // A没有时间，排在后面
                    if (!timeB) return -1; // B没有时间，排在后面
                    return new Date(timeB) - new Date(timeA); // 从新到旧
                });
                
                // 渲染新闻列表，支持自动滚动和手动滚动
                const newsHtml = sortedNews.map(news => createNewsItem(news)).join('');
                // 复制内容以实现无缝循环滚动
                const duplicatedNews = sortedNews.map(news => createNewsItem(news)).join('');
                container.innerHTML = `<div class="news-scroll-container">${newsHtml}${duplicatedNews}</div>`;
                container.classList.add('scrolling');
                
                // 设置滚动事件监听
                setupNewsScrollHandlers(container);
            }
        } else {
            const errorMsg = result.error || '未知错误';
            console.error('API返回错误:', errorMsg);
            container.innerHTML = `<div class="loading-spinner-small"><p>加载失败: ${errorMsg}</p></div>`;
            container.classList.remove('scrolling');
        }
    } catch (error) {
        console.error('加载新闻信息失败:', error);
        if (container) {
            const errorMsg = error.message || '网络错误，请检查服务器是否运行';
            container.innerHTML = `<div class="loading-spinner-small"><p>加载失败: ${errorMsg}</p><p style="font-size:0.75rem;color:#999;margin-top:8px;">请检查服务器是否正常运行</p></div>`;
            container.classList.remove('scrolling');
        }
    }
}

// 设置新闻滚动事件处理
function setupNewsScrollHandlers(container) {
    const scrollContainer = container.querySelector('.news-scroll-container');
    if (!scrollContainer) return;
    
    let isUserScrolling = false;
    let scrollTimeout = null;
    let lastScrollTime = 0;
    
    // 切换到手动滚动模式
    function switchToManualScroll() {
        const now = Date.now();
        // 防止频繁切换
        if (now - lastScrollTime < 50) {
            return;
        }
        lastScrollTime = now;
        
        if (!isUserScrolling) {
            isUserScrolling = true;
            // 获取当前动画位置
            const computedStyle = window.getComputedStyle(scrollContainer);
            const transform = computedStyle.transform;
            let currentY = 0;
            
            if (transform && transform !== 'none') {
                const matrix = transform.match(/matrix\(([^)]+)\)/);
                if (matrix) {
                    const values = matrix[1].split(',').map(v => parseFloat(v.trim()));
                    if (values.length >= 6) {
                        currentY = Math.abs(values[5]); // translateY值
                    }
                }
            }
            
            // 停止动画
            scrollContainer.style.animationPlayState = 'paused';
            scrollContainer.style.animation = 'none';
            scrollContainer.style.transform = 'none';
            
            // 切换到手动滚动模式
            container.classList.remove('scrolling');
            container.classList.add('manual-scroll');
            
            // 设置滚动位置
            if (currentY > 0) {
                container.scrollTop = currentY;
            }
        }
        
        // 清除之前的恢复定时器
        if (scrollTimeout) {
            clearTimeout(scrollTimeout);
        }
        
        // 3秒后恢复自动滚动
        scrollTimeout = setTimeout(() => {
            switchToAutoScroll();
        }, 3000);
    }
    
    // 切换到自动滚动模式
    function switchToAutoScroll() {
        if (!isUserScrolling) return;
        
        isUserScrolling = false;
        const currentScrollTop = container.scrollTop;
        
        // 切换回自动滚动模式
        container.classList.remove('manual-scroll');
        container.classList.add('scrolling');
        
        // 恢复动画
        scrollContainer.style.animation = 'scrollNews 120s linear infinite';
        scrollContainer.style.animationPlayState = 'running';
        
        // 设置初始位置（从当前滚动位置开始）
        if (currentScrollTop > 0) {
            scrollContainer.style.transform = `translateY(-${currentScrollTop}px)`;
        } else {
            scrollContainer.style.transform = 'translateY(0)';
        }
    }
    
    // 监听鼠标滚轮
    container.addEventListener('wheel', (e) => {
        switchToManualScroll();
    }, { passive: true });
    
    // 监听触摸事件
    container.addEventListener('touchstart', () => {
        switchToManualScroll();
    }, { passive: true });
    
    container.addEventListener('touchmove', () => {
        switchToManualScroll();
    }, { passive: true });
    
    // 监听滚动条拖动
    container.addEventListener('mousedown', () => {
        switchToManualScroll();
    });
    
    // 监听滚动事件（用户拖动滚动条）
    container.addEventListener('scroll', () => {
        if (container.classList.contains('manual-scroll')) {
            switchToManualScroll();
        }
    }, { passive: true });
    
    // 监听鼠标进入/离开（悬停时暂停）
    container.addEventListener('mouseenter', () => {
        if (container.classList.contains('scrolling') && scrollContainer) {
            scrollContainer.style.animationPlayState = 'paused';
        }
    });
    
    container.addEventListener('mouseleave', () => {
        if (container.classList.contains('scrolling') && scrollContainer && !isUserScrolling) {
            scrollContainer.style.animationPlayState = 'running';
        }
    });
}

// 创建新闻信息项
function createNewsItem(news) {
    const title = news.title || '未知新闻';
    const description = news.description || '';
    const link = news.link || '#';
    const platform = news.platform || '';
    const source = news.source || '';
    const publishedAt = news.published_at || '';
    const createdAt = news.created_at || '';
    // 不显示图片，已移除 imageUrl 变量
    
    // 格式化显示时间
    // 优先使用created_at（刷新时间），如果没有则使用published_at（发布时间）
    // 这样可以显示最新刷新的新闻，而不是原始发布时间
    let displayTime = null;
    const timeToUse = createdAt || publishedAt; // 优先使用created_at
    
    if (timeToUse) {
        try {
            // 解析时间字符串（格式：2025-12-09 08:20:34）
            // 需要处理时区问题，确保正确解析为本地时间
            const timeStr = timeToUse.trim();
            // 如果格式是 "YYYY-MM-DD HH:MM:SS"，需要手动解析为本地时间
            if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(timeStr)) {
                const [datePart, timePart] = timeStr.split(' ');
                const [year, month, day] = datePart.split('-').map(Number);
                const [hour, minute, second] = timePart.split(':').map(Number);
                // 使用本地时区创建Date对象
                displayTime = new Date(year, month - 1, day, hour, minute, second);
            } else {
                // 尝试标准解析
                displayTime = new Date(timeStr);
            }
            
            // 验证日期是否有效
            if (isNaN(displayTime.getTime())) {
                displayTime = null;
            }
        } catch (e) {
            console.error('解析时间失败:', timeToUse, e);
            displayTime = null;
        }
    }
    
    let timeHtml = '';
    if (displayTime) {
        try {
            const now = new Date();
            const diffMs = now - displayTime;
            const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
            const diffDays = Math.floor(diffHours / 24);
            
            if (diffHours < 1) {
                const diffMinutes = Math.floor(diffMs / (1000 * 60));
                if (diffMinutes < 1) {
                    timeHtml = `<div class="news-item-time">刚刚</div>`;
                } else {
                    timeHtml = `<div class="news-item-time">${diffMinutes}分钟前</div>`;
                }
            } else if (diffHours < 24) {
                timeHtml = `<div class="news-item-time">${diffHours}小时前</div>`;
            } else if (diffDays < 7) {
                timeHtml = `<div class="news-item-time">${diffDays}天前</div>`;
            } else {
                timeHtml = `<div class="news-item-time">${displayTime.toLocaleDateString('zh-CN')}</div>`;
            }
        } catch (e) {
            console.error('计算时间差失败:', e);
            timeHtml = '';
        }
    }
    
    // 平台标签
    let platformHtml = '';
    if (platform || source) {
        platformHtml = `<div class="news-item-platform">${platform || source}</div>`;
    }
    
    // 不显示图片（移除图片显示）
    
    const onClick = link && link !== '#' ? `onclick="window.open('${link}', '_blank')"` : '';
    
    // 确保不包含任何图片元素
    return `
        <div class="news-item" ${onClick}>
            <div class="news-item-content">
                <div class="news-item-header">
                    ${platformHtml}
                    ${timeHtml}
                </div>
                <div class="news-item-title">${title}</div>
                <!-- 不显示新闻预览（description） -->
            </div>
        </div>
    `;
}

// 刷新所有数据
// refreshStatusInterval 已在文件顶部声明，不需要重复声明

async function refreshAllData() {
    const btn = document.getElementById('refreshAllBtn');
    if (!btn) return;
    
    // 禁用按钮，显示加载状态
    const originalHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 刷新中...';
    
    // 清除之前的轮询
    if (refreshStatusInterval) {
        clearInterval(refreshStatusInterval);
    }
    
    try {
        // 调用后端API启动刷新任务
        const response = await fetch('/api/refresh-all', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // 检查响应状态
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 200)}`);
        }
        
        // 检查响应内容类型
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`服务器返回了非JSON响应，可能是404错误。请重启Flask服务器。响应内容: ${text.substring(0, 200)}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            console.log('刷新任务已启动，开始轮询状态...');
            console.log('初始状态:', result.status);
            // 开始轮询刷新状态
            refreshStatusInterval = setInterval(async () => {
                try {
                    console.log('轮询刷新状态...');
                    const statusResponse = await fetch('/api/refresh-status');
                    const status = await statusResponse.json();
                    console.log('当前刷新状态:', status);
                    
                    // 更新按钮显示当前状态
                    const messages = [];
                    if (status.papers && status.papers.status === 'running') {
                        messages.push('论文刷新中...');
                    }
                    if (status.jobs && status.jobs.status === 'running') {
                        messages.push('招聘刷新中...');
                    }
                    if (status.news && status.news.status === 'running') {
                        messages.push('新闻刷新中...');
                    }
                    
                    if (messages.length > 0) {
                        btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${messages[0]}`;
                    }
                    
                    // 检查是否全部完成
                    // 判断标准：所有任务的状态都不是 'running' 或 'pending'
                    const allTasksDone = (
                        status.papers && 
                        status.papers.status !== 'running' && 
                        status.papers.status !== 'pending' &&
                        status.jobs && 
                        status.jobs.status !== 'running' && 
                        status.jobs.status !== 'pending' &&
                        status.news && 
                        status.news.status !== 'running' && 
                        status.news.status !== 'pending'
                    );
                    
                    if (allTasksDone || !status.running) {
                        console.log('所有刷新任务已完成，状态:', status);
                        clearInterval(refreshStatusInterval);
                        refreshStatusInterval = null;
                        
                        // 显示刷新结果
                        const statuses = [];
                        const errors = [];
                        if (status.papers) {
                            if (status.papers.status === 'success') {
                                statuses.push('论文✓');
                            } else if (status.papers.status === 'error') {
                                statuses.push('论文✗');
                                errors.push(`论文刷新失败: ${status.papers.message || '未知错误'}`);
                            } else {
                                statuses.push('论文?');
                            }
                        }
                        if (status.jobs) {
                            if (status.jobs.status === 'success') {
                                statuses.push('招聘✓');
                            } else if (status.jobs.status === 'error') {
                                statuses.push('招聘✗');
                                errors.push(`招聘刷新失败: ${status.jobs.message || '未知错误'}`);
                            } else {
                                statuses.push('招聘?');
                            }
                        }
                        if (status.news) {
                            if (status.news.status === 'success') {
                                statuses.push('新闻✓');
                            } else if (status.news.status === 'error') {
                                statuses.push('新闻✗');
                                errors.push(`新闻刷新失败: ${status.news.message || '未知错误'}`);
                            } else {
                                statuses.push('新闻?');
                            }
                        }
                        
                        console.log('刷新完成，状态:', status);
                        console.log('刷新结果:', statuses);
                        if (errors.length > 0) {
                            console.error('刷新错误:', errors);
                        }
                        
                        // 重新加载所有数据（无论成功或失败，都重新加载以显示最新状态）
                        console.log('开始重新加载数据...');
                        console.log('1. 重新加载论文数据...');
                        loadPapers(true); // 刷新时显示新论文提示
                        console.log('2. 重新加载统计信息...');
                        loadStats();
                        console.log('3. 重新加载招聘信息...');
                        loadJobs();
                        // 强制重新加载新闻（清除可能的缓存）
                        console.log('4. 重新加载新闻信息...');
                        loadNews();
                        // 延迟再次加载，确保后端数据已更新
                        setTimeout(() => {
                            console.log('延迟重新加载数据（确保后端数据已更新）...');
                            console.log('延迟加载新闻...');
                            loadNews();
                            console.log('延迟加载招聘...');
                            loadJobs();
                            console.log('延迟加载论文...');
                            loadPapers(true);
                        }, 2000);
                        
                        // 恢复按钮
                        btn.disabled = false;
                        btn.innerHTML = originalHTML;
                        
                        // 显示刷新结果（包含错误信息）
                        if (errors.length > 0) {
                            alert('刷新完成：' + statuses.join(' ') + '\n\n错误信息：\n' + errors.join('\n'));
                        } else {
                            alert('刷新完成：' + statuses.join(' ') + '\n\n数据已重新加载，请查看页面更新。');
                        }
                    }
                } catch (error) {
                    console.error('获取刷新状态失败:', error);
                }
            }, 2000); // 每2秒轮询一次
        } else {
            throw new Error(result.error || '刷新失败');
        }
    } catch (error) {
        console.error('刷新数据失败:', error);
        alert('刷新失败: ' + error.message);
        
        // 恢复按钮
        btn.disabled = false;
        btn.innerHTML = originalHTML;
        
        // 清除轮询
        if (refreshStatusInterval) {
            clearInterval(refreshStatusInterval);
            refreshStatusInterval = null;
        }
    }
}

// ==================== 具身运势抽签功能 ====================

// 初始化抽签挂件
function initFortuneWidget() {
    // 更新日期显示
    const dateElement = document.getElementById('fortuneDate');
    if (dateElement) {
        const today = new Date();
        const month = today.getMonth() + 1;
        const day = today.getDate();
        dateElement.textContent = `${month}月${day}日`;
    }
    
    // 初始化研究方向标签
    const categoryTags = document.querySelectorAll('.category-tag');
    let currentCategory = localStorage.getItem('fortuneCategory') || 'all';
    
    categoryTags.forEach(tag => {
        const category = tag.getAttribute('data-category');
        if (category === currentCategory) {
            tag.classList.add('active');
        }
        
        tag.addEventListener('click', function() {
            // 切换标签状态
            categoryTags.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            currentCategory = category;
            localStorage.setItem('fortuneCategory', category);
        });
    });
    
    // 绑定抽签筒点击事件（筒本身可点击）
    const tubeMain = document.getElementById('fortuneTubeMain');
    if (tubeMain) {
        tubeMain.addEventListener('click', function() {
            // 检查今天是否已经抽过签（同一方向）
            const today = new Date().toDateString();
            const savedDate = localStorage.getItem('fortuneDate');
            const savedCategory = localStorage.getItem('fortuneCategory');
            
            if (savedDate === today && savedCategory === currentCategory) {
                // 今天已经抽过这个方向的签，显示结果
                const savedMessage = localStorage.getItem('fortuneMessage');
                const savedTimestamp = localStorage.getItem('fortuneTimestamp');
                if (savedMessage) {
                    showFortuneResult(savedMessage, savedTimestamp);
                    return;
                }
            }
            
            // 抽签
            drawFortune(currentCategory);
        });
    }
    
    // 保留摇签按钮事件（虽然隐藏了，但保留逻辑）
    const shakeBtn = document.getElementById('fortuneShakeBtn');
    if (shakeBtn) {
        shakeBtn.addEventListener('click', function() {
            // 检查今天是否已经抽过签（同一方向）
            const today = new Date().toDateString();
            const savedDate = localStorage.getItem('fortuneDate');
            const savedCategory = localStorage.getItem('fortuneCategory');
            
            if (savedDate === today && savedCategory === currentCategory) {
                // 今天已经抽过这个方向的签，显示结果
                const savedMessage = localStorage.getItem('fortuneMessage');
                const savedTimestamp = localStorage.getItem('fortuneTimestamp');
                if (savedMessage) {
                    showFortuneResult(savedMessage, savedTimestamp);
                    return;
                }
            }
            
            // 抽签
            drawFortune(currentCategory);
        });
    }
    
    // 初始化筒内竹签显示
    initTubeSticks();
    
    // 检查今天是否已经抽过签
    checkTodayFortune();
}

// 初始化筒内竹签显示
function initTubeSticks() {
    const tubeSticks = document.getElementById('tubeSticks');
    if (!tubeSticks) return;
    
    // 创建多个竹签元素，营造筒内有很多签的感觉
    tubeSticks.innerHTML = '';
    for (let i = 0; i < 20; i++) {
        const stick = document.createElement('div');
        stick.className = 'tube-stick-item';
        stick.style.left = Math.random() * 80 + '%';
        stick.style.top = Math.random() * 60 + '%';
        stick.style.transform = `rotate(${Math.random() * 360}deg)`;
        stick.style.opacity = 0.3 + Math.random() * 0.4;
        tubeSticks.appendChild(stick);
    }
}

// 更新标签状态
function updateCategoryTagStates(selectedCategory) {
    const tags = document.querySelectorAll('.category-tag');
    tags.forEach(tag => {
        const category = tag.getAttribute('data-category');
        if (category === selectedCategory) {
            tag.classList.add('active');
        } else {
            tag.classList.remove('active');
        }
    });
}

// 检查今天是否已经抽过签
function checkTodayFortune() {
    const today = new Date().toDateString();
    const savedDate = localStorage.getItem('fortuneDate');
    const savedMessage = localStorage.getItem('fortuneMessage');
    const savedTimestamp = localStorage.getItem('fortuneTimestamp');
    const savedCategory = localStorage.getItem('fortuneCategory');
    
    if (savedDate === today && savedMessage && savedCategory) {
        // 今天已经抽过签，显示结果
        showFortuneResult(savedMessage, savedTimestamp);
        
        // 更新标签状态
        updateCategoryTagStates(savedCategory);
    } else {
        // 今天没有抽过签，重置状态
        resetFortuneWidget();
    }
}

// 重置运势签状态
function resetFortuneWidget() {
    const fortuneResult = document.getElementById('fortuneResult');
    const flyingStick = document.getElementById('fortuneStickFlying');
    const shakeBtn = document.getElementById('fortuneShakeBtn');
    const tubeMain = document.getElementById('fortuneTubeMain');
    
    if (fortuneResult) {
        fortuneResult.classList.add('hidden');
    }
    
    if (flyingStick) {
        flyingStick.classList.remove('show', 'fly-out', 'expand');
        flyingStick.style.position = '';
        flyingStick.style.left = '';
        flyingStick.style.top = '';
        flyingStick.style.transform = '';
    }
    
    if (shakeBtn) {
        shakeBtn.disabled = false;
    }
    
    if (tubeMain) {
        tubeMain.style.opacity = '1';
        tubeMain.style.pointerEvents = 'auto';
    }
}

// 清除抽签记录（用于调试或重置）
function clearFortuneRecord() {
    localStorage.removeItem('fortuneDate');
    localStorage.removeItem('fortuneMessage');
    localStorage.removeItem('fortuneTimestamp');
    localStorage.removeItem('fortuneCategory');
    resetFortuneWidget();
    console.log('抽签记录已清除');
    // 刷新页面以重置状态
    location.reload();
}

// 抽签主函数
function drawFortune(category) {
    const tubeMain = document.getElementById('fortuneTubeMain');
    const shakeBtn = document.getElementById('fortuneShakeBtn');
    const flyingStick = document.getElementById('fortuneStickFlying');
    const fortuneResult = document.getElementById('fortuneResult');
    
    if (!tubeMain || !shakeBtn) {
        return;
    }
    
    // 禁用抽签筒点击（通过添加禁用类）
    if (tubeMain) {
        tubeMain.style.pointerEvents = 'none';
        tubeMain.style.opacity = '0.8';
    }
    
    // 禁用摇签按钮（虽然隐藏了，但保留逻辑）
    if (shakeBtn) {
        shakeBtn.disabled = true;
    }
    
    // 隐藏之前的结果和飞出的签
    if (fortuneResult) {
        fortuneResult.classList.add('hidden');
    }
    if (flyingStick) {
        flyingStick.classList.remove('show', 'fly-out', 'expand');
    }
    
    // 开始摇筒动画
    if (tubeMain) {
        tubeMain.classList.add('shaking');
    }
    
    // 摇筒动画持续2秒
    setTimeout(() => {
        // 停止摇筒动画
        tubeMain.classList.remove('shaking');
        
        // 获取随机词条
        const message = getRandomFortune(category);
        const timestamp = new Date().toLocaleString('zh-CN', {
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        // 保存到localStorage
        const today = new Date().toDateString();
        localStorage.setItem('fortuneDate', today);
        localStorage.setItem('fortuneMessage', message);
        localStorage.setItem('fortuneTimestamp', timestamp);
        localStorage.setItem('fortuneCategory', category);
        
        // 签从筒中飞出
        if (flyingStick) {
            const stickContent = document.getElementById('fortuneStickContent');
            if (stickContent) {
                stickContent.textContent = message;
            }
            
            // 计算筒的位置，让签从筒的位置飞出
            const tubeRect = tubeMain.getBoundingClientRect();
            const containerRect = document.getElementById('fortuneContainer').getBoundingClientRect();
            const tubeCenterX = tubeRect.left + tubeRect.width / 2 - containerRect.left;
            const tubeCenterY = tubeRect.top + tubeRect.height / 2 - containerRect.top;
            
            // 设置飞出签的初始位置（筒的中心，相对于容器）
            flyingStick.style.position = 'absolute';
            flyingStick.style.left = tubeCenterX + 'px';
            flyingStick.style.top = tubeCenterY + 'px';
            flyingStick.style.transform = 'translate(-50%, -50%)';
            
            // 显示飞出的签
            flyingStick.classList.add('show');
            
            // 飞出动画
            setTimeout(() => {
                flyingStick.classList.add('fly-out');
                
                // 展开动画
                setTimeout(() => {
                    flyingStick.classList.add('expand');
                    
                    // 显示结果覆盖层
                    setTimeout(() => {
                        showFortuneResult(message, timestamp);
                        
                        // 隐藏筒
                        if (tubeMain) {
                            tubeMain.style.opacity = '0';
                        }
                    }, 500);
                }, 800);
            }, 100);
        } else {
            // 如果没有飞出动画，直接显示结果
            showFortuneResult(message, timestamp);
            if (tubeMain) {
                tubeMain.style.opacity = '0';
            }
        }
    }, 2000);
}

// 获取随机运势词条（根据研究方向过滤）
function getRandomFortune(category) {
    if (typeof FORTUNE_MESSAGES === 'undefined' || !FORTUNE_MESSAGES || FORTUNE_MESSAGES.length === 0) {
        return '今日你的具身智能研究将获得突破性进展！';
    }
    
    const selectedCategory = category || 'all';
    
    // 根据研究方向过滤祝福语
    let filteredMessages = filterFortuneByCategory(FORTUNE_MESSAGES, selectedCategory);
    
    // 如果过滤后没有消息，使用全部消息
    if (filteredMessages.length === 0) {
        filteredMessages = FORTUNE_MESSAGES;
    }
    
    // 使用真正的随机数，确保每次抽签都是随机的
    // 结合时间戳、随机数和研究方向，增加随机性
    // 使用多个随机源组合，确保真正的随机性
    const timestamp = Date.now();
    const randomComponent1 = Math.random() * 1000000;
    const randomComponent2 = Math.random() * 1000000;
    const categoryHash = selectedCategory.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    
    // 组合多个随机源，确保每次都是不同的随机数
    const combinedRandom = (timestamp + randomComponent1 + randomComponent2 + categoryHash + Math.random() * 1000000) % 2147483647;
    
    // 使用更复杂的随机数生成算法（线性同余生成器增强）
    let random = combinedRandom;
    for (let i = 0; i < 7; i++) {  // 增加迭代次数，提高随机性
        random = (random * 1103515245 + 12345) & 0x7fffffff;
        // 再次混合Math.random()，确保真正的随机性
        random = (random + Math.floor(Math.random() * 1000)) % 2147483647;
    }
    
    // 最终使用Math.random()确保真正的随机性
    const finalRandom = Math.random() * 0.5 + (random / 0x7fffffff) * 0.5;
    const index = Math.floor(finalRandom * filteredMessages.length);
    
    // 调试信息（可以在控制台查看）
    if (filteredMessages.length < FORTUNE_MESSAGES.length) {
        console.log('✅ 过滤成功 - 研究方向:', selectedCategory, '过滤后数量:', filteredMessages.length, '/', FORTUNE_MESSAGES.length);
    }
    
    return filteredMessages[index];
}

// 根据研究方向过滤祝福语
function filterFortuneByCategory(messages, category) {
    if (category === 'all') {
        return messages;
    }
    
    // 研究方向关键词映射
    const categoryKeywords = {
        'Perception': ['感知', '视觉', '场景', '识别', '理解', '图像', '视觉感知', '场景理解', '视觉理解'],
        'VLM': ['视觉语言', 'VLM', '多模态', '视觉-语言', '视觉语言模型', '多模态学习'],
        'Planning': ['规划', '路径', '轨迹', '路径规划', '轨迹规划', '任务规划', '运动规划'],
        'RL/IL': ['强化学习', '模仿学习', 'RL', 'IL', '训练', '策略', '奖励', '梯度', '收敛', '优化器', '学习率'],
        'Manipulation': ['操作', '抓取', '抓取策略', '操作控制', '机器人操作', '力控制', '力反馈'],
        'Locomotion': ['运动', '行走', '平衡', '步态', '双足', '四足', '移动', '导航', '定位', '避障', '路径规划'],
        'Dexterous': ['灵巧', '精细', '灵巧操作', '精细操作', '灵巧手', '灵巧控制'],
        'VLA': ['视觉语言动作', 'VLA', '具身', '具身智能', '具身学习', '具身导航', '具身操作', '具身感知', '具身规划'],
        'Humanoid': ['人形', '人形机器人', '双足', '行走', '平衡', '步态', '人形控制']
    };
    
    const keywords = categoryKeywords[category] || [];
    if (keywords.length === 0) {
        return messages;
    }
    
    // 过滤包含关键词的消息
    return messages.filter(message => {
        return keywords.some(keyword => message.includes(keyword));
    });
}

// 显示抽签结果
function showFortuneResult(message, timestamp) {
    const fortuneResult = document.getElementById('fortuneResult');
    const fortuneMessage = document.getElementById('fortuneMessage');
    const fortuneTimestamp = document.getElementById('fortuneTimestamp');
    
    if (!fortuneResult || !fortuneMessage) {
        return;
    }
    
    fortuneMessage.textContent = message;
    
    if (fortuneTimestamp) {
        fortuneTimestamp.textContent = `抽签时间：${timestamp}`;
    }
    
    // 显示结果覆盖层
    fortuneResult.classList.remove('hidden');
}

