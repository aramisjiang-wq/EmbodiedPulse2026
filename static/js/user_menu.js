/**
 * 用户认证和导航栏管理
 * 功能：强制登录检测 + 用户按钮状态更新
 */

// 获取当前页面路径
const currentPath = window.location.pathname;

// 不需要强制登录的页面（白名单）
const publicPages = ['/login', '/auth/callback', '/admin/login', '/test', '/bilibili'];

// 检查是否是公开页面
function isPublicPage() {
    return publicPages.some(page => currentPath.startsWith(page));
}

// 从URL参数中提取并保存token（如果存在）
function extractAndSaveTokenFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    if (token) {
        console.log('✅ 从URL参数中提取到token，正在保存...');
        localStorage.setItem('auth_token', token);
        
        // 清除URL中的token参数（安全考虑）
        const cleanUrl = window.location.pathname + 
            (urlParams.toString().replace(/token=[^&]+&?/, '').replace(/&$/, '') ? 
             '?' + urlParams.toString().replace(/token=[^&]+&?/, '').replace(/&$/, '') : 
             '');
        window.history.replaceState({}, '', cleanUrl);
        
        console.log('✅ Token已保存并清除URL参数');
        return true;
    }
    
    return false;
}

// 强制登录检测
async function checkAuthRequired() {
    // 如果是公开页面，不需要检测
    if (isPublicPage()) {
        return true;
    }
    
    // 先从URL参数中提取token（如果有）
    extractAndSaveTokenFromUrl();
    
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
        // 未登录，保存当前页面，跳转到登录页
        console.log('未登录，跳转到登录页');
        localStorage.setItem('redirect_after_login', currentPath + window.location.search);
        window.location.href = '/login';
        return false;
    }
    
    // 验证token是否有效
    try {
        const response = await fetch('/api/user/profile', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            // Token无效，清除并跳转登录
            console.log('Token无效，跳转到登录页');
            localStorage.removeItem('auth_token');
            localStorage.setItem('redirect_after_login', currentPath + window.location.search);
            window.location.href = '/login';
            return false;
        }
        
        return true;
    } catch (error) {
        console.error('验证登录失败:', error);
        return true; // 网络错误时不阻止访问
    }
}

// 更新导航栏用户按钮
async function updateUserButton() {
    const loginBtn = document.getElementById('userLoginBtn');
    const profileBtn = document.getElementById('userProfileBtn');
    const userNameText = document.getElementById('userNameText');
    
    if (!loginBtn || !profileBtn) {
        return; // 页面上没有这些元素
    }
    
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
        // 未登录状态
        loginBtn.style.display = 'flex';
        profileBtn.style.display = 'none';
        return;
    }
    
    try {
        // 获取用户信息
        const response = await fetch('/api/user/profile', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.user) {
                // 已登录，显示用户名
                if (userNameText) {
                    userNameText.textContent = data.user.name || '用户';
                }
                loginBtn.style.display = 'none';
                profileBtn.style.display = 'flex';
            } else {
                // 数据格式错误
                loginBtn.style.display = 'flex';
                profileBtn.style.display = 'none';
            }
        } else {
            // Token无效
            localStorage.removeItem('auth_token');
            loginBtn.style.display = 'flex';
            profileBtn.style.display = 'none';
        }
    } catch (error) {
        console.error('获取用户信息失败:', error);
        // 网络错误，显示登录按钮
        loginBtn.style.display = 'flex';
        profileBtn.style.display = 'none';
    }
}

// 页面加载时执行
document.addEventListener('DOMContentLoaded', async function() {
    // 1. 先执行强制登录检测
    const isAuthenticated = await checkAuthRequired();
    
    // 2. 如果通过验证，更新导航栏按钮
    if (isAuthenticated) {
        updateUserButton();
    }
});

