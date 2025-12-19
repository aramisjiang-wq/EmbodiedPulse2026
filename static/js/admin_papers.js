/**
 * 论文管理页面逻辑
 */

// 全局变量
const token = localStorage.getItem('auth_token');
let currentPage = 1;
let perPage = 20;
let currentFilters = {
    search: '',
    category: '',
    date_from: '',
    date_to: '',
    min_citations: ''
};
let selectedPapers = new Set();
let currentUserRole = '';
let categories = [];

// 检查登录状态
if (!token) {
    window.location.href = '/admin/login';
}

// DOM元素
const adminUserName = document.getElementById('admin-user-name');
const logoutBtn = document.getElementById('logout-btn');
const searchInput = document.getElementById('search-input');
const categoryFilter = document.getElementById('category-filter');
const dateFrom = document.getElementById('date-from');
const dateTo = document.getElementById('date-to');
const minCitations = document.getElementById('min-citations');
const searchBtn = document.getElementById('search-btn');
const resetBtn = document.getElementById('reset-btn');
const selectAllCheckbox = document.getElementById('select-all');
const papersTbody = document.getElementById('papers-tbody');
const pagination = document.getElementById('pagination');
const paperModal = document.getElementById('paper-modal');
const editModal = document.getElementById('edit-modal');
const editForm = document.getElementById('edit-form');
const toast = document.getElementById('toast');

// 加载统计信息
async function loadStats() {
    try {
        const response = await fetch('/api/admin/papers/stats', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                document.getElementById('stat-total').textContent = data.stats.total || 0;
                document.getElementById('stat-today').textContent = data.stats.today || 0;
                document.getElementById('stat-avg-citations').textContent = data.stats.avg_citations || 0;
                document.getElementById('stat-categories').textContent = data.stats.categories || 0;
            }
        }
    } catch (error) {
        console.error('加载统计信息失败:', error);
    }
}

