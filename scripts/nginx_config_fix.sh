#!/bin/bash
# Nginx配置修复脚本 - 解决域名路由和静态资源问题

cat > /etc/nginx/sites-available/embodiedpulse.conf << 'EOF'
# 登录页
server {
    listen 80;
    server_name login.gradmotion.com;

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

    # 登录页面
    location / {
        proxy_pass http://127.0.0.1:5001/login;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# 具身论文页
server {
    listen 80;
    server_name essay.gradmotion.com;

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

# 具身视频页
server {
    listen 80;
    server_name blibli.gradmotion.com;

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

    # 登录页面（如果用户从bilibili页面跳转过来）- 精确匹配
    location = /login {
        proxy_pass http://127.0.0.1:5001/login;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 登录页面的其他路径（如 /login/xxx）
    location ~ ^/login/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 视频页面
    location / {
        proxy_pass http://127.0.0.1:5001/bilibili;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# 管理端
server {
    listen 80;
    server_name admin123.gradmotion.com;

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

# 测试配置
nginx -t

# 如果测试通过，重载nginx
if [ $? -eq 0 ]; then
    systemctl reload nginx
    echo "✅ Nginx配置已更新并重载"
else
    echo "❌ Nginx配置有错误，请检查"
    exit 1
fi

