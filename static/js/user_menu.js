/**
 * 用户认证和导航栏管理
 * 功能：强制登录检测 + 用户按钮状态更新
 */

// 获取当前页面路径
const currentPath = window.location.pathname;

// 不需要强制登录的页面（白名单）
const publicPages = ['/login', '/auth/callback', '/admin/login', '/test'];

// 检查是否是公开页面
function isPublicPage() {
    return publicPages.some(page => currentPath.startsWith(page));
}

// 从URL参数中提取并保存token（如果存在）
function extractAndSaveTokenFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    if (token) {
        console.log('✅ 从URL参数中提取到token，正在保存到当前域名:', window.location.hostname);
        try {
            localStorage.setItem('auth_token', token);
            
            // ✅ 修复：验证保存是否成功
            const savedToken = localStorage.getItem('auth_token');
            if (savedToken !== token) {
                console.error('❌ Token保存失败！');
                return false;
            }
            
            // 清除URL中的token参数（安全考虑）
            urlParams.delete('token');
            const cleanUrl = window.location.pathname + (urlParams.toString() ? '?' + urlParams.toString() : '');
            window.history.replaceState({}, '', cleanUrl);
            
            console.log('✅ Token已保存到', window.location.hostname, '并清除URL参数');
            return true;
        } catch (e) {
            console.error('❌ 保存token失败:', e);
            return false;
        }
    }
    
    return false;
}

// 强制登录检测
async function checkAuthRequired() {
    // 如果是公开页面，不需要检测
    if (isPublicPage()) {
        return true;
    }
    
    // ✅ 修复：先提取并保存token，确保完成后再读取
    const hasTokenInUrl = extractAndSaveTokenFromUrl();
    
    // ✅ 修复：如果从URL提取到token，等待一小段时间确保保存完成
    if (hasTokenInUrl) {
        await new Promise(resolve => setTimeout(resolve, 100)); // 等待100ms
    }
    
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
        // 未登录，保存当前页面和域名，跳转到登录页
        console.log('未登录，跳转到登录页');
        localStorage.setItem('redirect_after_login', currentPath + window.location.search);
        // 保存当前域名，以便登录后跳转回来
        if (window.location.hostname !== 'login.gradmotion.com') {
            localStorage.setItem('original_host', window.location.hostname);
        }
        window.location.href = '/login';
        return false;
    }
    
    // 验证token是否有效
    try {
        // ✅ 修复：增加超时控制，避免长时间等待
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5秒超时
        
        const response = await fetch('/api/auth/user-info', {
            headers: {
                'Authorization': `Bearer ${token}`
            },
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            // ✅ 修复：区分不同类型的错误
            if (response.status === 401) {
                // Token无效（401），清除并跳转登录
                console.log('Token无效（401），跳转到登录页');
                localStorage.removeItem('auth_token');
                localStorage.setItem('redirect_after_login', currentPath + window.location.search);
                // 保存当前域名
                if (window.location.hostname !== 'login.gradmotion.com') {
                    localStorage.setItem('original_host', window.location.hostname);
                }
                window.location.href = '/login';
                return false;
            } else {
                // ✅ 修复：其他错误（如500）不立即跳转，可能是服务器问题
                console.warn('Token验证失败，但可能是服务器问题（状态码:', response.status, '），允许继续访问');
                // 允许继续访问，避免循环跳转
                return true;
            }
        }
        
        return true;
    } catch (error) {
        // ✅ 修复：网络错误时，不立即跳转，可能是临时网络问题
        if (error.name === 'AbortError') {
            console.warn('Token验证超时，可能是网络问题，允许继续访问，避免循环跳转');
            return true; // 允许访问，避免循环
        }
        
        console.error('验证登录失败:', error);
        // ✅ 修复：只有确认是认证错误时才跳转
        // 网络错误时允许继续访问，避免循环跳转
        console.warn('网络错误，但不跳转，避免循环跳转。错误类型:', error.name);
        return true; // 允许访问，避免循环
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
        const response = await fetch('/api/auth/user-info', {
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

// 立即执行登录检查（不等待 DOMContentLoaded）
(function() {
    // 立即执行，不等待任何事件
    (async function initAuth() {
        // 0. 首先从URL参数中提取token（如果有，说明是从登录回调跳转过来的）
        // 这必须在 checkAuthRequired 之前执行，因为 token 可能通过 URL 参数传递
        const hasTokenInUrl = extractAndSaveTokenFromUrl();
        
        if (hasTokenInUrl) {
            console.log('✅ 从URL参数中提取到token，已保存到当前域名的localStorage');
            // ✅ 修复：等待一小段时间确保保存完成
            await new Promise(resolve => setTimeout(resolve, 50));
        }
        
        // ✅ 修复：验证token是否已保存
        const token = localStorage.getItem('auth_token');
        if (!token && hasTokenInUrl) {
            console.error('❌ Token提取失败，但URL中有token参数，重试一次');
            // 重试一次
            extractAndSaveTokenFromUrl();
            await new Promise(resolve => setTimeout(resolve, 50));
        }
        
        // 1. 先执行强制登录检测（这会阻止未登录用户访问）
        const isAuthenticated = await checkAuthRequired();
        
        // 2. 如果通过验证，等待DOM加载后更新导航栏按钮
        if (isAuthenticated) {
            // 等待DOM加载完成后再更新按钮（因为按钮元素可能还没渲染）
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', updateUserButton);
            } else {
                // DOM已加载，立即更新
                updateUserButton();
            }
        }
    })();
    
    // 页面可见性变化时重新检查（切换标签页回来时）
    document.addEventListener('visibilitychange', async function() {
        if (!document.hidden) {
            // 页面变为可见时，重新检查登录状态
            // 也检查URL参数中是否有新的token
            extractAndSaveTokenFromUrl();
            const isAuthenticated = await checkAuthRequired();
            if (isAuthenticated) {
                updateUserButton();
            }
        }
    });
})();

