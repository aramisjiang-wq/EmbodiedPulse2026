/**
 * 导航链接修正工具
 * 根据当前域名自动修正导航链接，确保跳转到正确的域名
 */

// 域名映射配置
const DOMAIN_MAP = {
    'essay.gradmotion.com': {
        home: 'https://essay.gradmotion.com/',
        papers: 'https://essay.gradmotion.com/',
        bilibili: 'https://essay.gradmotion.com/bilibili',
        profile: 'https://login.gradmotion.com/profile',
        login: 'https://login.gradmotion.com/login'
    },
    'blibli.gradmotion.com': {
        home: 'https://blibli.gradmotion.com/',
        papers: 'https://essay.gradmotion.com/',
        bilibili: 'https://blibli.gradmotion.com/',
        profile: 'https://login.gradmotion.com/profile',
        login: 'https://login.gradmotion.com/login'
    },
    'login.gradmotion.com': {
        home: 'https://essay.gradmotion.com/',
        papers: 'https://essay.gradmotion.com/',
        bilibili: 'https://blibli.gradmotion.com/',
        profile: 'https://login.gradmotion.com/profile',
        login: 'https://login.gradmotion.com/login'
    }
};

/**
 * 根据路径获取正确的完整URL
 * @param {string} path - 相对路径（如 '/', '/bilibili', '/profile'）
 * @returns {string} 完整的URL
 */
function getCorrectUrl(path) {
    const hostname = window.location.hostname;
    const domainConfig = DOMAIN_MAP[hostname] || DOMAIN_MAP['essay.gradmotion.com'];
    
    // 标准化路径
    const normalizedPath = path === '/' ? 'home' : path.replace(/^\//, '').replace(/\/$/, '');
    
    // 映射路径到配置键
    // 注意：/papers 实际上就是首页（论文页面），所以映射到 'papers' 配置
    const pathMap = {
        '': 'home',
        'home': 'home',
        'papers': 'papers',  // 论文页面就是首页，但使用 papers 配置
        'bilibili': 'bilibili',
        'profile': 'profile',
        'login': 'login'
    };
    
    const key = pathMap[normalizedPath] || 'home';
    return domainConfig[key] || domainConfig['home'];
}

/**
 * 修正单个链接元素
 * @param {HTMLAnchorElement} link - 链接元素
 */
function fixNavLink(link) {
    const href = link.getAttribute('href');
    
    // 跳过外部链接（包含 http:// 或 https:// 或 target="_blank"）
    if (!href || href.startsWith('http://') || href.startsWith('https://') || link.getAttribute('target') === '_blank') {
        return;
    }
    
    // 跳过锚点链接（以 # 开头）
    if (href.startsWith('#')) {
        return;
    }
    
    // 修正链接
    let correctUrl = getCorrectUrl(href);
    
    // ✅ 修复：如果从 login.gradmotion.com 跳转到其他域名，需要通过 URL 参数传递 token
    const currentHost = window.location.hostname;
    const targetUrl = new URL(correctUrl);
    const targetHost = targetUrl.hostname;
    
    // 如果跨域跳转（从 login.gradmotion.com 到其他域名），且目标域名不是 login.gradmotion.com
    if (currentHost === 'login.gradmotion.com' && targetHost !== 'login.gradmotion.com') {
        const token = localStorage.getItem('auth_token');
        if (token) {
            // 通过 URL 参数传递 token，目标页面会提取并保存到自己的 localStorage
            targetUrl.searchParams.set('token', token);
            correctUrl = targetUrl.toString();
            console.log('🔗 [fixNavLink] 跨域跳转，添加token参数:', targetHost);
        }
    }
    
    link.setAttribute('href', correctUrl);
}

/**
 * 修正页面中所有导航链接
 */
function fixAllNavLinks() {
    // 查找所有导航链接
    const navLinks = document.querySelectorAll('nav a[href], .nav-link, .nav-tab, .nav-item');
    
    navLinks.forEach(link => {
        fixNavLink(link);
    });
    
    console.log(`✅ 已修正 ${navLinks.length} 个导航链接`);
}

// 页面加载完成后自动修正
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', fixAllNavLinks);
} else {
    fixAllNavLinks();
}

/**
 * 安全跳转到指定路径（自动使用正确的域名）
 * @param {string} path - 相对路径（如 '/', '/login', '/bilibili'）
 */
function navigateTo(path) {
    let correctUrl = getCorrectUrl(path);
    
    // ✅ 修复：如果从 login.gradmotion.com 跳转到其他域名，需要通过 URL 参数传递 token
    const currentHost = window.location.hostname;
    const targetUrl = new URL(correctUrl);
    const targetHost = targetUrl.hostname;
    
    // 如果跨域跳转（从 login.gradmotion.com 到其他域名），且目标域名不是 login.gradmotion.com
    if (currentHost === 'login.gradmotion.com' && targetHost !== 'login.gradmotion.com') {
        const token = localStorage.getItem('auth_token');
        if (token) {
            // 通过 URL 参数传递 token，目标页面会提取并保存到自己的 localStorage
            targetUrl.searchParams.set('token', token);
            correctUrl = targetUrl.toString();
            console.log('🔗 [navigateTo] 跨域跳转，添加token参数:', targetHost);
        }
    }
    
    window.location.href = correctUrl;
}

// 导出函数供其他脚本使用
window.getCorrectUrl = getCorrectUrl;
window.fixNavLink = fixNavLink;
window.fixAllNavLinks = fixAllNavLinks;
window.navigateTo = navigateTo;

