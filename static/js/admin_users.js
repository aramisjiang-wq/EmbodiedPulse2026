/**
 * 用户管理页面逻辑
 */

// 全局变量
const token = localStorage.getItem('auth_token');
let currentPage = 1;
let perPage = 20;
let currentFilters = {
    search: '',
    status: '',
    role: ''
};
let selectedUsers = new Set();
let currentUserRole = '';

// 检查登录状态
if (!token) {
    window.location.href = '/admin/login';
}

// DOM元素
const adminUserName = document.getElementById('admin-user-name');
const logoutBtn = document.getElementById('logout-btn');
const searchInput = document.getElementById('search-input');
const statusFilter = document.getElementById('status-filter');
const roleFilter = document.getElementById('role-filter');
const searchBtn = document.getElementById('search-btn');
const resetBtn = document.getElementById('reset-btn');
const selectAllCheckbox = document.getElementById('select-all');
const batchActiveBtn = document.getElementById('batch-active-btn');
const batchBanBtn = document.getElementById('batch-ban-btn');
const usersTbody = document.getElementById('users-tbody');
const pagination = document.getElementById('pagination');
const userModal = document.getElementById('user-modal');
const editModal = document.getElementById('edit-modal');
const editForm = document.getElementById('edit-form');
const toast = document.getElementById('toast');

