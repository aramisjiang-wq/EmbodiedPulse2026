#!/bin/bash
# 为 Nginx 配置添加 HTTPS 支持（证书已存在）

set -e

echo "=========================================="
echo "为 Nginx 添加 HTTPS 配置"
echo "=========================================="

# 备份现有配置
if [ -f /etc/nginx/sites-available/embodiedpulse.conf ]; then
    cp /etc/nginx/sites-available/embodiedpulse.conf /etc/nginx/sites-available/embodiedpulse.conf.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ 已备份现有配置"
fi

# 读取现有配置并添加 HTTPS
cat > /etc/nginx/sites-available/embodiedpulse.conf << 'EOF'
# HTTP 重定向到 HTTPS - 登录页
server {
    listen 80;
    server_name login.gradmotion.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS - 登录页
server {
    listen 443 ssl http2;
    server_name login.gradmotion.com;

    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/login.gradmotion.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/login.gradmotion.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 静态资源直接代理（必须在最前面）
    location /static/ {
        proxy_pass http://127.0.0.1:5001/static/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API路由
    location /api/ {
        proxy_pass http://127.0.0.1:5001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 登录成功回调页面 - 必须在 /login 之前匹配
    location /auth/callback {
        proxy_pass http://127.0.0.1:5001/auth/callback;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 个人中心页面 - 必须在 /login 之前匹配
    location /profile {
        proxy_pass http://127.0.0.1:5001/profile;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 登录页面 - 精确匹配 /login
    location = /login {
        proxy_pass http://127.0.0.1:5001/login;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 其他路径（包括根路径）都代理到登录页
    location / {
        proxy_pass http://127.0.0.1:5001/login;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTP 重定向到 HTTPS - 具身论文页
server {
    listen 80;
    server_name essay.gradmotion.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS - 具身论文页
server {
    listen 443 ssl http2;
    server_name essay.gradmotion.com;

    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/essay.gradmotion.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/essay.gradmotion.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 静态资源直接代理（必须在最前面）
    location /static/ {
        proxy_pass http://127.0.0.1:5001/static/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API路由
    location /api/ {
        proxy_pass http://127.0.0.1:5001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 主页
    location / {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTP 重定向到 HTTPS - 具身视频页
server {
    listen 80;
    server_name blibli.gradmotion.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS - 具身视频页
server {
    listen 443 ssl http2;
    server_name blibli.gradmotion.com;

    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/blibli.gradmotion.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/blibli.gradmotion.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 静态资源直接代理（必须在最前面）
    location /static/ {
        proxy_pass http://127.0.0.1:5001/static/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API路由
    location /api/ {
        proxy_pass http://127.0.0.1:5001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 登录页面 - 使用精确匹配
    location = /login {
        proxy_pass http://127.0.0.1:5001/login;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 视频页面（默认路由，必须放在最后）
    location / {
        proxy_pass http://127.0.0.1:5001/bilibili;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTP 重定向到 HTTPS - 管理端
server {
    listen 80;
    server_name admin123.gradmotion.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS - 管理端
server {
    listen 443 ssl http2;
    server_name admin123.gradmotion.com;

    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/admin123.gradmotion.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin123.gradmotion.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 静态资源直接代理（必须在最前面）
    location /static/ {
        proxy_pass http://127.0.0.1:5001/static/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API路由
    location /api/ {
        proxy_pass http://127.0.0.1:5001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 管理端页面 - 默认跳转到dashboard
    location = / {
        return 301 /admin/dashboard;
    }

    # 管理端其他页面
    location /admin/ {
        proxy_pass http://127.0.0.1:5001/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

echo "✅ Nginx 配置已更新（包含 HTTPS）"

# 测试配置
echo ""
echo "🔍 测试 Nginx 配置..."
if sudo nginx -t; then
    echo "✅ Nginx 配置测试通过"
    
    # 重新加载 Nginx
    echo ""
    echo "🔄 重新加载 Nginx..."
    sudo systemctl reload nginx
    
    # 等待一下
    sleep 2
    
    # 检查端口监听
    echo ""
    echo "🔍 检查端口监听..."
    if netstat -tlnp 2>/dev/null | grep -q ":443"; then
        echo "✅ 端口 443 (HTTPS) 正在监听"
        netstat -tlnp 2>/dev/null | grep ":443"
    else
        echo "⚠️  端口 443 未监听，可能需要重启 Nginx"
        sudo systemctl restart nginx
        sleep 2
        netstat -tlnp 2>/dev/null | grep ":443" || echo "❌ 端口 443 仍未监听"
    fi
    
    echo ""
    echo "=========================================="
    echo "✅ HTTPS 配置完成！"
    echo "=========================================="
    echo ""
    echo "📋 测试 HTTPS 连接:"
    echo "  curl -I https://essay.gradmotion.com/"
    echo "  curl -I https://login.gradmotion.com/"
    echo "  curl -I https://blibli.gradmotion.com/"
    echo ""
else
    echo "❌ Nginx 配置测试失败"
    echo "恢复备份配置..."
    if [ -f /etc/nginx/sites-available/embodiedpulse.conf.backup.* ]; then
        LATEST_BACKUP=$(ls -t /etc/nginx/sites-available/embodiedpulse.conf.backup.* | head -1)
        cp "$LATEST_BACKUP" /etc/nginx/sites-available/embodiedpulse.conf
        echo "✅ 已恢复备份配置"
    fi
    exit 1
fi

