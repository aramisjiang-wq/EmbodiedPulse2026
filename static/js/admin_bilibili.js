/**
 * 视频管理页面逻辑
 */

// 全局变量
const token = localStorage.getItem('auth_token');
let currentTab = 'ups'; // 'ups' 或 'videos'
let currentPage = 1;
let perPage = 20;
let currentFilters = {
    search: '',
    uid: '',
    date_from: '',
    date_to: '',
    min_play: ''
};
let selectedUps = new Set();
let selectedVideos = new Set();
let currentUserRole = '';
let upsList = [];

// 检查登录状态
if (!token) {
    window.location.href = '/admin/login';
}

// DOM元素
const adminUserName = document.getElementById('admin-user-name');
const logoutBtn = document.getElementById('logout-btn');
const tabBtns = document.querySelectorAll('.tab-btn');
const searchInput = document.getElementById('search-input');
const upFilter = document.getElementById('up-filter');
const dateFrom = document.getElementById('date-from');
const dateTo = document.getElementById('date-to');
const minPlay = document.getElementById('min-play');
const searchBtn = document.getElementById('search-btn');
const resetBtn = document.getElementById('reset-btn');
const selectAllUps = document.getElementById('select-all-ups');
const selectAllVideos = document.getElementById('select-all-videos');
const upsTbody = document.getElementById('ups-tbody');
const videosTbody = document.getElementById('videos-tbody');
const upsSection = document.getElementById('ups-section');
const videosSection = document.getElementById('videos-section');
const upsPagination = document.getElementById('ups-pagination');
const videosPagination = document.getElementById('videos-pagination');
const upModal = document.getElementById('up-modal');
const videoModal = document.getElementById('video-modal');
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
    currentPage = 1;
    
    // 更新Tab按钮状态
    tabBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    
    // 显示/隐藏对应的section
    if (tab === 'ups') {
        upsSection.style.display = 'block';
        videosSection.style.display = 'none';
        upFilter.style.display = 'none';
        minPlay.style.display = 'none';
        loadUps(1);
    } else {
        upsSection.style.display = 'none';
        videosSection.style.display = 'block';
        upFilter.style.display = 'inline-block';
        minPlay.style.display = 'inline-block';
        loadVideos(1);
    }
}

// 加载系统配置信息
async function loadConfig() {
    try {
        const response = await fetch('/api/admin/bilibili/config', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                const config = data.config;
                const configInfo = document.getElementById('config-info');
                
                let html = '';
                
                // 服务器信息
                html += `
                    <div style="background: white; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0;">
                        <div style="font-weight: 600; color: #4a5568; margin-bottom: 8px;">
                            <i class="fas fa-server" style="margin-right: 6px;"></i>服务器信息
                        </div>
                        <div style="color: #718096; font-size: 12px; line-height: 1.8;">
                            <div><strong>IP地址:</strong> <code style="background: #f7fafc; padding: 2px 6px; border-radius: 3px;">${config.server.ip}</code></div>
                            <div><strong>端口号:</strong> <code style="background: #f7fafc; padding: 2px 6px; border-radius: 3px;">${config.server.port}</code></div>
                            <div><strong>主机名:</strong> <code style="background: #f7fafc; padding: 2px 6px; border-radius: 3px;">${config.server.hostname}</code></div>
                        </div>
                    </div>
                `;
                
                // 数据库信息
                html += `
                    <div style="background: white; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0;">
                        <div style="font-weight: 600; color: #4a5568; margin-bottom: 8px;">
                            <i class="fas fa-database" style="margin-right: 6px;"></i>数据库信息
                        </div>
                        <div style="color: #718096; font-size: 12px; line-height: 1.8;">
                            <div><strong>类型:</strong> <code style="background: #f7fafc; padding: 2px 6px; border-radius: 3px;">${config.database.type}</code></div>
                            <div><strong>主机:</strong> <code style="background: #f7fafc; padding: 2px 6px; border-radius: 3px;">${config.database.host}</code></div>
                            ${config.database.port !== '未知' ? `<div><strong>端口:</strong> <code style="background: #f7fafc; padding: 2px 6px; border-radius: 3px;">${config.database.port}</code></div>` : ''}
                            <div><strong>数据库名:</strong> <code style="background: #f7fafc; padding: 2px 6px; border-radius: 3px;">${config.database.name}</code></div>
                            <div><strong>用户名:</strong> <code style="background: #f7fafc; padding: 2px 6px; border-radius: 3px;">${config.database.user}</code></div>
                            <div><strong>密码:</strong> <code style="background: #f7fafc; padding: 2px 6px; border-radius: 3px;">${config.database.password}</code></div>
                            ${config.database.file_path ? `<div><strong>文件路径:</strong> <code style="background: #f7fafc; padding: 2px 6px; border-radius: 3px; font-size: 11px;">${config.database.file_path}</code></div>` : ''}
                            ${config.database.file_size ? `<div><strong>文件大小:</strong> <code style="background: #f7fafc; padding: 2px 6px; border-radius: 3px;">${config.database.file_size}</code></div>` : ''}
                            <div><strong>连接状态:</strong> <span style="color: ${config.database.connection_status.includes('✅') ? '#10b981' : '#ef4444'};">${config.database.connection_status}</span></div>
                        </div>
                    </div>
                `;
                
                configInfo.innerHTML = html;
            }
        }
    } catch (error) {
        console.error('加载配置信息失败:', error);
        const configInfo = document.getElementById('config-info');
        if (configInfo) {
            configInfo.innerHTML = '<div style="color: #ef4444;">加载配置信息失败</div>';
        }
    }
}