// 加载类别列表
async function loadCategories() {
    try {
        // 从API获取所有类别（通过获取第一页数据来获取类别）
        const response = await fetch('/api/admin/papers?page=1&per_page=1', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            // 从taxonomy获取类别列表（如果前端有的话）
            // 或者从API获取所有唯一类别
            const allCategoriesResponse = await fetch('/api/papers', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (allCategoriesResponse.ok) {
                const allData = await allCategoriesResponse.json();
                if (allData.success && allData.data) {
                    categories = Object.keys(allData.data).sort();
                    categories.forEach(cat => {
                        const option = document.createElement('option');
                        option.value = cat;
                        option.textContent = cat;
                        categoryFilter.appendChild(option);
                    });
                }
            }
        }
    } catch (error) {
        console.error('加载类别列表失败:', error);
    }
}

// 加载论文列表
async function loadPapers(page = 1) {
    try {
        currentPage = page;
        const params = new URLSearchParams({
            page: page,
            per_page: perPage,
            ...currentFilters
        });
        
        const response = await fetch(`/api/admin/papers?${params}`, {
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
            throw new Error('获取论文列表失败');
        }
        
        const data = await response.json();
        if (data.success) {
            displayPapers(data.papers);
            displayPagination(data.pagination.current_page, data.pagination.total, data.pagination.per_page);
        } else {
            showToast('获取论文列表失败: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('加载论文列表失败:', error);
        showToast('加载论文列表失败', 'error');
    }
}

// 显示论文列表
function displayPapers(papers) {
    if (papers.length === 0) {
        papersTbody.innerHTML = '<tr><td colspan="8" class="no-data">暂无论文数据</td></tr>';
        return;
    }
    
    papersTbody.innerHTML = papers.map(paper => `
        <tr>
            <td><input type="checkbox" class="paper-checkbox" data-paper-id="${paper.id}"></td>
            <td>${paper.id}</td>
            <td class="title-cell" title="${paper.title}">${paper.title.length > 50 ? paper.title.substring(0, 50) + '...' : paper.title}</td>
            <td class="author-cell" title="${paper.authors || ''}">${(paper.authors || '').length > 30 ? (paper.authors || '').substring(0, 30) + '...' : (paper.authors || '')}</td>
            <td>${paper.date || '-'}</td>
            <td><span class="badge badge-primary">${paper.category || 'Uncategorized'}</span></td>
            <td>${paper.citation_count || 0}</td>
            <td>
                <button class="btn-icon" onclick="viewPaper('${paper.id}')" title="查看">
                    <svg viewBox="0 0 24 24" width="18" height="18">
                        <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                    </svg>
                </button>
                <button class="btn-icon" onclick="editPaper('${paper.id}')" title="编辑">
                    <svg viewBox="0 0 24 24" width="18" height="18">
                        <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                    </svg>
                </button>
                <button class="btn-icon btn-danger" onclick="deletePaper('${paper.id}', '${paper.title.replace(/'/g, "\\'")}')" title="删除">
                    <svg viewBox="0 0 24 24" width="18" height="18">
                        <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                    </svg>
                </button>
            </td>
        </tr>
    `).join('');
    
    // 添加复选框事件监听
    document.querySelectorAll('.paper-checkbox').forEach(checkbox => {
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
    
    if (current > 1) {
        html += `<button class="page-btn" onclick="loadPapers(${current - 1})">上一页</button>`;
    }
    
    for (let i = 1; i <= Math.min(totalPages, 10); i++) {
        if (i === current) {
            html += `<button class="page-btn active">${i}</button>`;
        } else {
            html += `<button class="page-btn" onclick="loadPapers(${i})">${i}</button>`;
        }
    }
    
    if (totalPages > 10) {
        html += '<span>...</span>';
    }
    
    if (current < totalPages) {
        html += `<button class="page-btn" onclick="loadPapers(${current + 1})">下一页</button>`;
    }
    
    html += `<span class="page-info">共 ${total} 篇论文</span>`;
    
    pagination.innerHTML = html;
}

// 查看论文详情
async function viewPaper(paperId) {
    try {
        const response = await fetch(`/api/admin/papers/${paperId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        if (data.success) {
            displayPaperDetail(data.paper);
            paperModal.style.display = 'flex';
        } else {
            showToast('获取论文详情失败', 'error');
        }
    } catch (error) {
        console.error('获取论文详情失败:', error);
        showToast('获取论文详情失败', 'error');
    }
}

// 显示论文详情
function displayPaperDetail(paper) {
    const modalBody = document.getElementById('paper-modal-body');
    modalBody.innerHTML = `
        <div class="paper-detail">
            <h4>基本信息</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <label>论文ID</label>
                    <span>${paper.id}</span>
                </div>
                <div class="detail-item full-width">
                    <label>标题</label>
                    <span>${paper.title}</span>
                </div>
                <div class="detail-item full-width">
                    <label>作者</label>
                    <span>${paper.authors || '-'}</span>
                </div>
                <div class="detail-item">
                    <label>发布日期</label>
                    <span>${paper.date || '-'}</span>
                </div>
                <div class="detail-item">
                    <label>类别</label>
                    <span class="badge badge-primary">${paper.category || 'Uncategorized'}</span>
                </div>
                <div class="detail-item">
                    <label>引用数</label>
                    <span>${paper.citation_count || 0}</span>
                </div>
                <div class="detail-item">
                    <label>高影响力引用</label>
                    <span>${paper.influential_citation_count || 0}</span>
                </div>
                <div class="detail-item">
                    <label>发表期刊/会议</label>
                    <span>${paper.venue || '-'}</span>
                </div>
                <div class="detail-item full-width">
                    <label>摘要</label>
                    <div class="abstract-text">${paper.abstract || '-'}</div>
                </div>
                <div class="detail-item full-width">
                    <label>PDF链接</label>
                    <a href="${paper.pdf_url}" target="_blank">${paper.pdf_url}</a>
                </div>
                ${paper.code_url ? `
                <div class="detail-item full-width">
                    <label>代码链接</label>
                    <a href="${paper.code_url}" target="_blank">${paper.code_url}</a>
                </div>
                ` : ''}
            </div>
        </div>
    `;
}

// 编辑论文
async function editPaper(paperId) {
    try {
        const response = await fetch(`/api/admin/papers/${paperId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        if (data.success) {
            showEditModal(data.paper);
        } else {
            showToast('获取论文信息失败', 'error');
        }
    } catch (error) {
        console.error('获取论文信息失败:', error);
        showToast('获取论文信息失败', 'error');
    }
}

// 显示编辑模态框
function showEditModal(paper) {
    document.getElementById('edit-paper-id').value = paper.id;
    document.getElementById('edit-title').value = paper.title;
    document.getElementById('edit-code-url').value = paper.code_url || '';
    
    // 填充类别选择
    const categorySelect = document.getElementById('edit-category');
    categorySelect.innerHTML = '<option value="">未分类</option>';
    categories.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat;
        option.textContent = cat;
        if (cat === paper.category) {
            option.selected = true;
        }
        categorySelect.appendChild(option);
    });
    
    editModal.style.display = 'flex';
}

// 提交编辑表单
if (editForm) {
    editForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const paperId = document.getElementById('edit-paper-id').value;
        const formData = {
            title: document.getElementById('edit-title').value,
            category: document.getElementById('edit-category').value,
            code_url: document.getElementById('edit-code-url').value
        };
        
        try {
            const response = await fetch(`/api/admin/papers/${paperId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            if (data.success) {
                showToast('论文信息更新成功', 'success');
                editModal.style.display = 'none';
                loadPapers(currentPage);
            } else {
                showToast('更新失败: ' + data.message, 'error');
            }
        } catch (error) {
            console.error('更新论文失败:', error);
            showToast('更新论文失败', 'error');
        }
    });
}

// 删除论文
async function deletePaper(paperId, paperTitle) {
    if (!confirm(`确定要删除论文"${paperTitle.substring(0, 50)}..."吗？此操作不可恢复！`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/papers/${paperId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        if (data.success) {
            showToast('论文删除成功', 'success');
            loadPapers(currentPage);
            loadStats();
        } else {
            showToast('删除失败: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('删除论文失败:', error);
        showToast('删除论文失败', 'error');
    }
}

// 搜索和筛选
if (searchBtn) {
    searchBtn.addEventListener('click', () => {
        currentFilters.search = searchInput.value.trim();
        currentFilters.category = categoryFilter.value;
        currentFilters.date_from = dateFrom.value;
        currentFilters.date_to = dateTo.value;
        currentFilters.min_citations = minCitations.value;
        loadPapers(1);
    });
}

if (resetBtn) {
    resetBtn.addEventListener('click', () => {
        searchInput.value = '';
        categoryFilter.value = '';
        dateFrom.value = '';
        dateTo.value = '';
        minCitations.value = '';
        currentFilters = { search: '', category: '', date_from: '', date_to: '', min_citations: '' };
        loadPapers(1);
    });
}

// 全选/取消全选
if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener('change', (e) => {
        const checkboxes = document.querySelectorAll('.paper-checkbox');
        checkboxes.forEach(cb => {
            cb.checked = e.target.checked;
            const paperId = cb.dataset.paperId;
            if (e.target.checked) {
                selectedPapers.add(paperId);
            } else {
                selectedPapers.delete(paperId);
            }
        });
        updateBatchButtons();
    });
}

// 处理复选框变化
function handleCheckboxChange(e) {
    const paperId = e.target.dataset.paperId;
    if (e.target.checked) {
        selectedPapers.add(paperId);
    } else {
        selectedPapers.delete(paperId);
        selectAllCheckbox.checked = false;
    }
    updateBatchButtons();
}

// 更新批量操作按钮状态（暂时不需要）
function updateBatchButtons() {
    // 批量操作功能暂时不实现
}

// 模态框关闭
document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => {
        paperModal.style.display = 'none';
        editModal.style.display = 'none';
    });
});

window.addEventListener('click', (e) => {
    if (e.target === paperModal) {
        paperModal.style.display = 'none';
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
            
            currentUserRole = data.user.role;
            
            // 检查权限
            if (data.user.role !== 'admin' && data.user.role !== 'super_admin') {
                showToast('权限不足，您不是管理员', 'error');
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
                return;
            }
            
            // 加载数据
            await loadCategories();
            await loadStats();
            loadPapers(1);
        }
    } catch (error) {
        console.error('验证身份失败:', error);
        localStorage.removeItem('auth_token');
        window.location.href = '/admin/login';
    }
});

// ==================== 论文数据更新功能 ====================

// 状态轮询相关变量
let arxivStatusPollInterval = null;
let semanticStatusPollInterval = null;

// ArXiv论文抓取
const fetchArxivBtn = document.getElementById('fetch-arxiv-btn');
const updateSemanticBtn = document.getElementById('update-semantic-btn');
const taskStatusDiv = document.getElementById('task-status');
const statusMessage = document.getElementById('status-message');
const statusProgress = document.getElementById('status-progress');
const progressFill = document.getElementById('progress-fill');

// 启动ArXiv论文抓取
async function startFetchArxiv() {
    if (fetchArxivBtn.disabled) {
        return;
    }
    
    try {
        fetchArxivBtn.disabled = true;
        // 保留SVG，只更新文本
        const svg = fetchArxivBtn.querySelector('svg');
        fetchArxivBtn.innerHTML = '';
        if (svg) fetchArxivBtn.appendChild(svg.cloneNode(true));
        fetchArxivBtn.appendChild(document.createTextNode('抓取中...'));
        taskStatusDiv.style.display = 'block';
        statusMessage.textContent = '正在启动抓取任务...';
        statusProgress.textContent = '0/0';
        progressFill.style.width = '0%';
        
        const response = await fetch('/api/admin/papers/fetch-arxiv', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('抓取任务已启动', 'success');
            startArxivStatusPolling();
        } else {
            showToast('启动失败: ' + data.message, 'error');
            resetFetchArxivButton();
            taskStatusDiv.style.display = 'none';
        }
    } catch (error) {
        console.error('启动ArXiv抓取失败:', error);
        showToast('启动抓取失败', 'error');
        resetFetchArxivButton();
        taskStatusDiv.style.display = 'none';
    }
}

// 重置ArXiv按钮
function resetFetchArxivButton() {
    fetchArxivBtn.disabled = false;
    const svg = fetchArxivBtn.querySelector('svg');
    fetchArxivBtn.innerHTML = '';
    if (svg) {
        fetchArxivBtn.appendChild(svg.cloneNode(true));
    } else {
        // 如果SVG不存在，重新创建
        const newSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        newSvg.setAttribute('viewBox', '0 0 24 24');
        newSvg.setAttribute('width', '18');
        newSvg.setAttribute('height', '18');
        newSvg.setAttribute('fill', 'currentColor');
        newSvg.innerHTML = '<path d="M19 12h-2v3h-3v2h5v-5zM7 8h3V6H5v5h2V8zm14-4H3c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 14H3V6h18v12z"/>';
        fetchArxivBtn.appendChild(newSvg);
    }
    fetchArxivBtn.appendChild(document.createTextNode(' 从ArXiv拉取新论文'));
}

// 轮询ArXiv抓取状态
function startArxivStatusPolling() {
    if (arxivStatusPollInterval) {
        clearInterval(arxivStatusPollInterval);
    }
    
    arxivStatusPollInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/admin/papers/fetch-arxiv-status', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                updateStatusDisplay(data.status, 'arxiv');
                
                if (!data.status.running) {
                    // 任务完成，停止轮询
                    clearInterval(arxivStatusPollInterval);
                    arxivStatusPollInterval = null;
                    resetFetchArxivButton();
                    
                    if (data.status.message.includes('完成') || data.status.message.includes('成功')) {
                        showToast('抓取完成！', 'success');
                        // 刷新论文列表和统计
                        await loadPapers(currentPage);
                        await loadStats();
                    } else if (data.status.message.includes('失败')) {
                        showToast('抓取失败: ' + data.status.message, 'error');
                    }
                    
                    // 延迟隐藏状态显示
                    setTimeout(() => {
                        taskStatusDiv.style.display = 'none';
                    }, 3000);
                }
            }
        } catch (error) {
            console.error('获取ArXiv抓取状态失败:', error);
        }
    }, 2000); // 每2秒查询一次
}

// 启动Semantic Scholar更新
async function startUpdateSemantic() {
    if (updateSemanticBtn.disabled) {
        return;
    }
    
    try {
        updateSemanticBtn.disabled = true;
        // 保留SVG，只更新文本
        const svg = updateSemanticBtn.querySelector('svg');
        updateSemanticBtn.innerHTML = '';
        if (svg) updateSemanticBtn.appendChild(svg.cloneNode(true));
        updateSemanticBtn.appendChild(document.createTextNode('更新中...'));
        taskStatusDiv.style.display = 'block';
        statusMessage.textContent = '正在启动更新任务...';
        statusProgress.textContent = '0/0';
        progressFill.style.width = '0%';
        
        const response = await fetch('/api/admin/papers/update-semantic', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                skip_existing: true
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('更新任务已启动', 'success');
            startSemanticStatusPolling();
        } else {
            showToast('启动失败: ' + data.message, 'error');
            resetUpdateSemanticButton();
            taskStatusDiv.style.display = 'none';
        }
    } catch (error) {
        console.error('启动Semantic Scholar更新失败:', error);
        showToast('启动更新失败', 'error');
        resetUpdateSemanticButton();
        taskStatusDiv.style.display = 'none';
    }
}

// 重置Semantic Scholar按钮
function resetUpdateSemanticButton() {
    updateSemanticBtn.disabled = false;
    const svg = updateSemanticBtn.querySelector('svg');
    updateSemanticBtn.innerHTML = '';
    if (svg) {
        updateSemanticBtn.appendChild(svg.cloneNode(true));
    } else {
        // 如果SVG不存在，重新创建
        const newSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        newSvg.setAttribute('viewBox', '0 0 24 24');
        newSvg.setAttribute('width', '18');
        newSvg.setAttribute('height', '18');
        newSvg.setAttribute('fill', 'currentColor');
        newSvg.innerHTML = '<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>';
        updateSemanticBtn.appendChild(newSvg);
    }
    updateSemanticBtn.appendChild(document.createTextNode(' 更新Semantic Scholar数据'));
}

// 轮询Semantic Scholar更新状态
function startSemanticStatusPolling() {
    if (semanticStatusPollInterval) {
        clearInterval(semanticStatusPollInterval);
    }
    
    semanticStatusPollInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/admin/papers/update-semantic-status', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                updateStatusDisplay(data.status, 'semantic');
                
                if (!data.status.running) {
                    // 任务完成，停止轮询
                    clearInterval(semanticStatusPollInterval);
                    semanticStatusPollInterval = null;
                    resetUpdateSemanticButton();
                    
                    if (data.status.message.includes('完成') || data.status.message.includes('成功')) {
                        showToast('更新完成！', 'success');
                        // 刷新论文列表和统计
                        await loadPapers(currentPage);
                        await loadStats();
                    } else if (data.status.message.includes('失败')) {
                        showToast('更新失败: ' + data.status.message, 'error');
                    }
                    
                    // 延迟隐藏状态显示
                    setTimeout(() => {
                        taskStatusDiv.style.display = 'none';
                    }, 3000);
                }
            }
        } catch (error) {
            console.error('获取Semantic Scholar更新状态失败:', error);
        }
    }, 2000); // 每2秒查询一次
}

// 更新状态显示
function updateStatusDisplay(status, type) {
    if (!status) return;
    
    statusMessage.textContent = status.message || '处理中...';
    
    const total = status.total || 0;
    const progress = status.progress || 0;
    
    if (total > 0) {
        statusProgress.textContent = `${progress}/${total}`;
        const percentage = Math.min((progress / total) * 100, 100);
        progressFill.style.width = `${percentage}%`;
    } else {
        statusProgress.textContent = '0/0';
        progressFill.style.width = '0%';
    }
}

// 绑定按钮事件
if (fetchArxivBtn) {
    fetchArxivBtn.addEventListener('click', startFetchArxiv);
}

if (updateSemanticBtn) {
    updateSemanticBtn.addEventListener('click', startUpdateSemantic);
}

// 全局函数（供onclick使用）
window.viewPaper = viewPaper;
window.editPaper = editPaper;
window.deletePaper = deletePaper;
window.loadPapers = loadPapers;

