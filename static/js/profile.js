/**
 * 个人中心页面逻辑
 */

// 全局变量
let currentTab = 'info';
let currentUser = null;
const token = localStorage.getItem('auth_token');

// DOM元素
const navUserName = document.getElementById('nav-user-name');
const logoutBtn = document.getElementById('logout-btn');
const profileEditForm = document.getElementById('profile-edit-form');
const activityFilterBtn = document.getElementById('activity-filter-btn');
const toast = document.getElementById('toast');

// 检查登录状态
if (!token) {
    window.location.href = '/login';
}

// 加载用户详细信息
async function loadUserProfile() {
    try {
        const response = await fetch('/api/user/profile', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                // token无效，跳转到登录页
                localStorage.removeItem('auth_token');
                window.location.href = '/login';
                return;
            }
            throw new Error('获取用户信息失败');
        }
        
        const data = await response.json();
        if (data.success) {
            currentUser = data.user;
            displayUserProfile(data.user);
        } else {
            showToast('获取用户信息失败: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('加载用户信息失败:', error);
        showToast('加载用户信息失败', 'error');
    }
}

// 显示用户信息
function displayUserProfile(user) {
    // 侧边栏用户卡片
    document.getElementById('user-avatar').src = user.avatar_url || '/static/images/default-avatar.png';
    document.getElementById('user-name').textContent = user.name;
    document.getElementById('user-department').textContent = user.department || '-';
    document.getElementById('user-role-badge').textContent = getRoleLabel(user.role);
    document.getElementById('user-role-badge').className = 'badge ' + getRoleBadgeClass(user.role);
    
    // 导航栏
    if (navUserName) {
        navUserName.textContent = user.name;
    }
    
    // Tab 1: 基本信息
    document.getElementById('info-name').textContent = user.name;
    document.getElementById('info-email').textContent = user.email || '-';
    document.getElementById('info-mobile').textContent = user.mobile || '-';
    document.getElementById('info-department').textContent = user.department || '-';
    document.getElementById('info-user-type').textContent = user.user_type;
    document.getElementById('info-role').textContent = getRoleLabel(user.role);
    document.getElementById('info-status').textContent = getStatusLabel(user.status);
    document.getElementById('info-created').textContent = formatDateTime(user.created_at);
    document.getElementById('info-last-login').textContent = formatDateTime(user.last_login_at);
    
    // Tab 2: 编辑表单
    document.getElementById('edit-email').value = user.email || '';
    document.getElementById('edit-mobile').value = user.mobile || '';
    document.getElementById('edit-avatar').value = user.avatar_url || '';
}

// 加载登录历史
async function loadLoginHistory(page = 1) {
    try {
        const response = await fetch(`/api/user/login-history?page=${page}&per_page=20`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        if (data.success) {
            displayLoginHistory(data.history);
            displayPagination('login-pagination', page, data.total, data.per_page, loadLoginHistory);
        } else {
            showToast('加载登录历史失败', 'error');
        }
    } catch (error) {
        console.error('加载登录历史失败:', error);
        showToast('加载登录历史失败', 'error');
    }
}

// 显示登录历史
function displayLoginHistory(history) {
    const tbody = document.getElementById('login-history-tbody');
    
    if (history.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="no-data">暂无登录历史</td></tr>';
        return;
    }
    
    tbody.innerHTML = history.map(h => `
        <tr>
            <td>${formatDateTime(h.login_time)}</td>
            <td><span class="badge">${getLoginTypeLabel(h.login_type)}</span></td>
            <td>${h.ip_address || '-'}</td>
            <td>${h.location || '-'}</td>
            <td><span class="badge ${h.status === 'success' ? 'badge-success' : 'badge-danger'}">${h.status === 'success' ? '成功' : '失败'}</span></td>
        </tr>
    `).join('');
}

// 加载访问日志
async function loadAccessLogs(page = 1, startDate = null) {
    try {
        let url = `/api/user/access-logs?page=${page}&per_page=50`;
        if (startDate) {
            url += `&start_date=${startDate}`;
        }
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        if (data.success) {
            displayAccessLogs(data.logs);
            displayPagination('activity-pagination', page, data.total, data.per_page, loadAccessLogs);
        } else {
            showToast('加载访问记录失败', 'error');
        }
    } catch (error) {
        console.error('加载访问记录失败:', error);
        showToast('加载访问记录失败', 'error');
    }
}

// 显示访问日志
function displayAccessLogs(logs) {
    const tbody = document.getElementById('activity-tbody');
    
    if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="no-data">暂无访问记录</td></tr>';
        return;
    }
    
    tbody.innerHTML = logs.map(log => `
        <tr>
            <td>${formatDateTime(log.access_time)}</td>
            <td><a href="${log.page_url}" target="_blank">${log.page_title || log.page_url}</a></td>
            <td>${formatDuration(log.duration)}</td>
        </tr>
    `).join('');
}

// 加载统计数据
async function loadUserStats() {
    try {
        const response = await fetch('/api/user/stats', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        if (data.success) {
            displayUserStats(data.stats);
        } else {
            showToast('加载统计数据失败', 'error');
        }
    } catch (error) {
        console.error('加载统计数据失败:', error);
        showToast('加载统计数据失败', 'error');
    }
}

// 显示统计数据
function displayUserStats(stats) {
    document.getElementById('stat-total-logins').textContent = stats.total_logins || 0;
    document.getElementById('stat-total-access').textContent = stats.total_access || 0;
    document.getElementById('stat-today-access').textContent = stats.today_access || 0;
    document.getElementById('stat-account-age').textContent = stats.account_age_days || 0;
    document.getElementById('stat-most-visited').textContent = stats.most_visited_page || '暂无数据';
}

// 分页组件
function displayPagination(containerId, currentPage, total, perPage, callback) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const totalPages = Math.ceil(total / perPage);
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '<div class="pagination-inner">';
    
    // 上一页
    if (currentPage > 1) {
        html += `<button class="page-btn" onclick="loadPageData('${containerId}', ${currentPage - 1}, ${callback})">上一页</button>`;
    }
    
    // 页码
    for (let i = 1; i <= Math.min(totalPages, 10); i++) {
        if (i === currentPage) {
            html += `<button class="page-btn active">${i}</button>`;
        } else {
            html += `<button class="page-btn" onclick="loadPageData('${containerId}', ${i}, ${callback})">${i}</button>`;
        }
    }
    
    if (totalPages > 10) {
        html += '<span>...</span>';
    }
    
    // 下一页
    if (currentPage < totalPages) {
        html += `<button class="page-btn" onclick="loadPageData('${containerId}', ${currentPage + 1}, ${callback})">下一页</button>`;
    }
    
    html += `<span class="page-info">共 ${total} 条</span>`;
    html += '</div>';
    
    container.innerHTML = html;
}

// 更新个人信息
if (profileEditForm) {
    profileEditForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        
        try {
            const response = await fetch('/api/user/profile', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            if (result.success) {
                showToast('个人信息更新成功', 'success');
                currentUser = result.user;
                displayUserProfile(result.user);
                // 切换到基本信息Tab
                switchTab('info');
            } else {
                showToast('更新失败：' + result.message, 'error');
            }
        } catch (error) {
            console.error('更新失败:', error);
            showToast('更新失败', 'error');
        }
    });
}

