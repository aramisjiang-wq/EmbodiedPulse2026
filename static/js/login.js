/**
 * 登录页面逻辑
 */

// DOM元素
const feishuLoginBtn = document.getElementById('feishu-login-btn');
const loadingDiv = document.getElementById('loading');
const errorMessageDiv = document.getElementById('error-message');

// 检查是否已登录
function checkLoginStatus() {
    const token = localStorage.getItem('auth_token');
    
    if (token) {
        // 验证token是否有效
        fetch('/api/auth/user-info', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(res => {
            if (res.ok) {
                // ✅ 修复：已登录，跳转到主页（使用正确的域名，并通过URL参数传递token）
                const targetUrl = 'https://essay.gradmotion.com/';
                // 由于跨域，需要通过URL参数传递token
                const url = new URL(targetUrl);
                url.searchParams.set('token', token);
                console.log('✅ [checkLoginStatus] 已登录，跳转到主页（带token参数）:', url.toString());
                window.location.href = url.toString();
            } else {
                // token无效，清除
                console.log('⚠️ [checkLoginStatus] Token无效，清除');
                localStorage.removeItem('auth_token');
            }
        })
        .catch(err => {
            console.error('❌ [checkLoginStatus] 检查登录状态失败:', err);
            // ✅ 修复：网络错误时不自动跳转，避免循环
            // localStorage.removeItem('auth_token'); // 不删除token，可能是临时网络问题
        });
    } else {
        console.log('ℹ️ [checkLoginStatus] 未登录，显示登录页面');
    }
}

// 处理URL中的错误参数
function handleUrlError() {
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    
    if (error) {
        const errorMessages = {
            'missing_params': '登录参数缺失，请重试',
            'invalid_state': '登录验证失败（可能是验证码过期），请重新点击登录按钮',
            'no_user_id': '无法获取用户信息，请重试',
            'callback_failed': '登录处理失败，请重试',
            'feishu_config_error': '飞书登录配置错误，请联系管理员',
            'invalid_code': '登录验证码无效或已过期，请重新登录'
        };
        
        // 检查是否有详细原因
        const reason = urlParams.get('reason');
        if (reason === 'state_not_found') {
            errorMessages['invalid_state'] = '登录验证失败（验证码已过期或被使用），请重新点击"飞书扫码登录"按钮';
        }
        
        showError(errorMessages[error] || '登录失败，请重试');
        
        // 清除URL中的错误参数
        window.history.replaceState({}, '', '/login');
    }
}

// 处理URL中的token参数（飞书回调后）
function handleTokenCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    if (token) {
        console.log('✅ [handleTokenCallback] 从URL参数中提取到token');
        // 保存token
        localStorage.setItem('auth_token', token);
        
        // 清除URL中的token参数
        window.history.replaceState({}, '', '/login');
        
        // 获取保存的跳转地址，如果没有则跳转到主页
        let redirectUrl = localStorage.getItem('redirect_after_login') || '/';
        localStorage.removeItem('redirect_after_login');
        
        // ✅ 修复：如果是相对路径，转换为完整URL，并添加token参数
        if (redirectUrl && !redirectUrl.startsWith('http://') && !redirectUrl.startsWith('https://')) {
            // 根据路径判断域名
            if (redirectUrl === '/' || redirectUrl.startsWith('/papers')) {
                redirectUrl = 'https://essay.gradmotion.com/';
            } else if (redirectUrl.startsWith('/bilibili')) {
                redirectUrl = 'https://blibli.gradmotion.com/';
            } else {
                redirectUrl = 'https://essay.gradmotion.com' + redirectUrl;
            }
        }
        
        // ✅ 修复：跨域跳转时，需要通过URL参数传递token
        const url = new URL(redirectUrl);
        url.searchParams.set('token', token);
        redirectUrl = url.toString();
        
        console.log('🎯 [handleTokenCallback] 跳转到（带token参数）:', redirectUrl);
        
        // 跳转到目标页面
        setTimeout(() => {
            window.location.href = redirectUrl;
        }, 500);
        return true; // 返回true表示已处理token
    }
    return false; // 返回false表示没有token参数
}

// 飞书登录
async function feishuLogin() {
    try {
        // 显示加载状态
        showLoading();
        hideError();
        
        // 调用后端API获取飞书登录URL
        const response = await fetch('/api/auth/feishu/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                final_redirect: '/' // 登录成功后跳转的页面
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.login_url) {
            // 跳转到飞书登录页面
            window.location.href = data.login_url;
        } else {
            hideLoading();
            showError(data.message || '获取登录URL失败，请重试');
        }
        
    } catch (error) {
        console.error('飞书登录失败:', error);
        hideLoading();
        showError('网络错误，请检查连接后重试');
    }
}

// 显示加载状态
function showLoading() {
    if (loadingDiv) {
        loadingDiv.style.display = 'block';
    }
    if (feishuLoginBtn) {
        feishuLoginBtn.disabled = true;
        feishuLoginBtn.style.opacity = '0.5';
    }
}

// 隐藏加载状态
function hideLoading() {
    if (loadingDiv) {
        loadingDiv.style.display = 'none';
    }
    if (feishuLoginBtn) {
        feishuLoginBtn.disabled = false;
        feishuLoginBtn.style.opacity = '1';
    }
}

// 显示错误信息
function showError(message) {
    if (errorMessageDiv) {
        errorMessageDiv.textContent = message;
        errorMessageDiv.style.display = 'block';
        
        // 3秒后自动隐藏
        setTimeout(() => {
            hideError();
        }, 3000);
    }
}

// 隐藏错误信息
function hideError() {
    if (errorMessageDiv) {
        errorMessageDiv.style.display = 'none';
    }
}

// 事件监听
if (feishuLoginBtn) {
    feishuLoginBtn.addEventListener('click', feishuLogin);
}

// 页面加载时执行
document.addEventListener('DOMContentLoaded', () => {
    console.log('🔐 [login.js] 登录页面加载，当前域名:', window.location.hostname);
    
    // ✅ 修复：先处理URL中的token（如果有），然后再检查登录状态
    // 这样可以避免在已有token的情况下立即跳转
    const urlParams = new URLSearchParams(window.location.search);
    const tokenInUrl = urlParams.get('token');
    
    if (tokenInUrl) {
        // 如果有token参数，先处理它
        console.log('🔐 [login.js] URL中有token参数，先处理回调');
        handleTokenCallback();
    } else {
        // 没有token参数，检查是否已登录
        console.log('🔐 [login.js] URL中没有token参数，检查登录状态');
        checkLoginStatus();
    }
    
    // 处理URL中的错误
    handleUrlError();
});

// 键盘事件：回车键登录
document.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && feishuLoginBtn && !feishuLoginBtn.disabled) {
        feishuLogin();
    }
});

