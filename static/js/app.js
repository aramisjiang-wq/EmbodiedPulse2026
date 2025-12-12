// 全局状态
let currentTab = null;
let papersData = {};
let statsData = {};
let lastFetchUpdate = null; // 记录上次抓取完成时间，避免重复刷新
let statusPollingInterval = null; // 论文抓取轮询定时器
let newsStatusPollingInterval = null; // 新闻抓取轮询定时器
let refreshStatusInterval = null; // 刷新状态轮询定时器
let trendsChart = null;  // 趋势图表实例
let currentTrendDays = 30;  // 当前选择的天数

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
        // 新规则：不再需要localStorage的papersLastViewed
        // 后端直接返回今天新创建的论文数量，每天自动重置
        loadPapers(true); // 初始化时检查新论文
        loadCategories();
        // loadJobs(); // 已隐藏岗位机会挂件
        loadDatasets();
        loadNews();
        loadBilibili();
        loadTrends();
        initFortuneWidget();
        initBilibiliToggle();
        setupEventListeners();
        setupFilterSortListeners();
        // 注意：startStatusPolling() 只在需要时启动（点击抓取新论文按钮时）
        // 不在页面初始化时启动，避免与新闻抓取状态冲突
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
        if (newsStatusPollingInterval) {
            clearInterval(newsStatusPollingInterval);
            newsStatusPollingInterval = null;
        }
        if (refreshStatusInterval) {
            clearInterval(refreshStatusInterval);
            refreshStatusInterval = null;
        }
    });
});

