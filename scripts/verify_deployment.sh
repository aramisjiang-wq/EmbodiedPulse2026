#!/bin/bash
# 部署验证脚本 - 检查所有服务是否正常运行

set -e

echo "=========================================="
echo "Embodied Pulse 部署验证"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_service() {
    local service_name=$1
    local description=$2
    
    echo -n "检查 $description... "
    if systemctl is-active --quiet "$service_name"; then
        echo -e "${GREEN}✓ 运行中${NC}"
        return 0
    else
        echo -e "${RED}✗ 未运行${NC}"
        return 1
    fi
}

check_port() {
    local port=$1
    local description=$2
    
    echo -n "检查 $description (端口 $port)... "
    if netstat -tuln | grep -q ":$port "; then
        echo -e "${GREEN}✓ 监听中${NC}"
        return 0
    else
        echo -e "${RED}✗ 未监听${NC}"
        return 1
    fi
}

check_url() {
    local url=$1
    local description=$2
    
    echo -n "检查 $description... "
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|301\|302"; then
        echo -e "${GREEN}✓ 可访问${NC}"
        return 0
    else
        echo -e "${RED}✗ 不可访问${NC}"
        return 1
    fi
}

# 1. 检查 systemd 服务
echo ""
echo "1. 检查 systemd 服务"
echo "----------------------------------------"
check_service "embodiedpulse" "Flask 应用服务"
check_service "nginx" "Nginx 服务"

# 2. 检查端口
echo ""
echo "2. 检查端口监听"
echo "----------------------------------------"
check_port "5001" "Flask 应用端口"
check_port "80" "HTTP 端口"
check_port "443" "HTTPS 端口"

# 3. 检查本地服务
echo ""
echo "3. 检查本地服务"
echo "----------------------------------------"
check_url "http://127.0.0.1:5001/" "Flask 应用根路径"
check_url "http://127.0.0.1:5001/login" "Flask 登录页面"
check_url "http://127.0.0.1:5001/bilibili" "Flask 视频页面"

# 4. 检查域名（如果可访问）
echo ""
echo "4. 检查域名访问"
echo "----------------------------------------"
DOMAINS=(
    "http://login.gradmotion.com"
    "http://essay.gradmotion.com"
    "http://blibli.gradmotion.com"
    "http://admin123.gradmotion.com"
)

for domain in "${DOMAINS[@]}"; do
    check_url "$domain" "$domain"
done

# 5. 检查数据库文件
echo ""
echo "5. 检查数据库文件"
echo "----------------------------------------"
APP_DIR="/srv/EmbodiedPulse2026"
DB_FILES=(
    "instance/papers.db"
    "bilibili.db"
)

for db_file in "${DB_FILES[@]}"; do
    full_path="${APP_DIR}/${db_file}"
    echo -n "检查 $db_file... "
    if [ -f "$full_path" ]; then
        size=$(du -h "$full_path" | cut -f1)
        echo -e "${GREEN}✓ 存在 (大小: $size)${NC}"
    else
        echo -e "${YELLOW}⚠ 不存在（首次运行时会自动创建）${NC}"
    fi
done

# 6. 检查虚拟环境
echo ""
echo "6. 检查虚拟环境"
echo "----------------------------------------"
VENV_DIR="${APP_DIR}/venv"
if [ -d "$VENV_DIR" ]; then
    echo -e "${GREEN}✓ 虚拟环境存在${NC}"
    if [ -f "${VENV_DIR}/bin/gunicorn" ]; then
        echo -e "${GREEN}✓ Gunicorn 已安装${NC}"
    else
        echo -e "${RED}✗ Gunicorn 未安装${NC}"
    fi
else
    echo -e "${RED}✗ 虚拟环境不存在${NC}"
fi

# 7. 检查定时任务
echo ""
echo "7. 检查定时任务状态"
echo "----------------------------------------"
if systemctl is-active --quiet "embodiedpulse"; then
    # 检查日志中是否有定时任务相关信息
    if journalctl -u embodiedpulse --no-pager -n 50 | grep -q "定时任务\|scheduler\|APScheduler"; then
        echo -e "${GREEN}✓ 定时任务相关日志存在${NC}"
    else
        echo -e "${YELLOW}⚠ 未找到定时任务日志（可能未启用）${NC}"
    fi
fi

# 8. 检查 Nginx 配置
echo ""
echo "8. 检查 Nginx 配置"
echo "----------------------------------------"
if nginx -t 2>&1 | grep -q "successful"; then
    echo -e "${GREEN}✓ Nginx 配置语法正确${NC}"
else
    echo -e "${RED}✗ Nginx 配置有错误${NC}"
    nginx -t
fi

# 总结
echo ""
echo "=========================================="
echo "验证完成"
echo "=========================================="
echo ""
echo "查看服务日志："
echo "  journalctl -u embodiedpulse -f"
echo ""
echo "重启服务："
echo "  systemctl restart embodiedpulse"
echo "  systemctl restart nginx"
echo ""
echo "=========================================="

