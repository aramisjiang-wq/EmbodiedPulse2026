#!/bin/bash
# 检查论文数据抓取任务状态
# 使用方法: ./scripts/check_task_status.sh

set -e

APP_DIR="/srv/EmbodiedPulse2026"
SERVICE_NAME="embodiedpulse"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "检查论文数据抓取任务状态"
echo "=========================================="
echo ""

# ==================== 1. 检查服务状态 ====================
echo -e "${BLUE}1. 检查服务状态...${NC}"
if command -v systemctl >/dev/null 2>&1; then
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "${GREEN}✓${NC} $SERVICE_NAME 服务正在运行"
        systemctl status "$SERVICE_NAME" --no-pager -l | head -5
    else
        echo -e "${RED}✗${NC} $SERVICE_NAME 服务未运行"
    fi
else
    echo -e "${YELLOW}⚠${NC} systemctl 不可用"
fi

# ==================== 2. 检查相关进程 ====================
echo ""
echo -e "${BLUE}2. 检查相关进程...${NC}"
echo "查找Python进程（可能包含抓取任务）:"
ps aux | grep -E "python.*app\.py|gunicorn.*app|python.*fetch" | grep -v grep | head -10 || echo "未找到相关进程"

# ==================== 3. 检查日志中的任务信息 ====================
echo ""
echo -e "${BLUE}3. 检查最近日志（查找抓取任务）...${NC}"
if command -v journalctl >/dev/null 2>&1; then
    echo "最近50条日志中关于抓取任务的信息:"
    journalctl -u "$SERVICE_NAME" -n 50 --no-pager | grep -iE "抓取|fetch|arxiv|semantic|论文|paper" | tail -20 || echo "未找到相关日志"
    
    echo ""
    echo "最近10条错误日志:"
    journalctl -u "$SERVICE_NAME" -p err -n 10 --no-pager | tail -10 || echo "无错误日志"
else
    echo -e "${YELLOW}⚠${NC} journalctl 不可用，检查应用日志文件..."
    if [ -f "$APP_DIR/app.log" ]; then
        echo "最近50行日志:"
        tail -50 "$APP_DIR/app.log" | grep -iE "抓取|fetch|arxiv|semantic|论文|paper" || echo "未找到相关日志"
    else
        echo "未找到 app.log 文件"
    fi
fi

# ==================== 4. 检查API状态接口 ====================
echo ""
echo -e "${BLUE}4. 检查API状态接口...${NC}"
echo "尝试查询ArXiv抓取状态:"
STATUS_RESPONSE=$(curl -s http://localhost:5001/api/fetch-status 2>/dev/null || echo "{}")
if [ "$STATUS_RESPONSE" != "{}" ]; then
    echo "$STATUS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE"
    
    # 检查running状态
    if echo "$STATUS_RESPONSE" | grep -q '"running":\s*true'; then
        echo -e "${GREEN}✓${NC} ArXiv抓取任务正在运行"
        echo "$STATUS_RESPONSE" | grep -o '"message":"[^"]*"' | head -1
        echo "$STATUS_RESPONSE" | grep -o '"progress":[0-9]*' | head -1
        echo "$STATUS_RESPONSE" | grep -o '"total":[0-9]*' | head -1
    else
        echo -e "${YELLOW}⚠${NC} ArXiv抓取任务未运行"
    fi
else
    echo -e "${YELLOW}⚠${NC} 无法访问API状态接口（可能需要认证或服务未启动）"
fi

# ==================== 5. 检查数据库最新记录 ====================
echo ""
echo -e "${BLUE}5. 检查数据库最新记录...${NC}"
if [ -f "$APP_DIR/instance/papers.db" ]; then
    if command -v sqlite3 >/dev/null 2>&1; then
        echo "最近5篇论文（按创建时间）:"
        sqlite3 "$APP_DIR/instance/papers.db" "SELECT id, title, category, created_at FROM papers ORDER BY created_at DESC LIMIT 5;" 2>/dev/null || echo "无法查询数据库"
        
        echo ""
        echo "今天新增的论文数量:"
        sqlite3 "$APP_DIR/instance/papers.db" "SELECT COUNT(*) FROM papers WHERE DATE(created_at) = DATE('now');" 2>/dev/null || echo "无法查询"
    else
        echo -e "${YELLOW}⚠${NC} sqlite3 未安装，无法查询数据库"
    fi
else
    echo -e "${YELLOW}⚠${NC} 数据库文件不存在: $APP_DIR/instance/papers.db"
fi

# ==================== 6. 检查网络连接 ====================
echo ""
echo -e "${BLUE}6. 检查网络连接（ArXiv API）...${NC}"
if curl -s --connect-timeout 5 https://arxiv.org > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 可以访问 ArXiv"
else
    echo -e "${RED}✗${NC} 无法访问 ArXiv"
fi

if curl -s --connect-timeout 5 https://api.semanticscholar.org > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 可以访问 Semantic Scholar API"
else
    echo -e "${RED}✗${NC} 无法访问 Semantic Scholar API"
fi

# ==================== 7. 检查线程状态（如果可能） ====================
echo ""
echo -e "${BLUE}7. 检查系统资源...${NC}"
echo "CPU使用率:"
top -bn1 | grep "Cpu(s)" | head -1 || echo "无法获取CPU信息"

echo ""
echo "内存使用:"
free -h 2>/dev/null || vm_stat | head -10 || echo "无法获取内存信息"

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="
echo ""
echo "提示:"
echo "  - 如果任务正在运行，可以通过以下命令实时查看日志:"
echo "    sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "  - 如果任务卡住，可以重启服务:"
echo "    sudo systemctl restart $SERVICE_NAME"
echo ""