// 设置事件监听器
function setupEventListeners() {
    // 抓取新论文按钮 - 直接执行脚本，不显示模态框
    const fetchBtn = document.getElementById('fetchBtn');
    if (fetchBtn) {
        fetchBtn.addEventListener('click', startFetchPapers);
    }
    
    // 获取新News按钮 - 直接执行脚本
    const fetchNewsBtn = document.getElementById('fetchNewsBtn');
    if (fetchNewsBtn) {
        fetchNewsBtn.addEventListener('click', startFetchNews);
    }
    
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
    
    // 具身岗位机会挂件收起/展开
    const jobsWidgetHeader = document.getElementById('jobsWidgetHeader');
    const jobsWidget = document.querySelector('.jobs-widget');
    if (jobsWidgetHeader && jobsWidget) {
        jobsWidgetHeader.addEventListener('click', (e) => {
            // 如果点击的是链接按钮，不触发收起/展开
            if (e.target.closest('.jobs-header-btn')) {
                return;
            }
            jobsWidget.classList.toggle('collapsed');
            
            // 展开时清除红点提示
            if (!jobsWidget.classList.contains('collapsed')) {
                const updateBadge = document.getElementById('jobsUpdateBadge');
                if (updateBadge) {
                    updateBadge.classList.add('hidden');
                }
            }
        });
    }
    
    // 具身数据集挂件收起/展开
    const datasetsWidgetHeader = document.getElementById('datasetsWidgetHeader');
    const datasetsWidget = document.querySelector('.datasets-widget');
    if (datasetsWidgetHeader && datasetsWidget) {
        datasetsWidgetHeader.addEventListener('click', () => {
            datasetsWidget.classList.toggle('collapsed');
            
            // 展开时清除红点提示
            if (!datasetsWidget.classList.contains('collapsed')) {
                const updateBadge = document.getElementById('datasetsUpdateBadge');
                if (updateBadge) {
                    updateBadge.classList.add('hidden');
                }
            }
        });
    }
    
    // 具身论文数据仪表盘收起/展开
    const dashboardHeader = document.getElementById('dashboardHeader');
    const dashboardSection = document.querySelector('.combined-research-stats');
    const dashboardToggleBtn = document.getElementById('dashboardToggleBtn');
    
    if (dashboardHeader && dashboardSection) {
        // 点击标题区域或按钮都可以切换
        const toggleDashboard = (e) => {
            // 如果点击的是"抓取新论文"按钮，不触发收起/展开
            if (e.target.closest('#fetchBtn') || e.target.closest('.combined-header-actions')) {
                return;
            }
            dashboardSection.classList.toggle('collapsed');
        };
        
        if (dashboardHeader) {
            dashboardHeader.addEventListener('click', toggleDashboard);
        }
        
        // 按钮点击事件（阻止事件冒泡，避免重复触发）
        if (dashboardToggleBtn) {
            dashboardToggleBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                dashboardSection.classList.toggle('collapsed');
            });
        }
    }
    
    // 趋势分析时间选择器
    const trendsTimeBtns = document.querySelectorAll('.trends-time-btn');
    trendsTimeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // 更新按钮状态
            trendsTimeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // 加载对应天数的数据
            const days = parseInt(btn.getAttribute('data-days'));
            loadTrends(days);
        });
    });
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
        // 新规则：不再使用last_viewed参数，后端直接返回今天新创建的论文数量
        const url = '/api/papers';
        
        console.log('请求论文API:', url);
        const response = await fetch(url);
        console.log('论文API响应状态:', response.status, response.statusText);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const result = await response.json();
        console.log('论文API返回数据，success:', result.success, 'data keys:', result.data ? Object.keys(result.data) : 'no data');
        console.log('📊 API返回的完整数据:', JSON.stringify({
            success: result.success,
            new_papers_count: result.new_papers_count,
            has_data: !!result.data
        }));
        
        if (result.success) {
            if (!result.data || typeof result.data !== 'object') {
                throw new Error('返回的数据格式不正确: ' + typeof result.data);
            }
            papersData = result.data;
            console.log('准备渲染论文，数据类别数:', Object.keys(result.data).length);
            
            // 先保存新论文数量，在renderPapers之后使用
            const newPapersCount = result.new_papers_count;
            console.log('🔴 新论文数量（从API获取）:', newPapersCount, '类型:', typeof newPapersCount);
            
            // 渲染论文（这会创建标签页和红点元素）
            renderPapers(result.data);
            
            // 更新最后更新时间
            if (result.last_update) {
                updateLastUpdateTime(result.last_update);
            }
            
            console.log('论文数据加载完成');
            
            // 更新新论文红点提示（在renderPapers之后调用，确保元素已创建）
            // renderPapers是同步的，但为了确保DOM完全更新，延迟一下
            if (showNewBadge) {
                console.log('🔴 showNewBadge=true，准备更新红点');
                console.log('🔴 newPapersCount值:', newPapersCount, 'undefined?', newPapersCount === undefined);
                
                if (newPapersCount !== undefined && newPapersCount !== null) {
                    // 使用requestAnimationFrame确保DOM更新完成
                    requestAnimationFrame(() => {
                        setTimeout(() => {
                            console.log('🔴 准备更新红点，数量:', newPapersCount);
                            updateNewPapersBadge(newPapersCount);
                        }, 100);
                    });
                } else {
                    console.warn('⚠️ newPapersCount是undefined或null，无法更新红点');
                }
            } else {
                console.log('showNewBadge=false，跳过红点更新');
            }
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

// 更新新论文红点提示（新规则：今天看昨天的）
function updateNewPapersBadge(count) {
    console.log('🔴 updateNewPapersBadge 被调用，数量:', count, '类型:', typeof count);
    
    // 确保count是数字
    const numCount = typeof count === 'number' ? count : parseInt(count) || 0;
    console.log('🔴 转换后的数量:', numCount);
    
    // 延迟查找元素，因为红点是在renderPapers()中动态创建的
    // 使用递归重试机制，最多重试10次（总共约1秒）
    let retryCount = 0;
    const maxRetries = 10;
    
    function tryUpdate() {
        const badge = document.getElementById('newPapersBadge');
        const countElement = document.getElementById('newPapersCount');
        
        console.log('🔴 查找红点元素，retry:', retryCount, 'badge存在?', !!badge, 'countElement存在?', !!countElement);
        
        if (badge && countElement) {
            console.log('✅ 找到红点元素，准备更新显示，数量:', numCount);
            updateBadgeDisplay(badge, countElement, numCount);
        } else {
            retryCount++;
            if (retryCount < maxRetries) {
                console.log(`⏳ 红点元素未找到，重试 ${retryCount}/${maxRetries}...`);
                setTimeout(tryUpdate, 100);
            } else {
                console.error('❌ 红点提示元素未找到，已重试', maxRetries, '次');
                console.error('当前DOM中的tabs元素:', document.getElementById('tabs'));
                console.error('当前DOM中的newPapersBadge元素:', document.getElementById('newPapersBadge'));
            }
        }
    }
    
    tryUpdate();
}

// 更新红点显示的辅助函数
function updateBadgeDisplay(badge, countElement, count) {
    console.log('🔴 updateBadgeDisplay 被调用，昨天新论文数量:', count, '类型:', typeof count);
    console.log('🔴 badge元素:', badge);
    console.log('🔴 countElement元素:', countElement);
    console.log('🔴 badge当前classList:', badge.classList.toString());
    console.log('🔴 countElement当前内容:', countElement.textContent);
    
    // 确保count是数字类型
    const numCount = typeof count === 'number' ? count : (parseInt(count) || 0);
    console.log('🔴 转换后的数量:', numCount, '原始值:', count);
    
    // 新规则：今天看昨天的，直接显示后端返回的昨天新论文数量
    if (numCount > 0) {
        const displayCount = numCount > 99 ? '99+' : numCount.toString();
        countElement.textContent = displayCount;
        badge.classList.remove('hidden');
        console.log('✅ 红点提示已显示，数量:', displayCount, '(昨天新论文)');
        console.log('✅ badge当前classList（移除hidden后）:', badge.classList.toString());
    } else {
        badge.classList.add('hidden');
        console.log('ℹ️ 红点提示已隐藏（昨天无新论文），count值:', numCount);
    }
}

// 清除新论文提示（点击红点时调用）
// 新规则：只隐藏红点，不影响计数（因为每天会自动重置）
function clearNewPapersBadge() {
    const badge = document.getElementById('newPapersBadge');
    if (badge) {
        badge.classList.add('hidden');
        console.log('红点提示已清除（手动隐藏，明天如果有新论文会自动显示）');
    }
    // 注意：不再需要更新localStorage，因为新规则不依赖它
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

// 开始抓取新论文（简化版：直接执行脚本，不显示配置模态框）
async function startFetchPapers() {
    const fetchBtn = document.getElementById('fetchBtn');
    if (!fetchBtn) return;
    
    // 检查是否已有任务在运行
    try {
        const statusResponse = await fetch('/api/fetch-status');
        const status = await statusResponse.json();
        if (status.running) {
            alert('抓取任务正在运行中，请稍候...');
            return;
        }
    } catch (error) {
        console.warn('检查任务状态失败:', error);
    }
    
    // 保存原始按钮内容
    const originalBtnContent = fetchBtn.innerHTML;
    const originalDisabled = fetchBtn.disabled;
    
    // 更新按钮状态
    fetchBtn.disabled = true;
    fetchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 抓取中...';
    
    // 显示抓取状态条
    const statusDiv = document.getElementById('fetchStatus');
    statusDiv.classList.remove('hidden');
    updateFetchStatus('正在启动抓取任务...');
    
    // 重置lastFetchUpdate，确保抓取完成后能刷新
    lastFetchUpdate = null;
    
    try {
        console.log('🚀 开始抓取新论文，执行命令: python3 fetch_new_data.py --papers');
        
        // 调用API，不需要传递参数（后端直接执行脚本）
        const response = await fetch('/api/fetch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})  // 不传递任何参数
        });

        const result = await response.json();
        console.log('📊 抓取API响应:', result);
        
        if (result.success) {
            updateFetchStatus('抓取任务已启动，请稍候...');
            console.log('✅ 抓取任务已启动，开始轮询状态...');
            
            // 清除之前的轮询
            if (statusPollingInterval) {
                clearInterval(statusPollingInterval);
            }
            
            // 启动状态轮询
            startStatusPolling();
            
            // 立即检查一次状态（500ms后）
            setTimeout(async () => {
                try {
                    const statusResponse = await fetch('/api/fetch-status');
                    const status = await statusResponse.json();
                    console.log('📊 立即检查状态:', status);
                    
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
                    console.error('❌ 立即检查状态失败:', error);
                }
            }, 500);
        } else {
            // 启动失败
            updateFetchStatus('启动失败: ' + (result.message || '未知错误'));
            fetchBtn.disabled = originalDisabled;
            fetchBtn.innerHTML = originalBtnContent;
            
            setTimeout(() => {
                statusDiv.classList.add('hidden');
            }, 5000);
        }
    } catch (error) {
        console.error('❌ 启动抓取失败:', error);
        updateFetchStatus('启动失败: ' + error.message);
        fetchBtn.disabled = originalDisabled;
        fetchBtn.innerHTML = originalBtnContent;
        
        setTimeout(() => {
            statusDiv.classList.add('hidden');
        }, 5000);
    }
}

// 更新抓取状态
function updateFetchStatus(message) {
    const messageSpan = document.getElementById('statusMessage');
    if (messageSpan) {
        messageSpan.textContent = message;
    }
}

// 开始抓取新News（简化版：直接执行脚本）
async function startFetchNews() {
    const fetchNewsBtn = document.getElementById('fetchNewsBtn');
    if (!fetchNewsBtn) return;
    
    // 检查是否已有任务在运行
    try {
        const statusResponse = await fetch('/api/fetch-news-status');
        const status = await statusResponse.json();
        if (status.running) {
            alert('新闻抓取任务正在运行中，请稍候...');
            return;
        }
    } catch (error) {
        console.warn('检查任务状态失败:', error);
    }
    
    // 保存原始按钮内容
    const originalBtnContent = fetchNewsBtn.innerHTML;
    const originalDisabled = fetchNewsBtn.disabled;
    
    // 更新按钮状态
    fetchNewsBtn.disabled = true;
    fetchNewsBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    
    // 显示抓取状态条（复用论文抓取的状态条）
    const statusDiv = document.getElementById('fetchStatus');
    statusDiv.classList.remove('hidden');
    updateFetchStatus('正在启动新闻抓取任务...');
    
    try {
        console.log('🚀 开始抓取新News，执行命令: python3 fetch_new_data.py --news');
        
        // 调用API，不需要传递参数（后端直接执行脚本）
        const response = await fetch('/api/fetch-news', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})  // 不传递任何参数
        });

        // 检查响应内容类型
        const contentType = response.headers.get('content-type');
        let result;
        
        // 尝试解析JSON响应（即使状态码不是200）
        if (contentType && contentType.includes('application/json')) {
            try {
                const responseText = await response.text();
                result = JSON.parse(responseText);
                console.log('📊 新闻抓取API响应:', result);
            } catch (e) {
                console.error('❌ 解析JSON响应失败:', e);
                throw new Error(`解析服务器响应失败: ${e.message}`);
            }
        } else {
            // 非JSON响应
            const text = await response.text();
            console.error('❌ 服务器返回了非JSON响应:', text.substring(0, 200));
            throw new Error(`服务器返回了非JSON响应（可能是404错误）。请重启Flask服务器。响应内容: ${text.substring(0, 200)}`);
        }
        
        // 检查响应状态和结果
        if (!response.ok) {
            // 如果是400错误且消息是"任务正在运行中"，显示友好提示
            if (response.status === 400 && result.message && result.message.includes('正在运行')) {
                console.log('ℹ️ 新闻抓取任务正在运行中');
                updateFetchStatus(result.message || '新闻抓取任务正在运行中，请稍候...');
                
                // 启动状态轮询以显示当前进度
                startNewsStatusPolling();
                
                // 恢复按钮状态
                fetchNewsBtn.disabled = originalDisabled;
                fetchNewsBtn.innerHTML = originalBtnContent;
                return;
            }
            // 其他错误
            console.error('❌ API响应错误:', response.status, result);
            throw new Error(result.message || `HTTP ${response.status}: 请求失败`);
        }
        
        if (result.success) {
            updateFetchStatus('新闻抓取任务已启动，请稍候...');
            console.log('✅ 新闻抓取任务已启动，开始轮询状态...');
            
            // 启动新闻抓取状态轮询
            startNewsStatusPolling();
            
            // 立即检查一次状态（500ms后）
            setTimeout(async () => {
                try {
                    const statusResponse = await fetch('/api/fetch-news-status');
                    const status = await statusResponse.json();
                    console.log('📊 立即检查新闻抓取状态:', status);
                    
                    const statusDiv = document.getElementById('fetchStatus');
                    const messageSpan = document.getElementById('statusMessage');
                    const progressFill = document.getElementById('progressFill');
                    
                    if (status.running) {
                        statusDiv.classList.remove('hidden');
                        messageSpan.textContent = status.message || '正在抓取新闻...';
                        if (status.total > 0) {
                            const progress = Math.min((status.progress / status.total) * 100, 100);
                            progressFill.style.width = progress + '%';
                        }
                    }
                } catch (error) {
                    console.error('❌ 立即检查状态失败:', error);
                }
            }, 500);
        } else {
            // 启动失败
            updateFetchStatus('启动失败: ' + (result.message || '未知错误'));
            fetchNewsBtn.disabled = originalDisabled;
            fetchNewsBtn.innerHTML = originalBtnContent;
            
            setTimeout(() => {
                statusDiv.classList.add('hidden');
            }, 5000);
        }
    } catch (error) {
        console.error('❌ 启动新闻抓取失败:', error);
        updateFetchStatus('启动失败: ' + error.message);
        fetchNewsBtn.disabled = originalDisabled;
        fetchNewsBtn.innerHTML = originalBtnContent;
        
        setTimeout(() => {
            statusDiv.classList.add('hidden');
        }, 5000);
    }
}