// 加载统计信息
async function loadStats() {
    try {
        const response = await fetch('/api/admin/bilibili/stats', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                document.getElementById('stat-total-ups').textContent = data.stats.total_ups || 0;
                document.getElementById('stat-total-videos').textContent = data.stats.total_videos || 0;
                document.getElementById('stat-total-plays').textContent = formatNumber(data.stats.total_plays || 0);
                document.getElementById('stat-today-videos').textContent = data.stats.today_videos || 0;
            }
        }
    } catch (error) {
        console.error('加载统计信息失败:', error);
    }
}

// 加载UP主列表
async function loadUps(page = 1) {
    try {
        currentPage = page;
        const params = new URLSearchParams({
            page: page,
            per_page: perPage,
            search: currentFilters.search,
            is_active: ''
        });
        
        const response = await fetch(`/api/admin/bilibili/ups?${params}`, {
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
            throw new Error('获取UP主列表失败');
        }
        
        const data = await response.json();
        if (data.success) {
            displayUps(data.ups);
            displayPagination(upsPagination, data.pagination.current_page, data.pagination.total, data.pagination.per_page, 'loadUps');
            upsList = data.ups;
            updateUpFilter();
        } else {
            showToast('获取UP主列表失败: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('加载UP主列表失败:', error);
        showToast('加载UP主列表失败', 'error');
    }
}

// 显示UP主列表
function displayUps(ups) {
    if (ups.length === 0) {
        upsTbody.innerHTML = '<tr><td colspan="8" class="no-data">暂无UP主数据</td></tr>';
        return;
    }
    
    upsTbody.innerHTML = ups.map(up => `
        <tr>
            <td><input type="checkbox" class="up-checkbox" data-up-id="${up.uid}"></td>
            <td>${up.uid}</td>
            <td>${up.name}</td>
            <td>${up.fans_formatted || formatNumber(up.fans || 0)}</td>
            <td>${up.videos_count || 0}</td>
            <td>${up.views_formatted || formatNumber(up.views_count || 0)}</td>
            <td>${formatDateTime(up.last_fetch_at)}</td>
            <td>
                <button class="btn-icon" onclick="viewUp(${up.uid})" title="查看">
                    <svg viewBox="0 0 24 24" width="18" height="18">
                        <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                    </svg>
                </button>
            </td>
        </tr>
    `).join('');
    
    // 添加复选框事件监听
    document.querySelectorAll('.up-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', handleUpCheckboxChange);
    });
}

// 加载视频列表
async function loadVideos(page = 1) {
    try {
        currentPage = page;
        const params = new URLSearchParams({
            page: page,
            per_page: perPage,
            search: currentFilters.search,
            uid: currentFilters.uid,
            date_from: currentFilters.date_from,
            date_to: currentFilters.date_to,
            min_play: currentFilters.min_play
        });
        
        const response = await fetch(`/api/admin/bilibili/videos?${params}`, {
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
            throw new Error('获取视频列表失败');
        }
        
        const data = await response.json();
        if (data.success) {
            displayVideos(data.videos);
            displayPagination(videosPagination, data.pagination.current_page, data.pagination.total, data.pagination.per_page, 'loadVideos');
        } else {
            showToast('获取视频列表失败: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('加载视频列表失败:', error);
        showToast('加载视频列表失败', 'error');
    }
}

// 显示视频列表
function displayVideos(videos) {
    if (videos.length === 0) {
        videosTbody.innerHTML = '<tr><td colspan="9" class="no-data">暂无视频数据</td></tr>';
        return;
    }
    
    videosTbody.innerHTML = videos.map(video => `
        <tr>
            <td><input type="checkbox" class="video-checkbox" data-video-id="${video.bvid}"></td>
            <td>${video.bvid}</td>
            <td class="title-cell" title="${video.title}">${video.title.length > 40 ? video.title.substring(0, 40) + '...' : video.title}</td>
            <td>${video.up_name || '-'}</td>
            <td>${formatDateTime(video.pubdate)}</td>
            <td>${video.play_formatted || formatNumber(video.play || 0)}</td>
            <td>${video.video_review_formatted || formatNumber(video.video_review || 0)}</td>
            <td>${video.favorites_formatted || formatNumber(video.favorites || 0)}</td>
            <td>
                <button class="btn-icon" onclick="viewVideo('${video.bvid}')" title="查看">
                    <svg viewBox="0 0 24 24" width="18" height="18">
                        <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                    </svg>
                </button>
            </td>
        </tr>
    `).join('');
    
    // 添加复选框事件监听
    document.querySelectorAll('.video-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', handleVideoCheckboxChange);
    });
}

// 显示分页
function displayPagination(paginationEl, current, total, per_page, loadFunc) {
    if (!paginationEl) return;
    
    const totalPages = Math.ceil(total / per_page);
    
    if (totalPages <= 1) {
        paginationEl.innerHTML = '';
        return;
    }
    
    let html = '';
    
    if (current > 1) {
        html += `<button class="page-btn" onclick="${loadFunc}(${current - 1})">上一页</button>`;
    }
    
    for (let i = 1; i <= Math.min(totalPages, 10); i++) {
        if (i === current) {
            html += `<button class="page-btn active">${i}</button>`;
        } else {
            html += `<button class="page-btn" onclick="${loadFunc}(${i})">${i}</button>`;
        }
    }
    
    if (totalPages > 10) {
        html += '<span>...</span>';
    }
    
    if (current < totalPages) {
        html += `<button class="page-btn" onclick="${loadFunc}(${current + 1})">下一页</button>`;
    }
    
    html += `<span class="page-info">共 ${total} ${currentTab === 'ups' ? '个UP主' : '个视频'}</span>`;
    
    paginationEl.innerHTML = html;
}

// 更新UP主筛选下拉框
function updateUpFilter() {
    upFilter.innerHTML = '<option value="">全部UP主</option>';
    upsList.forEach(up => {
        const option = document.createElement('option');
        option.value = up.uid;
        option.textContent = up.name;
        upFilter.appendChild(option);
    });
}

// 查看UP主详情
async function viewUp(uid) {
    try {
        const response = await fetch(`/api/admin/bilibili/ups/${uid}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        if (data.success) {
            displayUpDetail(data.up);
            upModal.style.display = 'flex';
        } else {
            showToast('获取UP主详情失败', 'error');
        }
    } catch (error) {
        console.error('获取UP主详情失败:', error);
        showToast('获取UP主详情失败', 'error');
    }
}

// 显示UP主详情
function displayUpDetail(up) {
    const modalBody = document.getElementById('up-modal-body');
    modalBody.innerHTML = `
        <div class="up-detail">
            <h4>基本信息</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <label>UID</label>
                    <span>${up.uid}</span>
                </div>
                <div class="detail-item">
                    <label>名称</label>
                    <span>${up.name}</span>
                </div>
                <div class="detail-item">
                    <label>粉丝数</label>
                    <span>${up.fans_formatted || formatNumber(up.fans || 0)}</span>
                </div>
                <div class="detail-item">
                    <label>视频数</label>
                    <span>${up.videos_count || 0}</span>
                </div>
                <div class="detail-item">
                    <label>总播放量</label>
                    <span>${up.views_formatted || formatNumber(up.views_count || 0)}</span>
                </div>
                <div class="detail-item">
                    <label>获赞数</label>
                    <span>${up.likes_formatted || formatNumber(up.likes_count || 0)}</span>
                </div>
                <div class="detail-item">
                    <label>最后更新</label>
                    <span>${formatDateTime(up.last_fetch_at)}</span>
                </div>
            </div>
        </div>
    `;
}

// 查看视频详情
async function viewVideo(bvid) {
    try {
        const response = await fetch(`/api/admin/bilibili/videos/${bvid}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        if (data.success) {
            displayVideoDetail(data.video);
            videoModal.style.display = 'flex';
        } else {
            showToast('获取视频详情失败', 'error');
        }
    } catch (error) {
        console.error('获取视频详情失败:', error);
        showToast('获取视频详情失败', 'error');
    }
}

// 显示视频详情
function displayVideoDetail(video) {
    const modalBody = document.getElementById('video-modal-body');
    modalBody.innerHTML = `
        <div class="video-detail">
            <h4>基本信息</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <label>BV号</label>
                    <span>${video.bvid}</span>
                </div>
                <div class="detail-item full-width">
                    <label>标题</label>
                    <span>${video.title}</span>
                </div>
                <div class="detail-item">
                    <label>UP主</label>
                    <span>${video.up_name || '-'}</span>
                </div>
                <div class="detail-item">
                    <label>发布时间</label>
                    <span>${formatDateTime(video.pubdate)}</span>
                </div>
                <div class="detail-item">
                    <label>播放量</label>
                    <span>${video.play_formatted || formatNumber(video.play || 0)}</span>
                </div>
                <div class="detail-item">
                    <label>评论数</label>
                    <span>${video.video_review_formatted || formatNumber(video.video_review || 0)}</span>
                </div>
                <div class="detail-item">
                    <label>收藏数</label>
                    <span>${video.favorites_formatted || formatNumber(video.favorites || 0)}</span>
                </div>
                <div class="detail-item full-width">
                    <label>视频链接</label>
                    <a href="${video.url}" target="_blank">${video.url}</a>
                </div>
            </div>
        </div>
    `;
}

// 搜索和筛选
if (searchBtn) {
    searchBtn.addEventListener('click', () => {
        currentFilters.search = searchInput.value.trim();
        if (currentTab === 'videos') {
            currentFilters.uid = upFilter.value;
            currentFilters.date_from = dateFrom.value;
            currentFilters.date_to = dateTo.value;
            currentFilters.min_play = minPlay.value;
        }
        if (currentTab === 'ups') {
            loadUps(1);
        } else {
            loadVideos(1);
        }
    });
}

if (resetBtn) {
    resetBtn.addEventListener('click', () => {
        searchInput.value = '';
        upFilter.value = '';
        dateFrom.value = '';
        dateTo.value = '';
        minPlay.value = '';
        currentFilters = { search: '', uid: '', date_from: '', date_to: '', min_play: '' };
        if (currentTab === 'ups') {
            loadUps(1);
        } else {
            loadVideos(1);
        }
    });
}

// 复选框处理
function handleUpCheckboxChange(e) {
    const uid = e.target.dataset.upId;
    if (e.target.checked) {
        selectedUps.add(uid);
    } else {
        selectedUps.delete(uid);
        selectAllUps.checked = false;
    }
    updateBatchButtons();
}

function handleVideoCheckboxChange(e) {
    const bvid = e.target.dataset.videoId;
    if (e.target.checked) {
        selectedVideos.add(bvid);
    } else {
        selectedVideos.delete(bvid);
        selectAllVideos.checked = false;
    }
    updateBatchButtons();
}

function updateBatchButtons() {
    // 批量操作功能暂时不实现
}

// 模态框关闭
document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => {
        upModal.style.display = 'none';
        videoModal.style.display = 'none';
    });
});

