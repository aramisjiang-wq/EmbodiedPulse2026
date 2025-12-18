#!/bin/bash
# 检查 HTTPS/SSL 配置

echo "=========================================="
echo "检查 HTTPS/SSL 配置"
echo "=========================================="
echo ""

# 1. 检查 SSL 证书
echo "1️⃣  检查 SSL 证书..."
if [ -d "/etc/letsencrypt/live" ]; then
    echo "✅ Let's Encrypt 证书目录存在"
    for domain in essay.gradmotion.com login.gradmotion.com blibli.gradmotion.com admin123.gradmotion.com; do
        if [ -d "/etc/letsencrypt/live/$domain" ]; then
            echo "  ✅ $domain 证书存在"
            cert_file="/etc/letsencrypt/live/$domain/fullchain.pem"
            if [ -f "$cert_file" ]; then
                echo "    证书有效期:"
                openssl x509 -in "$cert_file" -noout -dates 2>/dev/null | grep -E "notBefore|notAfter" || echo "    无法读取证书信息"
            fi
        else
            echo "  ❌ $domain 证书不存在"
        fi
    done
else
    echo "❌ Let's Encrypt 证书目录不存在"
fi
echo ""

# 2. 检查 Nginx SSL 配置
echo "2️⃣  检查 Nginx SSL 配置..."
if grep -q "listen 443" /etc/nginx/sites-available/embodiedpulse.conf 2>/dev/null; then
    echo "✅ Nginx 配置包含 HTTPS (443端口)"
    echo "SSL 配置片段:"
    grep -A 5 "listen 443" /etc/nginx/sites-available/embodiedpulse.conf | head -20
else
    echo "❌ Nginx 配置未包含 HTTPS (443端口)"
    echo "当前配置只监听 HTTP (80端口)"
fi
echo ""

# 3. 测试 HTTPS 连接
echo "3️⃣  测试 HTTPS 连接..."
for domain in essay.gradmotion.com login.gradmotion.com blibli.gradmotion.com; do
    echo "测试 $domain:"
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "https://$domain/" 2>&1)
    if [ "$response" = "200" ] || [ "$response" = "301" ] || [ "$response" = "302" ]; then
        echo "  ✅ HTTPS 连接正常 (HTTP $response)"
    else
        echo "  ❌ HTTPS 连接失败 (HTTP $response)"
        echo "  详细错误:"
        curl -v "https://$domain/" 2>&1 | grep -E "SSL|certificate|error" | head -5
    fi
done
echo ""

# 4. 检查端口监听
echo "4️⃣  检查端口监听..."
if netstat -tlnp 2>/dev/null | grep -q ":443"; then
    echo "✅ 端口 443 (HTTPS) 正在监听"
    netstat -tlnp 2>/dev/null | grep ":443"
else
    echo "❌ 端口 443 (HTTPS) 未监听"
fi
echo ""

# 5. 检查 Nginx 访问日志（最近错误）
echo "5️⃣  检查 Nginx 访问日志（最近错误）..."
if [ -f /var/log/nginx/access.log ]; then
    echo "最近的 HTTPS 请求:"
    sudo tail -50 /var/log/nginx/access.log | grep "443" | tail -10
else
    echo "⚠️  访问日志文件不存在"
fi
echo ""

# 6. 检查防火墙规则
echo "6️⃣  检查防火墙规则..."
if command -v iptables >/dev/null 2>&1; then
    echo "iptables 规则 (443端口):"
    sudo iptables -L -n | grep -E "443|ACCEPT|REJECT|DROP" | head -10
fi
echo ""

# 7. 检查云服务器安全组（提示）
echo "7️⃣  云服务器安全组检查..."
echo "⚠️  请检查阿里云控制台的安全组规则："
echo "   - 确保 443 端口 (HTTPS) 已开放"
echo "   - 确保 80 端口 (HTTP) 已开放"
echo "   - 检查入站规则是否允许 HTTPS 流量"
echo ""

