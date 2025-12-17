/**
 * 管理仪表盘逻辑
 */

// 全局变量
const token = localStorage.getItem('auth_token');
let overviewStats = null;
let trendsStats = null;

// 检查登录状态
if (!token) {
    window.location.href = '/admin/login';
}

// DOM元素
const adminUserName = document.getElementById('admin-user-name');
const logoutBtn = document.getElementById('logout-btn');
const toast = document.getElementById('toast');

// 加载统计概览
async function loadOverviewStats() {
    try {
        const response = await fetch('/api/admin/stats/overview', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('auth_token');
                window.location.href = '/admin/login';
                return;
            }
            throw new Error('获取统计数据失败');
        }
        
        const data = await response.json();
        if (data.success) {
            overviewStats = data.stats;
            displayOverviewStats(data.stats);
        } else {
            showToast('获取统计数据失败: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('加载统计数据失败:', error);
        showToast('加载统计数据失败', 'error');
    }
}

// 显示统计概览
function displayOverviewStats(stats) {
    document.getElementById('stat-total-users').textContent = stats.users.total || 0;
    document.getElementById('stat-new-users-today').textContent = stats.users.new_today || 0;
    document.getElementById('stat-active-users').textContent = stats.users.active || 0;
    document.getElementById('stat-active-users-today').textContent = stats.active_users.today || 0;
    document.getElementById('stat-total-logins').textContent = stats.logins.total || 0;
    document.getElementById('stat-logins-today').textContent = stats.logins.today || 0;
    document.getElementById('stat-total-access').textContent = stats.access.total || 0;
    document.getElementById('stat-access-today').textContent = stats.access.today || 0;
}

// 加载趋势统计
async function loadTrendsStats(days = 30) {
    try {
        const response = await fetch(`/api/admin/stats/trends?days=${days}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        if (data.success) {
            trendsStats = data.trends;
            renderCharts(data.trends, data.period);
            if (overviewStats && overviewStats.distribution) {
                renderDistributionCharts(overviewStats.distribution);
            }
        } else {
            showToast('获取趋势数据失败', 'error');
        }
    } catch (error) {
        console.error('加载趋势数据失败:', error);
        showToast('加载趋势数据失败', 'error');
    }
}

// 渲染图表
function renderCharts(trends, period) {
    // 准备日期标签
    const dates = generateDateRange(period.start_date, period.end_date);
    
    // 用户增长趋势
    const newUsersData = dates.map(date => trends.new_users[date] || 0);
    const activeUsersData = dates.map(date => trends.active_users[date] || 0);
    
    const usersCtx = document.getElementById('usersChart');
    if (usersCtx) {
        new Chart(usersCtx, {
            type: 'line',
            data: {
                labels: dates.map(d => formatDate(d)),
                datasets: [
                    {
                        label: '新增用户',
                        data: newUsersData,
                        borderColor: 'rgb(102, 126, 234)',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: '活跃用户',
                        data: activeUsersData,
                        borderColor: 'rgb(52, 168, 83)',
                        backgroundColor: 'rgba(52, 168, 83, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }
    
    // 登录活跃度
    const loginsData = dates.map(date => trends.logins[date] || 0);
    const accessData = dates.map(date => trends.access[date] || 0);
    
    const loginsCtx = document.getElementById('loginsChart');
    if (loginsCtx) {
        new Chart(loginsCtx, {
            type: 'bar',
            data: {
                labels: dates.map(d => formatDate(d)),
                datasets: [
                    {
                        label: '登录次数',
                        data: loginsData,
                        backgroundColor: 'rgba(25, 118, 210, 0.7)',
                        borderColor: 'rgb(25, 118, 210)',
                        borderWidth: 1
                    },
                    {
                        label: '访问次数',
                        data: accessData,
                        backgroundColor: 'rgba(255, 152, 0, 0.7)',
                        borderColor: 'rgb(255, 152, 0)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }
}

// 渲染分布图表
function renderDistributionCharts(distribution) {
    // 用户类型分布
    const userTypeCtx = document.getElementById('userTypeChart');
    if (userTypeCtx && distribution.user_type) {
        const typeLabels = Object.keys(distribution.user_type).map(t => {
            return t === 'internal' ? '内部用户' : '外部用户';
        });
        const typeData = Object.values(distribution.user_type);
        
        new Chart(userTypeCtx, {
            type: 'doughnut',
            data: {
                labels: typeLabels,
                datasets: [{
                    data: typeData,
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(118, 75, 162, 0.8)'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    // 用户角色分布
    const roleCtx = document.getElementById('roleChart');
    if (roleCtx && distribution.role) {
        const roleLabels = Object.keys(distribution.role).map(r => {
            return r === 'user' ? '普通用户' : r === 'admin' ? '管理员' : '超级管理员';
        });
        const roleData = Object.values(distribution.role);
        
        new Chart(roleCtx, {
            type: 'doughnut',
            data: {
                labels: roleLabels,
                datasets: [{
                    data: roleData,
                    backgroundColor: [
                        'rgba(52, 168, 83, 0.8)',
                        'rgba(255, 152, 0, 0.8)',
                        'rgba(244, 67, 54, 0.8)'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

// 加载最近活动
async function loadRecentActivity() {
    try {
        const response = await fetch('/api/admin/logs/login?page=1&per_page=10', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        if (data.success && data.logs) {
            displayRecentActivity(data.logs);
        }
    } catch (error) {
        console.error('加载最近活动失败:', error);
    }
}

// 显示最近活动
function displayRecentActivity(logs) {
    const container = document.getElementById('recent-activity');
    if (!container) return;
    
    if (logs.length === 0) {
        container.innerHTML = '<p class="no-data">暂无活动记录</p>';
        return;
    }
    
    const html = logs.map(log => {
        const statusClass = log.status === 'success' ? 'success' : 'failed';
        const statusText = log.status === 'success' ? '成功' : '失败';
        const userName = log.user ? log.user.name : '未知用户';
        
        return `
            <div class="activity-item">
                <div class="activity-icon ${statusClass}">
                    <svg viewBox="0 0 24 24" width="16" height="16">
                        ${log.status === 'success' ? 
                            '<path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>' :
                            '<path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>'
                        }
                    </svg>
                </div>
                <div class="activity-content">
                    <div class="activity-text">
                        <strong>${userName}</strong> ${log.login_type === 'feishu' ? '通过飞书' : '使用密码'}登录
                        <span class="activity-status ${statusClass}">${statusText}</span>
                    </div>
                    <div class="activity-time">${formatDateTime(log.login_time)}</div>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = html;
}

// 退出登录
if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
        } catch (error) {
            console.error('退出登录失败:', error);
        } finally {
            localStorage.removeItem('auth_token');
            window.location.href = '/admin/login';
        }
    });
}