// 轮询新闻抓取状态（只在新闻抓取时启动）
function startNewsStatusPolling() {
    // 清除之前的定时器
    if (newsStatusPollingInterval) {
        clearInterval(newsStatusPollingInterval);
    }
    
    // 同时停止论文抓取状态轮询，避免冲突
    if (statusPollingInterval) {
        clearInterval(statusPollingInterval);
        statusPollingInterval = null;
    }
    
    newsStatusPollingInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/fetch-news-status');
            const status = await response.json();
            
            const statusDiv = document.getElementById('fetchStatus');
            const messageSpan = document.getElementById('statusMessage');
            const progressFill = document.getElementById('progressFill');
            const fetchNewsBtn = document.getElementById('fetchNewsBtn');
            
            // 调试日志
            if (status.running || status.progress > 0) {
                console.log('新闻抓取状态:', status);
            }
            
            if (status.running) {
                statusDiv.classList.remove('hidden');
                messageSpan.textContent = status.message || '正在抓取新闻...';
                
                if (status.total > 0) {
                    const progress = Math.min((status.progress / status.total) * 100, 100);
                    progressFill.style.width = progress + '%';
                } else {
                    progressFill.style.width = '50%';  // 不确定进度时显示50%
                }
            } else {
                // 抓取完成
                if (status.last_update) {
                    // 恢复按钮状态
                    if (fetchNewsBtn) {
                        fetchNewsBtn.disabled = false;
                        fetchNewsBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
                    }
                    
                    // 隐藏状态条并刷新新闻数据
                    setTimeout(() => {
                        statusDiv.classList.add('hidden');
                        loadNews();  // 刷新新闻列表
                    }, 2000);
                } else {
                    // 没有任务运行时，隐藏状态栏
                    statusDiv.classList.add('hidden');
                }
                
                // 停止轮询
                if (newsStatusPollingInterval) {
                    clearInterval(newsStatusPollingInterval);
                    newsStatusPollingInterval = null;
                }
            }
        } catch (error) {
            console.error('获取新闻抓取状态失败:', error);
        }
    }, 2000);  // 每2秒轮询一次
}