window.addEventListener('click', (e) => {
    if (e.target === upModal) {
        upModal.style.display = 'none';
    }
    if (e.target === videoModal) {
        videoModal.style.display = 'none';
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

function formatNumber(num) {
    if (num >= 100000000) {
        return (num / 100000000).toFixed(1) + '亿';
    } else if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万';
    }
    return num.toString();
}

function showToast(message, type = 'info') {
    if (!toast) return;
    
    toast.textContent = message;
    toast.className = `toast toast-${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// 触发B站数据更新
async function triggerFetchBilibiliData() {
    const fetchBtn = document.getElementById('fetch-bilibili-btn');
    const statusDiv = document.getElementById('fetch-task-status');
    const messageSpan = document.getElementById('fetch-task-message');
    const progressSpan = document.getElementById('fetch-task-progress');
    const progressBar = document.getElementById('fetch-task-progress-bar');
    
    if (!fetchBtn) return;
    
    // 禁用按钮
    fetchBtn.disabled = true;
    fetchBtn.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" style="animation: spin 1s linear infinite;"><path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/></svg> 更新中...';
    
    // 显示状态区域
    statusDiv.style.display = 'block';
    messageSpan.textContent = '正在启动更新任务...';
    progressSpan.textContent = '0%';
    progressBar.style.width = '0%';
    
    try {
        const response = await fetch('/api/admin/bilibili/fetch-data', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                update_play_counts: true,
                video_count: 50
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('数据更新任务已启动', 'success');
            // 开始轮询状态
            pollFetchStatus();
        } else {
            showToast('启动更新任务失败: ' + data.message, 'error');
            fetchBtn.disabled = false;
            fetchBtn.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M19 12h-2v3h-3v2h5v-5zM7 8h3V6H5v5h2V8zm14-4H3c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 14H3V6h18v12z"/></svg> 更新B站数据';
            statusDiv.style.display = 'none';
        }
    } catch (error) {
        console.error('触发更新失败:', error);
        showToast('触发更新失败', 'error');
        fetchBtn.disabled = false;
        fetchBtn.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M19 12h-2v3h-3v2h5v-5zM7 8h3V6H5v5h2V8zm14-4H3c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 14H3V6h18v12z"/></svg> 更新B站数据';
        statusDiv.style.display = 'none';
    }
}

// 轮询更新状态
let statusPollInterval = null;
function pollFetchStatus() {
    // 清除之前的轮询
    if (statusPollInterval) {
        clearInterval(statusPollInterval);
    }
    
    const messageSpan = document.getElementById('fetch-task-message');
    const progressSpan = document.getElementById('fetch-task-progress');
    const progressBar = document.getElementById('fetch-task-progress-bar');
    const fetchBtn = document.getElementById('fetch-bilibili-btn');
    const statusDiv = document.getElementById('fetch-task-status');
    
    // 立即查询一次
    checkFetchStatus();
    
    // 每2秒查询一次
    statusPollInterval = setInterval(() => {
        checkFetchStatus();
    }, 2000);
    
    function checkFetchStatus() {
        fetch('/api/admin/bilibili/fetch-status', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.status) {
                const status = data.status;
                
                // 更新状态显示
                messageSpan.textContent = status.message || '处理中...';
                const progress = status.progress || 0;
                progressSpan.textContent = `${progress}%`;
                progressBar.style.width = `${progress}%`;
                
                // 如果任务完成，停止轮询并刷新数据
                if (!status.running) {
                    clearInterval(statusPollInterval);
                    statusPollInterval = null;
                    
                    // 恢复按钮
                    fetchBtn.disabled = false;
                    fetchBtn.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M19 12h-2v3h-3v2h5v-5zM7 8h3V6H5v5h2V8zm14-4H3c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 14H3V6h18v12z"/></svg> 更新B站数据';
                    
                    // 3秒后隐藏状态区域
                    setTimeout(() => {
                        statusDiv.style.display = 'none';
                    }, 3000);
                    
                    // 刷新统计数据
                    loadStats();
                    
                    // 刷新当前列表
                    if (currentTab === 'ups') {
                        loadUps(currentPage);
                    } else {
                        loadVideos(currentPage);
                    }
                    
                    showToast('数据更新完成！', 'success');
                }
            }
        })
        .catch(error => {
            console.error('查询状态失败:', error);
        });
    }
}

// 页面加载时执行
document.addEventListener('DOMContentLoaded', async () => {
    // 刷新配置按钮
    const refreshConfigBtn = document.getElementById('refresh-config-btn');
    if (refreshConfigBtn) {
        refreshConfigBtn.addEventListener('click', () => {
            loadConfig();
        });
    }
    
    // 更新B站数据按钮
    const fetchBilibiliBtn = document.getElementById('fetch-bilibili-btn');
    if (fetchBilibiliBtn) {
        fetchBilibiliBtn.addEventListener('click', () => {
            if (!confirm('确定要更新B站数据吗？这将更新UP主信息、视频列表和播放量数据。')) {
                return;
            }
            triggerFetchBilibiliData();
        });
    }
    
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
            await loadConfig();
            await loadStats();
            loadUps(1);
            
            // 检查是否有正在运行的任务
            checkInitialFetchStatus();
        }
    } catch (error) {
        console.error('验证身份失败:', error);
        localStorage.removeItem('auth_token');
        window.location.href = '/admin/login';
    }
});

// 检查初始状态（页面加载时）
async function checkInitialFetchStatus() {
    try {
        const response = await fetch('/api/admin/bilibili/fetch-status', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        if (data.success && data.status && data.status.running) {
            // 如果有正在运行的任务，开始轮询
            const fetchBtn = document.getElementById('fetch-bilibili-btn');
            const statusDiv = document.getElementById('fetch-task-status');
            if (fetchBtn && statusDiv) {
                fetchBtn.disabled = true;
                fetchBtn.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" style="animation: spin 1s linear infinite;"><path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/></svg> 更新中...';
                statusDiv.style.display = 'block';
                pollFetchStatus();
            }
        }
    } catch (error) {
        console.error('检查初始状态失败:', error);
    }
}

// 全局函数（供onclick使用）
window.viewUp = viewUp;
window.viewVideo = viewVideo;
window.loadUps = loadUps;
window.loadVideos = loadVideos;

