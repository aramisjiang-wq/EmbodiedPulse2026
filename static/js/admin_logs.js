/**
 * 日志监控页面逻辑
 */

// 全局变量
const token = localStorage.getItem('auth_token');
let currentTab = 'login';
let loginPage = 1;
let accessPage = 1;
const perPage = 50;
let loginFilters = { user_id: '', status: '', start_date: '', end_date: '' };
let accessFilters = { user_id: '', start_date: '', end_date: '' };

// 检查登录状态
if (!token) {
    window.location.href = '/admin/login';
}

// DOM元素
const adminUserName = document.getElementById('admin-user-name');
const logoutBtn = document.getElementById('logout-btn');
const tabBtns = document.querySelectorAll('.tab-btn');
const loginLogsTab = document.getElementById('login-logs-tab');
const accessLogsTab = document.getElementById('access-logs-tab');
const toast = document.getElementById('toast');

// Tab切换
tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        switchTab(tab);
    });
});

function switchTab(tab) {
    currentTab = tab;
    
    // 更新按钮状态
    tabBtns.forEach(btn => {
        if (btn.dataset.tab === tab) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // 更新内容显示
    if (tab === 'login') {
        loginLogsTab.classList.add('active');
        accessLogsTab.classList.remove('active');
        if (document.getElementById('login-logs-tbody').children.length === 1 &&
            document.getElementById('login-logs-tbody').children[0].textContent.includes('加载中')) {
            loadLoginLogs(1);
        }
    } else {
        accessLogsTab.classList.add('active');
        loginLogsTab.classList.remove('active');
        if (document.getElementById('access-logs-tbody').children.length === 1 &&
            document.getElementById('access-logs-tbody').children[0].textContent.includes('加载中')) {
            loadAccessLogs(1);
        }
    }
}

// ==================== 登录日志 ====================

// 加载登录日志
async function loadLoginLogs(page = 1) {
    try {
        loginPage = page;
        const params = new URLSearchParams({
            page: page,
            per_page: perPage,
            ...loginFilters
        });
        
        const response = await fetch(`/api/admin/logs/login?${params}`, {
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
            throw new Error('获取登录日志失败');
        }
        
        const data = await response.json();
        if (data.success) {
            displayLoginLogs(data.logs);
            displayPagination('login-pagination', data.current_page, data.total, data.per_page, 'login');
        } else {
            showToast('获取登录日志失败: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('加载登录日志失败:', error);
        showToast('加载登录日志失败', 'error');
    }
}

// 显示登录日志
function displayLoginLogs(logs) {
    const tbody = document.getElementById('login-logs-tbody');
    
    if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="no-data">暂无日志数据</td></tr>';
        return;
    }
    
    tbody.innerHTML = logs.map(log => `
        <tr>
            <td>${log.id}</td>
            <td>
                ${log.user ? `
                    <div>
                        <div><strong>${log.user.name}</strong></div>
                        <div style="font-size: 12px; color: #95a5a6;">${log.user.email || '-'}</div>
                    </div>
                ` : `<span style="color: #95a5a6;">用户ID: ${log.user_id || '-'}</span>`}
            </td>
            <td><span class="badge badge-${log.login_type === 'feishu' ? 'primary' : 'default'}">${log.login_type === 'feishu' ? '飞书' : '密码'}</span></td>
            <td><span class="badge ${log.status === 'success' ? 'badge-success' : 'badge-danger'}">${log.status === 'success' ? '成功' : '失败'}</span></td>
            <td>${log.failure_reason || '-'}</td>
            <td>${log.ip_address || '-'}</td>
            <td>${formatDateTime(log.login_time)}</td>
        </tr>
    `).join('');
}

// 登录日志搜索
document.getElementById('login-search-btn').addEventListener('click', () => {
    loginFilters.user_id = document.getElementById('login-user-id').value.trim();
    loginFilters.status = document.getElementById('login-status').value;
    loginFilters.start_date = document.getElementById('login-start-date').value;
    loginFilters.end_date = document.getElementById('login-end-date').value;
    loadLoginLogs(1);
});

// 登录日志重置
document.getElementById('login-reset-btn').addEventListener('click', () => {
    document.getElementById('login-user-id').value = '';
    document.getElementById('login-status').value = '';
    document.getElementById('login-start-date').value = '';
    document.getElementById('login-end-date').value = '';
    loginFilters = { user_id: '', status: '', start_date: '', end_date: '' };
    loadLoginLogs(1);
});

// ==================== 访问日志 ====================

// 加载访问日志
async function loadAccessLogs(page = 1) {
    try {
        accessPage = page;
        const params = new URLSearchParams({
            page: page,
            per_page: perPage,
            ...accessFilters
        });
        
        const response = await fetch(`/api/admin/logs/access?${params}`, {
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
            throw new Error('获取访问日志失败');
        }
        
        const data = await response.json();
        if (data.success) {
            displayAccessLogs(data.logs);
            displayPagination('access-pagination', data.current_page, data.total, data.per_page, 'access');
        } else {
            showToast('获取访问日志失败: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('加载访问日志失败:', error);
        showToast('加载访问日志失败', 'error');
    }
}

// 显示访问日志
function displayAccessLogs(logs) {
    const tbody = document.getElementById('access-logs-tbody');
    
    if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="no-data">暂无日志数据</td></tr>';
        return;
    }
    
    tbody.innerHTML = logs.map(log => `
        <tr>
            <td>${log.id}</td>
            <td>
                ${log.user ? `
                    <div>
                        <div><strong>${log.user.name}</strong></div>
                        <div style="font-size: 12px; color: #95a5a6;">${log.user.email || '-'}</div>
                    </div>
                ` : `<span style="color: #95a5a6;">用户ID: ${log.user_id || '-'}</span>`}
            </td>
            <td><a href="${log.page_url}" target="_blank" title="${log.page_url}">${truncateUrl(log.page_url)}</a></td>
            <td>${log.ip_address || '-'}</td>
            <td>${formatDuration(log.duration_ms)}</td>
            <td>${formatDateTime(log.access_time)}</td>
        </tr>
    `).join('');
}

// 访问日志搜索
document.getElementById('access-search-btn').addEventListener('click', () => {
    accessFilters.user_id = document.getElementById('access-user-id').value.trim();
    accessFilters.start_date = document.getElementById('access-start-date').value;
    accessFilters.end_date = document.getElementById('access-end-date').value;
    loadAccessLogs(1);
});

// 访问日志重置
document.getElementById('access-reset-btn').addEventListener('click', () => {
    document.getElementById('access-user-id').value = '';
    document.getElementById('access-start-date').value = '';
    document.getElementById('access-end-date').value = '';
    accessFilters = { user_id: '', start_date: '', end_date: '' };
    loadAccessLogs(1);
});

// ==================== 分页 ====================

function displayPagination(containerId, current, total, per_page, type) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const totalPages = Math.ceil(total / per_page);
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // 上一页
    if (current > 1) {
        const prevPage = current - 1;
        html += `<button class="page-btn" onclick="${type === 'login' ? 'loadLoginLogs' : 'loadAccessLogs'}(${prevPage})">上一页</button>`;
    }
    
    // 页码
    for (let i = 1; i <= Math.min(totalPages, 10); i++) {
        if (i === current) {
            html += `<button class="page-btn active">${i}</button>`;
        } else {
            html += `<button class="page-btn" onclick="${type === 'login' ? 'loadLoginLogs' : 'loadAccessLogs'}(${i})">${i}</button>`;
        }
    }
    
    if (totalPages > 10) {
        html += '<span>...</span>';
    }
    
    // 下一页
    if (current < totalPages) {
        const nextPage = current + 1;
        html += `<button class="page-btn" onclick="${type === 'login' ? 'loadLoginLogs' : 'loadAccessLogs'}(${nextPage})">下一页</button>`;
    }
    
    html += `<span class="page-info">共 ${total} 条</span>`;
    
    container.innerHTML = html;
}

// ==================== 工具函数 ====================

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

function truncateUrl(url) {
    if (!url) return '-';
    const maxLength = 50;
    if (url.length <= maxLength) return url;
    return url.substring(0, maxLength) + '...';
}

function showToast(message, type = 'info') {
    if (!toast) return;
    
    toast.textContent = message;
    toast.className = `toast toast-${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
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

// 页面加载时执行
document.addEventListener('DOMContentLoaded', async () => {
    // 验证身份
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
            
            // 检查权限
            if (data.user.role !== 'admin' && data.user.role !== 'super_admin') {
                showToast('权限不足，您不是管理员', 'error');
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
                return;
            }
            
            // 加载登录日志
            loadLoginLogs(1);
        }
    } catch (error) {
        console.error('验证身份失败:', error);
        localStorage.removeItem('auth_token');
        window.location.href = '/admin/login';
    }
});

// 全局函数（供onclick使用）
window.loadLoginLogs = loadLoginLogs;
window.loadAccessLogs = loadAccessLogs;