// 轮询论文抓取状态（只在论文抓取时启动）
function startStatusPolling() {
    // 清除之前的定时器
    if (statusPollingInterval) {
        clearInterval(statusPollingInterval);
    }
    
    // 同时停止新闻抓取状态轮询，避免冲突
    if (newsStatusPollingInterval) {
        clearInterval(newsStatusPollingInterval);
        newsStatusPollingInterval = null;
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
                console.log('论文抓取状态:', status);
            }
            
            if (status.running) {
                statusDiv.classList.remove('hidden');
                // 显示当前抓取的关键词和进度
                let displayMessage = status.message || '正在抓取论文...';
                if (status.current_keyword) {
                    displayMessage = `正在抓取 ${status.current_keyword}...`;
                }
                messageSpan.textContent = displayMessage;
                
                if (status.total > 0) {
                    const progress = Math.min((status.progress / status.total) * 100, 100);
                    progressFill.style.width = progress + '%';
                    console.log(`📊 抓取进度: ${status.progress}/${status.total} (${progress.toFixed(1)}%) - ${displayMessage}`);
                } else {
                    // 如果total还没设置，显示不确定进度
                    progressFill.style.width = '10%';
                    console.log('⏳ 等待抓取任务启动...');
                }
            } else {
                // 只在抓取刚完成时刷新一次（避免重复刷新）
                if (status.last_update && status.last_update !== lastFetchUpdate) {
                    lastFetchUpdate = status.last_update;
                    // 抓取完成，刷新数据
                    setTimeout(() => {
                        statusDiv.classList.add('hidden');
                        // 强制刷新统计、论文数据和趋势图（显示新论文提示）
                        loadStats();
                        loadPapers(true); // 传入true以显示新论文提示
                        loadCategories(); // 重新加载类别筛选器
                        loadTrends(currentTrendDays); // 刷新趋势图
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

// 已移除模态框相关代码

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
            
            // 检查是否有今天的新更新，显示红点提示
            const updateBadge = document.getElementById('jobsUpdateBadge');
            if (updateBadge) {
                if (result.has_new_today) {
                    updateBadge.classList.remove('hidden');
                } else {
                    updateBadge.classList.add('hidden');
                }
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
            
            // 检查是否有今天的新更新，显示红点提示
            const updateBadge = document.getElementById('datasetsUpdateBadge');
            if (updateBadge) {
                if (result.has_new_today) {
                    updateBadge.classList.remove('hidden');
                } else {
                    updateBadge.classList.add('hidden');
                }
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

// 初始化B站展开/收起功能
function initBilibiliToggle() {
    const toggleBtn = document.getElementById('bilibiliToggleBtn');
    const widget = document.querySelector('.bilibili-widget');
    
    if (toggleBtn && widget) {
        toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            widget.classList.toggle('collapsed');
            const icon = toggleBtn.querySelector('i');
            if (icon) {
                if (widget.classList.contains('collapsed')) {
                    icon.classList.remove('fa-chevron-up');
                    icon.classList.add('fa-chevron-down');
                } else {
                    icon.classList.remove('fa-chevron-down');
                    icon.classList.add('fa-chevron-up');
                }
            }
        });
    }
}

// 加载Bilibili数据
async function loadBilibili() {
    const container = document.getElementById('bilibiliContainer');
    
    if (!container) {
        console.warn('loadBilibili: 找不到bilibiliContainer元素，跳过加载');
        return;
    }
    
    try {
        console.log('loadBilibili: 开始调用 /api/bilibili API...');
        const response = await fetch('/api/bilibili');
        console.log('loadBilibili: API响应状态:', response.status, response.statusText);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (result.success && result.data) {
            const data = result.data;
            const videos = data.videos || [];
            
            // 构建HTML
            let html = '';
            
            // 检查是否有错误标记
            if (data.error) {
                html += `
                    <div class="bilibili-error-message" style="padding: 12px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; margin-bottom: 12px;">
                        <p style="margin: 0; color: #856404; font-size: 0.875rem;">
                            <i class="fas fa-info-circle"></i> ${data.error_message || 'Bilibili API暂时无法访问，请稍后刷新页面重试'}
                        </p>
                    </div>
                `;
            }
            
            // 视频列表 - 按日期从新到旧排序
            if (videos.length > 0) {
                // 确保按日期从新到旧排序（使用pubdate_raw时间戳）
                const sortedVideos = [...videos].sort((a, b) => {
                    const timeA = a.pubdate_raw || 0;
                    const timeB = b.pubdate_raw || 0;
                    return timeB - timeA; // 从新到旧
                });
                
                html += '<div class="bilibili-video-list">';
                sortedVideos.forEach(video => {
                    html += `
                        <a href="${video.url}" target="_blank" class="bilibili-video-item">
                            <div class="bilibili-video-info">
                                <h5 class="bilibili-video-title">${video.title || '无标题'}</h5>
                                <div class="bilibili-video-meta">
                                    <span><i class="fas fa-clock"></i> ${video.pubdate || ''}</span>
                                    <span><i class="fas fa-play"></i> ${video.play || '0'}</span>
                                    <span><i class="fas fa-comment"></i> ${video.video_review || '0'}</span>
                                    <span><i class="fas fa-star"></i> ${video.favorites || '0'}</span>
                                </div>
                            </div>
                        </a>
                    `;
                });
                html += '</div>';
            } else if (!data.error) {
                html += '<div class="loading-spinner-small"><p>暂无视频信息</p></div>';
            } else {
                html += '<div class="loading-spinner-small"><p>无法加载视频列表</p></div>';
            }
            
            container.innerHTML = html;
        } else {
            throw new Error(result.error || '获取Bilibili数据失败');
        }
    } catch (error) {
        console.error('loadBilibili: 加载失败:', error);
        const container = document.getElementById('bilibiliContainer');
        if (container) {
            container.innerHTML = `
                <div class="loading-spinner-small">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>加载Bilibili信息失败: ${error.message}</p>
                </div>
            `;
        }
    }
}

// 加载论文趋势分析数据
async function loadTrends(days = 30) {
    const container = document.getElementById('trendsContainer');
    
    if (!container) {
        console.warn('loadTrends: 找不到trendsContainer元素，跳过加载');
        return;
    }
    
    // 显示加载状态
    container.innerHTML = `
        <div class="loading-spinner-small">
            <i class="fas fa-spinner fa-spin"></i>
                        <p>加载活跃度数据中...</p>
        </div>
    `;
    
    try {
        // 如果是7天，需要请求14天数据来计算环比
        // 如果是30天，需要请求60天数据来计算环比
        const apiDays = days === 7 ? 14 : (days === 30 ? 60 : days);
        console.log(`loadTrends: 开始调用 /api/trends API (${apiDays}天，用于${days}天分析)...`);
        const response = await fetch(`/api/trends?days=${apiDays}`);
        console.log('loadTrends: API响应状态:', response.status, response.statusText);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('loadTrends: API错误响应:', errorText);
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('loadTrends: API返回数据:', result);
        
        if (result.success && result.trends) {
            const trendsCount = Object.keys(result.trends).length;
            console.log(`loadTrends: 获取到 ${trendsCount} 个类别的趋势数据`);
            
            if (trendsCount === 0) {
                container.innerHTML = `
                    <div class="loading-spinner-small">
                        <i class="fas fa-info-circle"></i>
                        <p>暂无趋势数据，请先抓取论文数据</p>
                    </div>
                `;
                return;
            }
            
            currentTrendDays = days;
            // 如果是7天，需要传递实际请求的天数（14天）给渲染函数，以便正确计算环比
            // 如果是30天，需要传递实际请求的天数（60天）给渲染函数，以便正确计算环比
            const actualDays = days === 7 ? 14 : (days === 30 ? 60 : days);
            renderTrendsChart(result.trends, result.growth, result.start_date, result.end_date, actualDays);
        } else {
            throw new Error(result.error || '获取趋势数据失败');
        }
    } catch (error) {
        console.error('loadTrends: 加载失败:', error);
        const container = document.getElementById('trendsContainer');
        if (container) {
            container.innerHTML = `
                <div class="loading-spinner-small" style="padding: 20px; text-align: center;">
                    <i class="fas fa-exclamation-triangle" style="color: #ef4444; font-size: 1.5rem; margin-bottom: 10px;"></i>
                    <p style="color: #64748b; margin: 0;">加载趋势数据失败</p>
                    <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 5px;">${error.message}</p>
                </div>
            `;
        }
    }
}

// 渲染趋势图表
function renderTrendsChart(trendsData, growthData, startDate, endDate, actualDays = null) {
    const container = document.getElementById('trendsContainer');
    if (!container) {
        console.error('renderTrendsChart: 找不到trendsContainer元素');
        return;
    }
    
    // 准备图表数据
    const categories = Object.keys(trendsData).sort();
    console.log('renderTrendsChart: 类别数量:', categories.length, '类别列表:', categories);
    
    if (categories.length === 0) {
        container.innerHTML = `
            <div class="loading-spinner-small" style="padding: 20px; text-align: center;">
                <i class="fas fa-info-circle" style="color: #64748b; font-size: 1.5rem; margin-bottom: 10px;"></i>
                <p style="color: #64748b; margin: 0;">暂无趋势数据</p>
            </div>
        `;
        return;
    }
    
    // 检查Chart.js是否加载
    if (typeof Chart === 'undefined') {
        console.error('renderTrendsChart: Chart.js未加载');
        container.innerHTML = `
            <div class="loading-spinner-small" style="padding: 20px; text-align: center;">
                <i class="fas fa-exclamation-triangle" style="color: #ef4444; font-size: 1.5rem; margin-bottom: 10px;"></i>
                <p style="color: #64748b; margin: 0;">Chart.js库未加载，请刷新页面重试</p>
            </div>
        `;
        return;
    }
    
    // 计算活跃量分析（上涨/下滑）
    const activityAnalysis = {};
    categories.forEach(category => {
        const data = trendsData[category];
        const counts = data.counts || [];
        const dates = data.dates || [];
        
        if (counts.length === 0) {
            activityAnalysis[category] = {
                current: 0,
                previous: 0,
                change: 0,
                changePercent: 0,
                trend: 'neutral'
            };
            return;
        }
        
        // 计算当前周期和上一个周期的活跃量
        let currentPeriod = 0;
        let previousPeriod = 0;
        
        if (currentTrendDays === 7) {
            // 7天：最近7天 vs 前一个7天（环比）
            // 需要14天的数据来计算环比，如果数据不足14天，则用已有数据计算
            if (counts.length >= 14) {
                // 最近7天 vs 前一个7天
                const recentCount = counts.slice(-7).reduce((a, b) => a + b, 0);
                const previousCount = counts.slice(-14, -7).reduce((a, b) => a + b, 0);
                currentPeriod = recentCount;
                previousPeriod = previousCount;
            } else if (counts.length >= 7) {
                // 数据不足14天，用最近7天 vs 前7天（如果存在）
                const recentCount = counts.slice(-7).reduce((a, b) => a + b, 0);
                const previousCount = counts.slice(0, Math.min(7, counts.length - 7)).reduce((a, b) => a + b, 0);
                currentPeriod = recentCount;
                previousPeriod = previousCount;
            } else {
                // 数据不足7天，无法计算环比
                const recentCount = counts.reduce((a, b) => a + b, 0);
                currentPeriod = recentCount;
                previousPeriod = 0;
            }
        } else {
            // 30天：最近30天 vs 前一个30天（环比）
            // 需要60天的数据来计算环比，如果数据不足60天，则用已有数据计算
            if (counts.length >= 60) {
                // 最近30天 vs 前一个30天
                const recentCount = counts.slice(-30).reduce((a, b) => a + b, 0);
                const previousCount = counts.slice(-60, -30).reduce((a, b) => a + b, 0);
                currentPeriod = recentCount;
                previousPeriod = previousCount;
            } else if (counts.length >= 30) {
                // 数据不足60天，用最近30天 vs 前30天（如果存在）
                const recentCount = counts.slice(-30).reduce((a, b) => a + b, 0);
                const previousCount = counts.slice(0, Math.min(30, counts.length - 30)).reduce((a, b) => a + b, 0);
                currentPeriod = recentCount;
                previousPeriod = previousCount;
            } else {
                // 数据不足30天，无法计算环比
                const recentCount = counts.reduce((a, b) => a + b, 0);
                currentPeriod = recentCount;
                previousPeriod = 0;
            }
        }
        
        const change = currentPeriod - previousPeriod;
        const changePercent = previousPeriod > 0 ? ((change / previousPeriod) * 100) : (currentPeriod > 0 ? 100 : 0);
        
        activityAnalysis[category] = {
            current: currentPeriod,
            previous: previousPeriod,
            change: change,
            changePercent: changePercent,
            trend: change > 0 ? 'up' : (change < 0 ? 'down' : 'neutral')
        };
    });
    
    // 处理数据：7天显示最近7天，30天按周统计
    let processedTrendsData = trendsData;
    let processedDates = [];
    if (categories.length > 0 && trendsData[categories[0]]) {
        processedDates = trendsData[categories[0]].dates || [];
    }
    
    // 如果是7天，只显示最近7天的数据（用于图表显示）
    if (currentTrendDays === 7 && actualDays && actualDays === 14) {
        processedTrendsData = {};
        categories.forEach(category => {
            const data = trendsData[category];
            const counts = data.counts || [];
            const dates = data.dates || [];
            
            // 只取最近7天
            processedTrendsData[category] = {
                dates: dates.slice(-7),
                counts: counts.slice(-7),
                total: counts.slice(-7).reduce((a, b) => a + b, 0)
            };
        });
        if (categories.length > 0 && processedTrendsData[categories[0]]) {
            processedDates = processedTrendsData[categories[0]].dates || [];
        }
    }
    
    // 如果是30天，只显示最近30天的数据（用于图表显示）
    if (currentTrendDays === 30 && actualDays && actualDays === 60) {
        processedTrendsData = {};
        categories.forEach(category => {
            const data = trendsData[category];
            const counts = data.counts || [];
            const dates = data.dates || [];
            
            // 只取最近30天
            processedTrendsData[category] = {
                dates: dates.slice(-30),
                counts: counts.slice(-30),
                total: counts.slice(-30).reduce((a, b) => a + b, 0)
            };
        });
        if (categories.length > 0 && processedTrendsData[categories[0]]) {
            processedDates = processedTrendsData[categories[0]].dates || [];
        }
    }
    
    // 处理30天数据：按周统计
    if (currentTrendDays === 30) {
        processedTrendsData = {};
        let weeklyLabels = []; // 在外部定义，用于存储日期标签
        
        // 先使用第一个类别生成日期标签（所有类别应该使用相同的日期）
        if (categories.length > 0 && trendsData[categories[0]]) {
            const firstData = trendsData[categories[0]];
            const firstDates = firstData.dates || [];
            const weekSize = 7;
            
            for (let i = 0; i < firstDates.length; i += weekSize) {
                if (firstDates[i]) {
                    const d = new Date(firstDates[i]);
                    weeklyLabels.push(`${d.getMonth() + 1}/${d.getDate()}`);
                }
            }
        }
        
        // 为每个类别生成周统计数据
        categories.forEach(category => {
            const data = trendsData[category];
            const counts = data.counts || [];
            
            // 按周分组统计
            const weeklyData = [];
            const weekSize = 7;
            
            for (let i = 0; i < counts.length; i += weekSize) {
                const weekCounts = counts.slice(i, i + weekSize);
                const weekTotal = weekCounts.reduce((a, b) => a + b, 0);
                weeklyData.push(weekTotal);
            }
            
            processedTrendsData[category] = {
                dates: weeklyLabels,
                counts: weeklyData,
                total: data.total
            };
        });
        
        if (weeklyLabels.length > 0) {
            processedDates = weeklyLabels;
        }
    }
    
    // 生成日期标签
    let dateLabels = [];
    if (categories.length > 0 && processedTrendsData[categories[0]]) {
        const firstCategory = processedTrendsData[categories[0]];
        dateLabels = firstCategory.dates || [];
    }
    
    if (dateLabels.length === 0) {
        console.warn('renderTrendsChart: 没有日期标签数据');
        container.innerHTML = `
            <div class="loading-spinner-small" style="padding: 20px; text-align: center;">
                <i class="fas fa-info-circle" style="color: #64748b; font-size: 1.5rem; margin-bottom: 10px;"></i>
                <p style="color: #64748b; margin: 0;">暂无日期数据</p>
            </div>
        `;
        return;
    }
    
    console.log('renderTrendsChart: 日期标签数量:', dateLabels.length);
    
    // 为每个研究方向分配不同的颜色（确保不同方向有明显区别）
    const categoryColors = [
        { border: 'rgba(59, 130, 246, 0.9)', fill: 'rgba(59, 130, 246, 0.1)' },      // 蓝色
        { border: 'rgba(16, 185, 129, 0.9)', fill: 'rgba(16, 185, 129, 0.1)' },      // 绿色
        { border: 'rgba(239, 68, 68, 0.9)', fill: 'rgba(239, 68, 68, 0.1)' },        // 红色
        { border: 'rgba(245, 158, 11, 0.9)', fill: 'rgba(245, 158, 11, 0.1)' },      // 橙色
        { border: 'rgba(139, 92, 246, 0.9)', fill: 'rgba(139, 92, 246, 0.1)' },      // 紫色
        { border: 'rgba(236, 72, 153, 0.9)', fill: 'rgba(236, 72, 153, 0.1)' },     // 粉色
        { border: 'rgba(14, 165, 233, 0.9)', fill: 'rgba(14, 165, 233, 0.1)' },      // 天蓝色
        { border: 'rgba(34, 197, 94, 0.9)', fill: 'rgba(34, 197, 94, 0.1)' },        // 青绿色
        { border: 'rgba(251, 146, 60, 0.9)', fill: 'rgba(251, 146, 60, 0.1)' },      // 橙红色
        { border: 'rgba(168, 85, 247, 0.9)', fill: 'rgba(168, 85, 247, 0.1)' },      // 紫罗兰
    ];
    
    // 准备数据集（每个研究方向使用不同颜色）
    const datasets = categories.map((category, index) => {
        const categoryData = processedTrendsData[category];
        if (!categoryData) {
            console.warn(`renderTrendsChart: 类别 ${category} 没有数据`);
            return null;
        }
        const data = categoryData.counts || [];
        
        // 为每个类别分配颜色（循环使用颜色数组）
        const colorIndex = index % categoryColors.length;
        const colors = categoryColors[colorIndex];
        
        return {
            label: category,
            data: data,
            borderColor: colors.border,
            backgroundColor: colors.fill,
            borderWidth: 2.5,
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: colors.border,
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2.5,
        };
    }).filter(dataset => dataset !== null); // 过滤掉null值
    
    // 创建活跃量分析卡片（股票风格）
    const activityCardsHtml = `
        <div class="trends-activity-cards">
            ${categories.map(category => {
                const analysis = activityAnalysis[category];
                if (!analysis) {
                    console.warn(`renderTrendsChart: 类别 ${category} 没有分析数据`);
                    return '';
                }
                const trendClass = analysis.trend || 'neutral';
                const trendIcon = analysis.trend === 'up' ? 'fa-arrow-up' : (analysis.trend === 'down' ? 'fa-arrow-down' : 'fa-minus');
                
                return `
                    <div class="trends-activity-card ${trendClass}">
                        <div class="activity-card-header">
                            <span class="activity-category">${category}</span>
                            <span class="activity-trend ${trendClass}">
                                <i class="fas ${trendIcon}"></i>
                            </span>
                        </div>
                        <div class="activity-card-body">
                            <div class="activity-value">${analysis.current || 0}</div>
                            <div class="activity-change ${trendClass}">
                                ${analysis.change > 0 ? '+' : ''}${analysis.change || 0} 
                                (${analysis.changePercent > 0 ? '+' : ''}${(analysis.changePercent || 0).toFixed(1)}%)
                            </div>
                        </div>
                    </div>
                `;
            }).filter(html => html !== '').join('')}
        </div>
    `;
    
    // 创建图表容器
    const chartHtml = `
        ${activityCardsHtml}
        <div class="trends-chart-container">
            <canvas id="trendsChart"></canvas>
        </div>
    `;
    
    container.innerHTML = chartHtml;
    
    // 等待DOM更新
    setTimeout(() => {
        // 销毁旧图表
        if (trendsChart) {
            try {
                trendsChart.destroy();
            } catch (e) {
                console.warn('销毁旧图表时出错:', e);
            }
            trendsChart = null;
        }
        
        // 创建新图表（股票风格）
        const ctx = document.getElementById('trendsChart');
        if (ctx && typeof Chart !== 'undefined') {
            trendsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dateLabels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            boxWidth: 14,
                            padding: 12,
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            usePointStyle: true,
                            color: '#374151'
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(17, 24, 39, 0.95)',
                        padding: 14,
                        titleFont: {
                            size: 13,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 12,
                            weight: '500'
                        },
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            title: function(context) {
                                if (context && context.length > 0 && context[0]) {
                                    if (currentTrendDays === 30) {
                                        return `第${context[0].dataIndex + 1}周`;
                                    }
                                    const index = context[0].dataIndex;
                                    if (processedDates && processedDates[index]) {
                                        return processedDates[index];
                                    }
                                    if (dateLabels && dateLabels[index]) {
                                        return dateLabels[index];
                                    }
                                }
                                return '';
                            },
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y} 篇`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1,
                            precision: 0,
                            font: {
                                size: 11,
                                weight: '500'
                            },
                            color: '#6b7280',
                            padding: 8
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.06)',
                            drawBorder: false,
                            lineWidth: 1
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 0,
                            font: {
                                size: 11,
                                weight: '500'
                            },
                            color: '#6b7280',
                            padding: 8
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
            });
            console.log('renderTrendsChart: 图表创建成功');
        } else {
            console.error('renderTrendsChart: Chart.js未加载或canvas元素不存在');
            if (!ctx) {
                container.innerHTML = `
                    <div class="loading-spinner-small" style="padding: 20px; text-align: center;">
                        <i class="fas fa-exclamation-triangle" style="color: #ef4444; font-size: 1.5rem; margin-bottom: 10px;"></i>
                        <p style="color: #64748b; margin: 0;">无法创建图表：canvas元素不存在</p>
                    </div>
                `;
            } else if (typeof Chart === 'undefined') {
                container.innerHTML = `
                    <div class="loading-spinner-small" style="padding: 20px; text-align: center;">
                        <i class="fas fa-exclamation-triangle" style="color: #ef4444; font-size: 1.5rem; margin-bottom: 10px;"></i>
                        <p style="color: #64748b; margin: 0;">Chart.js库未加载，请刷新页面重试</p>
                    </div>
                `;
            }
        }
    }, 100); // 延迟100ms确保DOM更新完成
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

// refreshStatusInterval 已在文件顶部声明，用于其他功能

// 已删除 refreshAllData 函数（刷新全局数据按钮已移除）

// ==================== 具身赛博🙏拜一拜功能 ====================

// 初始化拜一拜挂件
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
    let currentCategory = localStorage.getItem('fortuneCategory') || 'coding';
    
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
    
    // 绑定佛像点击事件（佛像本身可点击）
    const tubeMain = document.getElementById('fortuneTubeMain');
    if (tubeMain) {
        tubeMain.addEventListener('click', function() {
            // 检查今天是否已经拜过（同一方向）
            const today = new Date().toDateString();
            const savedDate = localStorage.getItem('fortuneDate');
            const savedCategory = localStorage.getItem('fortuneCategory');
            
            if (savedDate === today && savedCategory === currentCategory) {
                // 今天已经拜过这个方向，显示结果
                const savedMessage = localStorage.getItem('fortuneMessage');
                const savedTimestamp = localStorage.getItem('fortuneTimestamp');
                if (savedMessage) {
                    showFortuneResult(savedMessage, savedTimestamp);
                    return;
                }
            }
            
            // 拜一拜
            drawFortune(currentCategory);
        });
    }
    
    // 保留拜拜按钮事件（虽然隐藏了，但保留逻辑）
    const shakeBtn = document.getElementById('fortuneShakeBtn');
    if (shakeBtn) {
        shakeBtn.addEventListener('click', function() {
            // 检查今天是否已经拜过（同一方向）
            const today = new Date().toDateString();
            const savedDate = localStorage.getItem('fortuneDate');
            const savedCategory = localStorage.getItem('fortuneCategory');
            
            if (savedDate === today && savedCategory === currentCategory) {
                // 今天已经拜过这个方向，显示结果
                const savedMessage = localStorage.getItem('fortuneMessage');
                const savedTimestamp = localStorage.getItem('fortuneTimestamp');
                if (savedMessage) {
                    showFortuneResult(savedMessage, savedTimestamp);
                    return;
                }
            }
            
            // 拜一拜
            drawFortune(currentCategory);
        });
    }
    
    // 初始化香火烟雾显示
    initIncenseSmoke();
    
    // 检查今天是否已经拜过
    checkTodayFortune();
}

// 初始化香火烟雾显示
function initIncenseSmoke() {
    const incenseSmoke = document.getElementById('incenseSmoke');
    if (!incenseSmoke) return;
    
    // 创建多个烟雾粒子，营造香火缭绕的感觉
    incenseSmoke.innerHTML = '';
    for (let i = 0; i < 3; i++) {
        const smoke = document.createElement('div');
        smoke.className = 'smoke-particle';
        smoke.style.left = (40 + Math.random() * 20) + '%';
        smoke.style.animationDelay = (i * 0.5) + 's';
        incenseSmoke.appendChild(smoke);
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

// 检查今天是否已经拜过
function checkTodayFortune() {
    const today = new Date().toDateString();
    const savedDate = localStorage.getItem('fortuneDate');
    const savedMessage = localStorage.getItem('fortuneMessage');
    const savedTimestamp = localStorage.getItem('fortuneTimestamp');
    const savedCategory = localStorage.getItem('fortuneCategory');
    
    if (savedDate === today && savedMessage && savedCategory) {
        // 今天已经拜过，显示结果
        showFortuneResult(savedMessage, savedTimestamp);
        
        // 更新标签状态
        updateCategoryTagStates(savedCategory);
    } else {
        // 今天没有拜过，重置状态
        resetFortuneWidget();
    }
}

// 重置拜一拜状态
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
        tubeMain.classList.remove('bowing');
    }
}

// 清除拜拜记录（用于调试或重置）
function clearFortuneRecord() {
    localStorage.removeItem('fortuneDate');
    localStorage.removeItem('fortuneMessage');
    localStorage.removeItem('fortuneTimestamp');
    localStorage.removeItem('fortuneCategory');
    // 清除所有类别的已使用祝福语记录
    localStorage.removeItem('fortuneUsed_coding');
    localStorage.removeItem('fortuneUsed_hardware');
    localStorage.removeItem('fortuneUsed_paper');
    resetFortuneWidget();
    console.log('拜拜记录已清除');
    // 刷新页面以重置状态
    location.reload();
}

// 拜一拜主函数
function drawFortune(category) {
    const tubeMain = document.getElementById('fortuneTubeMain');
    const shakeBtn = document.getElementById('fortuneShakeBtn');
    const flyingStick = document.getElementById('fortuneStickFlying');
    const fortuneResult = document.getElementById('fortuneResult');
    
    if (!tubeMain || !shakeBtn) {
        return;
    }
    
    // 禁用佛像点击（通过添加禁用类）
    if (tubeMain) {
        tubeMain.style.pointerEvents = 'none';
        tubeMain.style.opacity = '0.8';
    }
    
    // 禁用拜拜按钮（虽然隐藏了，但保留逻辑）
    if (shakeBtn) {
        shakeBtn.disabled = true;
    }
    
    // 隐藏之前的结果和飞出的赐福
    if (fortuneResult) {
        fortuneResult.classList.add('hidden');
    }
    if (flyingStick) {
        flyingStick.classList.remove('show', 'fly-out', 'expand');
    }
    
    // 开始拜拜动画（佛像点头）
    if (tubeMain) {
        tubeMain.classList.add('bowing');
    }
    
    // 拜拜动画持续2秒
    setTimeout(() => {
        // 停止拜拜动画
        tubeMain.classList.remove('bowing');
        
        // 获取随机赐福词条
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
        
        // 注意：已使用的祝福语索引已在getRandomFortune中保存
        
        // 赐福从佛像中飞出
        if (flyingStick) {
            const stickContent = document.getElementById('fortuneStickContent');
            if (stickContent) {
                stickContent.textContent = message;
            }
            
            // 计算佛像的位置，让赐福从佛像的位置飞出
            const tubeRect = tubeMain.getBoundingClientRect();
            const containerRect = document.getElementById('fortuneContainer').getBoundingClientRect();
            const tubeCenterX = tubeRect.left + tubeRect.width / 2 - containerRect.left;
            const tubeCenterY = tubeRect.top + tubeRect.height / 2 - containerRect.top;
            
            // 设置飞出赐福的初始位置（佛像的中心，相对于容器）
            flyingStick.style.position = 'absolute';
            flyingStick.style.left = tubeCenterX + 'px';
            flyingStick.style.top = tubeCenterY + 'px';
            flyingStick.style.transform = 'translate(-50%, -50%)';
            
            // 显示飞出的赐福
            flyingStick.classList.add('show');
            flyingStick.style.visibility = 'visible';
            flyingStick.style.opacity = '1';
            
            // 飞出动画
            setTimeout(() => {
                flyingStick.classList.add('fly-out');
                
                // 展开动画
                setTimeout(() => {
                    flyingStick.classList.add('expand');
                    
                    // 显示结果覆盖层（同时隐藏飞出的签）
                    setTimeout(() => {
                        // 先隐藏飞出的签
                        if (flyingStick) {
                            flyingStick.classList.remove('show', 'fly-out', 'expand');
                            flyingStick.style.opacity = '0';
                            flyingStick.style.visibility = 'hidden';
                        }
                        if (fortuneStickContent) {
                            fortuneStickContent.textContent = '';
                        }
                        
                        // 显示结果
                        showFortuneResult(message, timestamp);
                        
                        // 隐藏佛像
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

// 获取随机赐福词条（根据研究方向过滤，确保不重复）
function getRandomFortune(category) {
    // 使用新的BLESSING_MESSAGES结构
    if (typeof BLESSING_MESSAGES === 'undefined' || !BLESSING_MESSAGES) {
        return '佛祖满意：\'今日你的具身智能研究将获得突破性进展！\'';
    }
    
    const selectedCategory = category || 'coding';
    
    // 根据方向获取祝福语
    let filteredMessages = BLESSING_MESSAGES[selectedCategory] || [];
    
    // 如果该方向没有消息，使用coding方向的消息
    if (filteredMessages.length === 0) {
        filteredMessages = BLESSING_MESSAGES.coding || [];
    }
    
    // 如果还是没有消息，返回默认消息
    if (filteredMessages.length === 0) {
        return '佛祖满意：\'今日你的具身智能研究将获得突破性进展！\'';
    }
    
    // 获取已使用的祝福语索引（按类别存储）
    const usedKey = `fortuneUsed_${selectedCategory}`;
    let usedIndices = [];
    try {
        const usedData = localStorage.getItem(usedKey);
        if (usedData) {
            usedIndices = JSON.parse(usedData);
        }
    } catch (e) {
        console.warn('读取已使用祝福语失败:', e);
        usedIndices = [];
    }
    
    // 如果所有祝福语都已使用过，重置记录
    if (usedIndices.length >= filteredMessages.length) {
        usedIndices = [];
        localStorage.setItem(usedKey, JSON.stringify(usedIndices));
    }
    
    // 获取未使用的索引
    const availableIndices = [];
    for (let i = 0; i < filteredMessages.length; i++) {
        if (!usedIndices.includes(i)) {
            availableIndices.push(i);
        }
    }
    
    // 从可用索引中随机选择一个
    let index;
    if (availableIndices.length > 0) {
        // 使用多个随机源确保真正的随机性
        const timestamp = Date.now();
        const randomComponent1 = Math.random() * 1000000;
        const randomComponent2 = Math.random() * 1000000;
        const categoryHash = selectedCategory.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
        
        // 组合多个随机源
        const combinedRandom = (timestamp + randomComponent1 + randomComponent2 + categoryHash + Math.random() * 1000000) % 2147483647;
        
        // 使用线性同余生成器增强随机性
        let random = combinedRandom;
        for (let i = 0; i < 7; i++) {
            random = (random * 1103515245 + 12345) & 0x7fffffff;
            random = (random + Math.floor(Math.random() * 1000)) % 2147483647;
        }
        
        // 最终随机数
        const finalRandom = Math.random() * 0.5 + (random / 0x7fffffff) * 0.5;
        const availableIndex = Math.floor(finalRandom * availableIndices.length);
        index = availableIndices[availableIndex];
    } else {
        // 如果所有都用过了（理论上不会发生），随机选择一个
        index = Math.floor(Math.random() * filteredMessages.length);
    }
    
    // 记录已使用的索引
    usedIndices.push(index);
    try {
        localStorage.setItem(usedKey, JSON.stringify(usedIndices));
    } catch (e) {
        console.warn('保存已使用祝福语失败:', e);
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

// 显示拜拜结果
function showFortuneResult(message, timestamp) {
    const fortuneResult = document.getElementById('fortuneResult');
    const fortuneMessage = document.getElementById('fortuneMessage');
    const fortuneTimestamp = document.getElementById('fortuneTimestamp');
    const flyingStick = document.getElementById('fortuneStickFlying');
    const fortuneStickContent = document.getElementById('fortuneStickContent');
    
    if (!fortuneResult || !fortuneMessage) {
        return;
    }
    
    // 清除飞出的签内容，避免重复显示
    if (flyingStick) {
        flyingStick.classList.remove('show', 'fly-out', 'expand');
        flyingStick.style.opacity = '0';
    }
    if (fortuneStickContent) {
        fortuneStickContent.textContent = '';
    }
    
    // 设置结果消息（确保只显示一次）
    fortuneMessage.textContent = message;
    
    if (fortuneTimestamp) {
        fortuneTimestamp.textContent = `拜拜时间：${timestamp}`;
    }
    
    // 显示结果覆盖层
    fortuneResult.classList.remove('hidden');
}

