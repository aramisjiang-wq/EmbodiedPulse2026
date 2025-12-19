#!/bin/bash
# 远程检查服务器上的任务状态（在本地运行，通过SSH连接服务器）
# 使用方法: ./scripts/check_task_status_remote.sh [服务器地址] [用户名]

set -e

# 默认服务器配置
SERVER_USER="${2:-root}"
SERVER_IP="${1:-your-server-ip}"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "远程检查服务器任务状态"
echo "服务器: $SERVER_USER@$SERVER_IP"
echo "=========================================="
echo ""

# 检查SSH连接
echo -e "${BLUE}检查SSH连接...${NC}"
if ssh -o ConnectTimeout=5 "$SERVER_USER@$SERVER_IP" "echo '连接成功'" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} SSH连接正常"
else
    echo -e "${RED}✗${NC} 无法连接到服务器"
    echo "请检查:"
    echo "  1. 服务器地址是否正确: $SERVER_IP"
    echo "  2. 用户名是否正确: $SERVER_USER"
    echo "  3. SSH密钥是否配置"
    exit 1
fi

# 在服务器上执行检查
echo ""
echo -e "${BLUE}在服务器上执行检查...${NC}"
ssh "$SERVER_USER@$SERVER_IP" << 'EOF'
    APP_DIR="/srv/EmbodiedPulse2026"
    SERVICE_NAME="embodiedpulse"
    
    echo "=========================================="
    echo "1. 检查服务状态"
    echo "=========================================="
    if command -v systemctl >/dev/null 2>&1; then
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            echo "✓ $SERVICE_NAME 服务正在运行"
            systemctl status "$SERVICE_NAME" --no-pager -l | head -5
        else
            echo "✗ $SERVICE_NAME 服务未运行"
        fi
    fi
    
    echo ""
    echo "=========================================="
    echo "2. 检查相关进程"
    echo "=========================================="
    ps aux | grep -E "python.*app\.py|gunicorn.*app|python.*fetch" | grep -v grep | head -10 || echo "未找到相关进程"
    
    echo ""
    echo "=========================================="
    echo "3. 检查最近日志"
    echo "=========================================="
    if command -v journalctl >/dev/null 2>&1; then
        echo "最近50条日志中关于抓取任务的信息:"
        journalctl -u "$SERVICE_NAME" -n 50 --no-pager | grep -iE "抓取|fetch|arxiv|semantic|论文|paper" | tail -20 || echo "未找到相关日志"
    fi
    
    echo ""
    echo "=========================================="
    echo "4. 检查API状态"
    echo "=========================================="
    STATUS_RESPONSE=$(curl -s http://localhost:5001/api/fetch-status 2>/dev/null || echo "{}")
    if [ "$STATUS_RESPONSE" != "{}" ]; then
        echo "$STATUS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE"
        
        if echo "$STATUS_RESPONSE" | grep -q '"running":\s*true'; then
            echo ""
            echo "✓ ArXiv抓取任务正在运行"
            echo "$STATUS_RESPONSE" | grep -o '"message":"[^"]*"' | head -1
            echo "$STATUS_RESPONSE" | grep -o '"progress":[0-9]*' | head -1
            echo "$STATUS_RESPONSE" | grep -o '"total":[0-9]*' | head -1
        else
            echo ""
            echo "⚠ ArXiv抓取任务未运行"
        fi
    else
        echo "⚠ 无法访问API状态接口"
    fi
    
    echo ""
    echo "=========================================="
    echo "5. 检查数据库最新记录"
    echo "=========================================="
    if [ -f "$APP_DIR/instance/papers.db" ] && command -v sqlite3 >/dev/null 2>&1; then
        echo "今天新增的论文数量:"
        sqlite3 "$APP_DIR/instance/papers.db" "SELECT COUNT(*) FROM papers WHERE DATE(created_at) = DATE('now');" 2>/dev/null || echo "无法查询"
        
        echo ""
        echo "最近5篇论文:"
        sqlite3 "$APP_DIR/instance/papers.db" "SELECT id, substr(title, 1, 50) as title, category, created_at FROM papers ORDER BY created_at DESC LIMIT 5;" 2>/dev/null || echo "无法查询"
    fi
    
    echo ""
    echo "=========================================="
    echo "检查完成"
    echo "=========================================="
EOF

echo ""
echo -e "${GREEN}远程检查完成${NC}"