// Tab切换
document.querySelectorAll('.menu-item').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const tab = e.currentTarget.dataset.tab;
        switchTab(tab);
    });
});

function switchTab(tab) {
    // 更新菜单激活状态
    document.querySelectorAll('.menu-item').forEach(a => a.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
    
    // 更新内容显示
    document.querySelectorAll('.profile-tab').forEach(t => t.classList.remove('active'));
    document.getElementById(`tab-${tab}`).classList.add('active');
    
    // 加载对应数据
    currentTab = tab;
    if (tab === 'login') {
        loadLoginHistory();
    } else if (tab === 'activity') {
        loadAccessLogs();
    } else if (tab === 'stats') {
        loadUserStats();
    }
}

// 访问记录筛选
if (activityFilterBtn) {
    activityFilterBtn.addEventListener('click', () => {
        const startDate = document.getElementById('activity-start-date').value;
        loadAccessLogs(1, startDate);
    });
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
            window.location.href = '/login';
        }
    });
}

// Toast提示
function showToast(message, type = 'info') {
    if (!toast) return;
    
    toast.textContent = message;
    toast.className = `toast toast-${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// 工具函数
function getRoleLabel(role) {
    const labels = {
        'user': '普通用户',
        'admin': '管理员',
        'super_admin': '超级管理员'
    };
    return labels[role] || role;
}

function getRoleBadgeClass(role) {
    const classes = {
        'user': 'badge-default',
        'admin': 'badge-warning',
        'super_admin': 'badge-danger'
    };
    return classes[role] || 'badge-default';
}

function getStatusLabel(status) {
    const labels = {
        'active': '正常',
        'inactive': '未激活',
        'banned': '已禁用'
    };
    return labels[status] || status;
}

function getLoginTypeLabel(type) {
    const labels = {
        'feishu': '飞书',
        'password': '密码'
    };
    return labels[type] || type;
}

function formatDateTime(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN');
}

function formatDuration(ms) {
    if (!ms) return '-';
    const seconds = Math.floor(ms / 1000);
    if (seconds < 60) return `${seconds}秒`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}分${remainingSeconds}秒`;
}

// 页面加载时执行
document.addEventListener('DOMContentLoaded', () => {
    loadUserProfile();
});

// 记录页面访问
fetch('/api/auth/log-access', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        page_url: window.location.href,
        page_title: document.title
    })
}).catch(err => console.error('记录访问日志失败:', err));

