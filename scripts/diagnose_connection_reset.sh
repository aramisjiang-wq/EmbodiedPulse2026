#!/bin/bash
# 诊断 ERR_CONNECTION_RESET 问题

echo "=========================================="
echo "诊断 ERR_CONNECTION_RESET 问题"
echo "=========================================="
echo ""

# 1. 检查 Flask 服务状态
echo "1️⃣  检查 Flask 服务状态..."
if systemctl is-active --quiet embodiedpulse; then
    echo "✅ Flask 服务正在运行"
    systemctl status embodiedpulse --no-pager -l | head -20
else
    echo "❌ Flask 服务未运行！"
    echo "尝试启动服务..."
    sudo systemctl start embodiedpulse
    sleep 2
    if systemctl is-active --quiet embodiedpulse; then
        echo "✅ Flask 服务已启动"
    else
        echo "❌ Flask 服务启动失败"
        echo "查看错误日志:"
        sudo journalctl -u embodiedpulse -n 50 --no-pager
    fi
fi
echo ""

# 2. 检查端口监听
echo "2️⃣  检查端口监听..."
if netstat -tlnp 2>/dev/null | grep -q ":5001"; then
    echo "✅ 端口 5001 正在监听"
    netstat -tlnp 2>/dev/null | grep ":5001"
else
    echo "❌ 端口 5001 未监听！"
    echo "检查是否有进程占用:"
    sudo lsof -i :5001 || echo "没有进程占用端口 5001"
fi
echo ""

# 3. 检查 Nginx 状态
echo "3️⃣  检查 Nginx 状态..."
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 正在运行"
    systemctl status nginx --no-pager -l | head -10
else
    echo "❌ Nginx 未运行！"
    echo "尝试启动 Nginx..."
    sudo systemctl start nginx
    sleep 1
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx 已启动"
    else
        echo "❌ Nginx 启动失败"
        echo "查看错误日志:"
        sudo journalctl -u nginx -n 50 --no-pager
    fi
fi
echo ""

# 4. 测试本地连接
echo "4️⃣  测试本地 Flask 连接..."
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5001/ | grep -q "200\|302\|301"; then
    echo "✅ Flask 本地连接正常"
    curl -I http://127.0.0.1:5001/ 2>&1 | head -5
else
    echo "❌ Flask 本地连接失败"
    echo "响应:"
    curl -v http://127.0.0.1:5001/ 2>&1 | head -20
fi
echo ""

# 5. 检查 Nginx 配置
echo "5️⃣  检查 Nginx 配置..."
if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置正确"
else
    echo "❌ Nginx 配置有错误！"
    sudo nginx -t
fi
echo ""

# 6. 检查 Nginx 错误日志
echo "6️⃣  检查 Nginx 错误日志（最近20行）..."
if [ -f /var/log/nginx/error.log ]; then
    echo "最近的错误:"
    sudo tail -20 /var/log/nginx/error.log
else
    echo "⚠️  错误日志文件不存在"
fi
echo ""

# 7. 检查 Flask 错误日志
echo "7️⃣  检查 Flask 错误日志（最近30行）..."
sudo journalctl -u embodiedpulse -n 30 --no-pager | tail -30
echo ""

# 8. 检查防火墙
echo "8️⃣  检查防火墙状态..."
if command -v ufw >/dev/null 2>&1; then
    echo "UFW 状态:"
    sudo ufw status
elif command -v firewall-cmd >/dev/null 2>&1; then
    echo "Firewalld 状态:"
    sudo firewall-cmd --list-all
else
    echo "⚠️  未检测到常见防火墙工具"
fi
echo ""

# 9. 检查进程
echo "9️⃣  检查相关进程..."
echo "Gunicorn 进程:"
ps aux | grep -E "gunicorn|flask" | grep -v grep || echo "未找到相关进程"
echo ""

# 10. 提供修复建议
echo "=========================================="
echo "🔧 修复建议"
echo "=========================================="
echo ""
echo "如果 Flask 服务未运行:"
echo "  sudo systemctl restart embodiedpulse"
echo "  sudo journalctl -u embodiedpulse -f"
echo ""
echo "如果 Nginx 未运行:"
echo "  sudo systemctl restart nginx"
echo "  sudo nginx -t"
echo ""
echo "如果端口被占用:"
echo "  sudo lsof -i :5001"
echo "  sudo kill -9 <PID>"
echo ""
echo "如果配置有问题:"
echo "  bash scripts/nginx_config_fix.sh"
echo "  sudo nginx -t"
echo "  sudo systemctl reload nginx"
echo ""
echo "查看实时日志:"
echo "  sudo journalctl -u embodiedpulse -f"
echo "  sudo tail -f /var/log/nginx/error.log"
echo ""

