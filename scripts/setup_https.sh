#!/bin/bash
# 配置 HTTPS 证书（使用 Certbot）

set -e

echo "=========================================="
echo "配置 HTTPS 证书（Certbot）"
echo "=========================================="

# 检查是否已安装 certbot
if ! command -v certbot &> /dev/null; then
    echo "安装 Certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
    echo "✅ Certbot 已安装"
else
    echo "✅ Certbot 已安装"
fi

# 域名列表
DOMAINS=(
    "login.gradmotion.com"
    "essay.gradmotion.com"
    "blibli.gradmotion.com"
    "admin123.gradmotion.com"
)

echo ""
echo "开始为以下域名申请 SSL 证书："
for domain in "${DOMAINS[@]}"; do
    echo "  - $domain"
done
echo ""

# 为每个域名申请证书
for domain in "${DOMAINS[@]}"; do
    echo "=========================================="
    echo "处理域名: $domain"
    echo "=========================================="
    
    # 使用 Nginx 插件自动配置
    certbot --nginx -d "$domain" --non-interactive --agree-tos --email admin@gradmotion.com --redirect
    
    if [ $? -eq 0 ]; then
        echo "✅ $domain SSL 证书配置成功"
    else
        echo "❌ $domain SSL 证书配置失败"
    fi
    echo ""
done

# 设置自动续期
echo "=========================================="
echo "设置证书自动续期"
echo "=========================================="
systemctl enable certbot.timer
systemctl start certbot.timer

echo "✅ 证书自动续期已启用"
echo ""
echo "=========================================="
echo "验证证书状态："
echo "=========================================="
certbot certificates

echo ""
echo "=========================================="
echo "✅ HTTPS 配置完成！"
echo "=========================================="
echo "证书将在到期前自动续期"
echo "手动续期命令: certbot renew"
echo "=========================================="