// 工具函数
function generateDateRange(startDate, endDate) {
    const dates = [];
    const current = new Date(startDate);
    const end = new Date(endDate);
    
    while (current <= end) {
        dates.push(current.toISOString().split('T')[0]);
        current.setDate(current.getDate() + 1);
    }
    
    return dates;
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return `${date.getMonth() + 1}/${date.getDate()}`;
}

function formatDateTime(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN');
}

function showToast(message, type = 'info') {
    if (!toast) return;
    
    toast.textContent = message;
    toast.className = `toast toast-${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// 页面加载时执行
document.addEventListener('DOMContentLoaded', async () => {
    // 验证身份并加载管理员信息
    try {
        const response = await fetch('/api/admin/profile', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            localStorage.removeItem('auth_token');
            window.location.href = '/admin/login';
            return;
        }
        
        const data = await response.json();
        if (data.success && data.user) {
            if (adminUserName) {
                adminUserName.textContent = data.user.name;
            }
            
            // 检查权限（必须是管理员或超级管理员）
            if (data.user.role !== 'admin' && data.user.role !== 'super_admin') {
                showToast('权限不足，您不是管理员', 'error');
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
                return;
            }
            
            // 加载数据
            await loadOverviewStats();
            await loadTrendsStats(30);
            await loadRecentActivity();
        }
    } catch (error) {
        console.error('验证身份失败:', error);
        localStorage.removeItem('auth_token');
        window.location.href = '/admin/login';
    }
});

