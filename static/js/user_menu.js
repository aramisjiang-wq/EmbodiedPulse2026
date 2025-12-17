/**
 * 用户菜单 - 全局用户登录状态和菜单
 */

// 检查用户登录状态并更新UI
async function checkUserLoginStatus() {
    const token = localStorage.getItem('auth_token');
    const loginBtn = document.getElementById('loginBtn');
    const userProfile = document.getElementById('userProfile');
    const userName = document.getElementById('userName');
    const userAvatar = document.getElementById('userAvatar');
    const adminLink = document.getElementById('adminLink');
    
    if (!token) {
        // 未登录
        if (loginBtn) loginBtn.style.display = 'flex';
        if (userProfile) userProfile.style.display = 'none';
        return;
    }
    
    try {
        // 验证token并获取用户信息
        const response = await fetch('/api/user/profile', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            // Token无效，清除并显示登录按钮
            localStorage.removeItem('auth_token');
            if (loginBtn) loginBtn.style.display = 'flex';
            if (userProfile) userProfile.style.display = 'none';
            return;
        }
        
        const data = await response.json();
        
        if (data.success && data.user) {
            // 已登录，显示用户信息
            if (loginBtn) loginBtn.style.display = 'none';
            if (userProfile) userProfile.style.display = 'flex';
            if (userName) userName.textContent = data.user.name || '用户';
            
            // 如果有头像，显示头像
            if (data.user.avatar_url && userAvatar) {
                userAvatar.innerHTML = `<img src="${data.user.avatar_url}" alt="${data.user.name}">`;
            }
            
            // 如果是管理员，显示管理后台链接
            if (adminLink && (data.user.role === 'admin' || data.user.role === 'super_admin')) {
                adminLink.style.display = 'flex';
            }
        } else {
            // 数据格式错误
            localStorage.removeItem('auth_token');
            if (loginBtn) loginBtn.style.display = 'flex';
            if (userProfile) userProfile.style.display = 'none';
        }
    } catch (error) {
        console.error('检查登录状态失败:', error);
        // 网络错误，保持当前状态（不清除token）
    }
}

// 退出登录
async function handleLogout() {
    const token = localStorage.getItem('auth_token');
    
    if (token) {
        try {
            // 调用退出API
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
        } catch (error) {
            console.error('退出登录失败:', error);
        }
    }
    
    // 清除token
    localStorage.removeItem('auth_token');
    
    // 刷新页面
    window.location.reload();
}

// 用户头像点击事件（显示/隐藏下拉菜单）
function toggleUserDropdown(event) {
    event.stopPropagation();
    const userProfile = document.getElementById('userProfile');
    if (userProfile) {
        userProfile.classList.toggle('active');
    }
}

// 点击页面其他地方关闭下拉菜单
document.addEventListener('click', function(event) {
    const userProfile = document.getElementById('userProfile');
    const userAvatar = document.getElementById('userAvatar');
    
    if (userProfile && userAvatar) {
        if (!userProfile.contains(event.target) && !userAvatar.contains(event.target)) {
            userProfile.classList.remove('active');
        }
    }
});

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    // 检查登录状态
    checkUserLoginStatus();
    
    // 绑定退出登录按钮
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    // 绑定用户头像点击事件
    const userAvatar = document.getElementById('userAvatar');
    if (userAvatar) {
        userAvatar.addEventListener('click', toggleUserDropdown);
    }
});