// 加载用户列表
async function loadUsers(page = 1) {
    try {
        currentPage = page;
        const params = new URLSearchParams({
            page: page,
            per_page: perPage,
            ...currentFilters
        });
        
        const response = await fetch(`/api/admin/users?${params}`, {
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
            throw new Error('获取用户列表失败');
        }
        
        const data = await response.json();
        if (data.success) {
            displayUsers(data.users);
            displayPagination(data.current_page, data.total, data.per_page);
        } else {
            showToast('获取用户列表失败: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('加载用户列表失败:', error);
        showToast('加载用户列表失败', 'error');
    }
}

// 显示用户列表
function displayUsers(users) {
    if (users.length === 0) {
        usersTbody.innerHTML = '<tr><td colspan="11" class="no-data">暂无用户数据</td></tr>';
        return;
    }
    
    usersTbody.innerHTML = users.map(user => `
        <tr>
            <td><input type="checkbox" class="user-checkbox" data-user-id="${user.id}"></td>
            <td>${user.id}</td>
            <td>${user.name}</td>
            <td>${user.email || '-'}</td>
            <td>${user.mobile || '-'}</td>
            <td><span class="badge badge-${user.user_type === 'internal' ? 'primary' : 'default'}">${user.user_type === 'internal' ? '内部' : '外部'}</span></td>
            <td><span class="badge ${getRoleBadgeClass(user.role)}">${getRoleLabel(user.role)}</span></td>
            <td><span class="badge ${getStatusBadgeClass(user.status)}">${getStatusLabel(user.status)}</span></td>
            <td>${formatDateTime(user.created_at)}</td>
            <td>${formatDateTime(user.last_login_at)}</td>
            <td>
                <button class="btn-icon" onclick="viewUser(${user.id})" title="查看">
                    <svg viewBox="0 0 24 24" width="18" height="18">
                        <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                    </svg>
                </button>
                <button class="btn-icon" onclick="editUser(${user.id})" title="编辑">
                    <svg viewBox="0 0 24 24" width="18" height="18">
                        <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                    </svg>
                </button>
                ${user.role !== 'super_admin' && currentUserRole === 'super_admin' ? `
                <button class="btn-icon btn-danger" onclick="deleteUser(${user.id}, '${user.name}')" title="删除">
                    <svg viewBox="0 0 24 24" width="18" height="18">
                        <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                    </svg>
                </button>
                ` : ''}
            </td>
        </tr>
    `).join('');
    
    // 添加复选框事件监听
    document.querySelectorAll('.user-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', handleCheckboxChange);
    });
}

// 显示分页
function displayPagination(current, total, per_page) {
    if (!pagination) return;
    
    const totalPages = Math.ceil(total / per_page);
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // 上一页
    if (current > 1) {
        html += `<button class="page-btn" onclick="loadUsers(${current - 1})">上一页</button>`;
    }
    
    // 页码
    for (let i = 1; i <= Math.min(totalPages, 10); i++) {
        if (i === current) {
            html += `<button class="page-btn active">${i}</button>`;
        } else {
            html += `<button class="page-btn" onclick="loadUsers(${i})">${i}</button>`;
        }
    }
    
    if (totalPages > 10) {
        html += '<span>...</span>';
    }
    
    // 下一页
    if (current < totalPages) {
        html += `<button class="page-btn" onclick="loadUsers(${current + 1})">下一页</button>`;
    }
    
    html += `<span class="page-info">共 ${total} 个用户</span>`;
    
    pagination.innerHTML = html;
}

// 查看用户详情
async function viewUser(userId) {
    try {
        const response = await fetch(`/api/admin/users/${userId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        if (data.success) {
            displayUserDetail(data.user, data.login_history, data.stats);
            userModal.style.display = 'flex';
        } else {
            showToast('获取用户详情失败', 'error');
        }
    } catch (error) {
        console.error('获取用户详情失败:', error);
        showToast('获取用户详情失败', 'error');
    }
}

// 显示用户详情
function displayUserDetail(user, history, stats) {
    const modalBody = document.getElementById('modal-body');
    modalBody.innerHTML = `
        <div class="user-detail">
            <h4>基本信息</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <label>用户ID</label>
                    <span>${user.id}</span>
                </div>
                <div class="detail-item">
                    <label>姓名</label>
                    <span>${user.name}</span>
                </div>
                <div class="detail-item">
                    <label>邮箱</label>
                    <span>${user.email || '-'}</span>
                </div>
                <div class="detail-item">
                    <label>手机</label>
                    <span>${user.mobile || '-'}</span>
                </div>
                <div class="detail-item">
                    <label>部门</label>
                    <span>${user.department || '-'}</span>
                </div>
                <div class="detail-item">
                    <label>飞书ID</label>
                    <span>${user.feishu_id}</span>
                </div>
                <div class="detail-item">
                    <label>用户类型</label>
                    <span class="badge badge-${user.user_type === 'internal' ? 'primary' : 'default'}">${user.user_type === 'internal' ? '内部用户' : '外部用户'}</span>
                </div>
                <div class="detail-item">
                    <label>角色</label>
                    <span class="badge ${getRoleBadgeClass(user.role)}">${getRoleLabel(user.role)}</span>
                </div>
                <div class="detail-item">
                    <label>状态</label>
                    <span class="badge ${getStatusBadgeClass(user.status)}">${getStatusLabel(user.status)}</span>
                </div>
                <div class="detail-item">
                    <label>注册时间</label>
                    <span>${formatDateTime(user.created_at)}</span>
                </div>
                <div class="detail-item">
                    <label>最后登录</label>
                    <span>${formatDateTime(user.last_login_at)}</span>
                </div>
                <div class="detail-item">
                    <label>更新时间</label>
                    <span>${formatDateTime(user.updated_at)}</span>
                </div>
            </div>
            
            <h4 style="margin-top: 24px;">统计数据</h4>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">${stats.total_access_count || 0}</div>
                    <div class="stat-label">总访问次数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.today_access_count || 0}</div>
                    <div class="stat-label">今日访问</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.login_count || 0}</div>
                    <div class="stat-label">成功登录次数</div>
                </div>
            </div>
            
            <h4 style="margin-top: 24px;">最近登录历史</h4>
            <div class="history-list">
                ${history.length > 0 ? history.map(h => `
                    <div class="history-item">
                        <span class="badge ${h.status === 'success' ? 'badge-success' : 'badge-danger'}">${h.status === 'success' ? '成功' : '失败'}</span>
                        <span>${h.login_type === 'feishu' ? '飞书登录' : '密码登录'}</span>
                        <span>${formatDateTime(h.login_time)}</span>
                        <span>${h.ip_address || '-'}</span>
                    </div>
                `).join('') : '<p class="no-data">暂无登录历史</p>'}
            </div>
        </div>
    `;
}

// 编辑用户
async function editUser(userId) {
    try {
        const response = await fetch(`/api/admin/users/${userId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        if (data.success) {
            showEditModal(data.user);
        } else {
            showToast('获取用户信息失败', 'error');
        }
    } catch (error) {
        console.error('获取用户信息失败:', error);
        showToast('获取用户信息失败', 'error');
    }
}

// 显示编辑模态框
function showEditModal(user) {
    document.getElementById('edit-user-id').value = user.id;
    document.getElementById('edit-name').value = user.name;
    document.getElementById('edit-email').value = user.email || '';
    document.getElementById('edit-mobile').value = user.mobile || '';
    document.getElementById('edit-department').value = user.department || '';
    document.getElementById('edit-status').value = user.status;
    document.getElementById('edit-role').value = user.role;
    
    // 只有超级管理员可以修改角色
    if (currentUserRole !== 'super_admin') {
        document.getElementById('role-group').style.display = 'none';
    }
    
    editModal.style.display = 'flex';
}

// 提交编辑表单
if (editForm) {
    editForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const userId = document.getElementById('edit-user-id').value;
        const formData = {
            name: document.getElementById('edit-name').value,
            email: document.getElementById('edit-email').value,
            mobile: document.getElementById('edit-mobile').value,
            department: document.getElementById('edit-department').value,
            status: document.getElementById('edit-status').value
        };
        
        if (currentUserRole === 'super_admin') {
            formData.role = document.getElementById('edit-role').value;
        }
        
        try {
            const response = await fetch(`/api/admin/users/${userId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            if (data.success) {
                showToast('用户信息更新成功', 'success');
                editModal.style.display = 'none';
                loadUsers(currentPage);
            } else {
                showToast('更新失败: ' + data.message, 'error');
            }
        } catch (error) {
            console.error('更新用户失败:', error);
            showToast('更新用户失败', 'error');
        }
    });
}

// 删除用户
async function deleteUser(userId, userName) {
    if (!confirm(`确定要删除用户"${userName}"吗？此操作不可恢复！`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/users/${userId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        if (data.success) {
            showToast('用户删除成功', 'success');
            loadUsers(currentPage);
        } else {
            showToast('删除失败: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('删除用户失败:', error);
        showToast('删除用户失败', 'error');
    }
}

// 搜索和筛选
if (searchBtn) {
    searchBtn.addEventListener('click', () => {
        currentFilters.search = searchInput.value.trim();
        currentFilters.status = statusFilter.value;
        currentFilters.role = roleFilter.value;
        loadUsers(1);
    });
}

if (resetBtn) {
    resetBtn.addEventListener('click', () => {
        searchInput.value = '';
        statusFilter.value = '';
        roleFilter.value = '';
        currentFilters = { search: '', status: '', role: '' };
        loadUsers(1);
    });
}

// 全选/取消全选
if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener('change', (e) => {
        const checkboxes = document.querySelectorAll('.user-checkbox');
        checkboxes.forEach(cb => {
            cb.checked = e.target.checked;
            const userId = parseInt(cb.dataset.userId);
            if (e.target.checked) {
                selectedUsers.add(userId);
            } else {
                selectedUsers.delete(userId);
            }
        });
        updateBatchButtons();
    });
}

// 处理复选框变化
function handleCheckboxChange(e) {
    const userId = parseInt(e.target.dataset.userId);
    if (e.target.checked) {
        selectedUsers.add(userId);
    } else {
        selectedUsers.delete(userId);
        selectAllCheckbox.checked = false;
    }
    updateBatchButtons();
}

// 更新批量操作按钮状态
function updateBatchButtons() {
    const hasSelection = selectedUsers.size > 0;
    batchActiveBtn.disabled = !hasSelection;
    batchBanBtn.disabled = !hasSelection;
}

// 批量激活
if (batchActiveBtn) {
    batchActiveBtn.addEventListener('click', () => {
        batchUpdateStatus('active');
    });
}

// 批量禁用
if (batchBanBtn) {
    batchBanBtn.addEventListener('click', () => {
        if (!confirm(`确定要禁用选中的 ${selectedUsers.size} 个用户吗？`)) {
            return;
        }
        batchUpdateStatus('banned');
    });
}

// 批量更新状态
async function batchUpdateStatus(status) {
    try {
        const response = await fetch('/api/admin/users/batch', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_ids: Array.from(selectedUsers),
                action: 'update_status',
                value: status
            })
        });
        
        const data = await response.json();
        if (data.success) {
            showToast(data.message, 'success');
            selectedUsers.clear();
            selectAllCheckbox.checked = false;
            updateBatchButtons();
            loadUsers(currentPage);
        } else {
            showToast('批量操作失败: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('批量操作失败:', error);
        showToast('批量操作失败', 'error');
    }
}

// 模态框关闭
document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => {
        userModal.style.display = 'none';
        editModal.style.display = 'none';
    });
});

window.addEventListener('click', (e) => {
    if (e.target === userModal) {
        userModal.style.display = 'none';
    }
    if (e.target === editModal) {
        editModal.style.display = 'none';
    }
});

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

function getStatusBadgeClass(status) {
    const classes = {
        'active': 'badge-success',
        'inactive': 'badge-default',
        'banned': 'badge-danger'
    };
    return classes[status] || 'badge-default';
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
    // 验证身份
    try {
        const response = await fetch('/api/user/profile', {
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
            
            currentUserRole = data.user.role;
            
            // 检查权限
            if (data.user.role !== 'admin' && data.user.role !== 'super_admin') {
                showToast('权限不足，您不是管理员', 'error');
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
                return;
            }
            
            // 加载用户列表
            loadUsers(1);
        }
    } catch (error) {
        console.error('验证身份失败:', error);
        localStorage.removeItem('auth_token');
        window.location.href = '/admin/login';
    }
});

// 全局函数（供onclick使用）
window.viewUser = viewUser;
window.editUser = editUser;
window.deleteUser = deleteUser;
window.loadUsers = loadUsers;

