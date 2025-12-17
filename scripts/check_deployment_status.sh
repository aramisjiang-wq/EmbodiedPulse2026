#!/bin/bash
# 全面检查部署状态和上线准备情况

set -e

APP_DIR="/srv/EmbodiedPulse2026"
VENV_DIR="${APP_DIR}/venv"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "部署状态全面检查"
echo "=========================================="
echo ""

# 检查函数
check_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

check_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

check_error() {
    echo -e "${RED}✗${NC} $1"
}

check_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# ==================== 1. 数据库检查 ====================
echo "=========================================="
echo "1. 数据库文件检查"
echo "=========================================="

DB_FILES=(
    "instance/papers.db:论文数据库"
    "bilibili.db:B站视频数据库"
)

DB_EXISTS=0
DB_TOTAL_SIZE=0

for db_info in "${DB_FILES[@]}"; do
    IFS=':' read -r db_path db_name <<< "$db_info"
    full_path="${APP_DIR}/${db_path}"
    
    if [ -f "$full_path" ]; then
        size=$(du -h "$full_path" | cut -f1)
        size_bytes=$(stat -f%z "$full_path" 2>/dev/null || stat -c%s "$full_path" 2>/dev/null || echo "0")
        DB_TOTAL_SIZE=$((DB_TOTAL_SIZE + size_bytes))
        
        # 检查文件大小是否合理（至少大于 1KB）
        if [ "$size_bytes" -gt 1024 ]; then
            check_ok "$db_name 存在 (大小: $size)"
            
            # 尝试检查数据库内容
            if command -v sqlite3 &> /dev/null; then
                if [ "$db_path" == "instance/papers.db" ]; then
                    count=$(sqlite3 "$full_path" "SELECT COUNT(*) FROM papers;" 2>/dev/null || echo "0")
                    check_info "  论文数量: $count"
                elif [ "$db_path" == "bilibili.db" ]; then
                    up_count=$(sqlite3 "$full_path" "SELECT COUNT(*) FROM bilibili_up;" 2>/dev/null || echo "0")
                    video_count=$(sqlite3 "$full_path" "SELECT COUNT(*) FROM bilibili_video;" 2>/dev/null || echo "0")
                    check_info "  UP主数量: $up_count, 视频数量: $video_count"
                fi
            fi
            DB_EXISTS=$((DB_EXISTS + 1))
        else
            check_warning "$db_name 存在但文件很小 (大小: $size)，可能是空数据库"
        fi
    else
        check_error "$db_name 不存在: $full_path"
    fi
done

echo ""
if [ $DB_EXISTS -eq ${#DB_FILES[@]} ]; then
    check_ok "所有数据库文件都存在且有数据"
else
    check_warning "部分数据库文件缺失或为空"
fi

# ==================== 2. 服务状态检查 ====================
echo ""
echo "=========================================="
echo "2. 服务状态检查"
echo "=========================================="

# 检查 systemd 服务
if systemctl is-active --quiet embodiedpulse; then
    check_ok "embodiedpulse 服务正在运行"
    
    # 检查服务是否启用
    if systemctl is-enabled --quiet embodiedpulse; then
        check_ok "服务已设置为开机自启"
    else
        check_warning "服务未设置为开机自启"
    fi
else
    check_error "embodiedpulse 服务未运行"
fi

# 检查 Nginx
if systemctl is-active --quiet nginx; then
    check_ok "Nginx 服务正在运行"
else
    check_error "Nginx 服务未运行"
fi

# ==================== 3. 端口检查 ====================
echo ""
echo "=========================================="
echo "3. 端口监听检查"
echo "=========================================="

# 检查 5001 端口
if lsof -ti:5001 > /dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":5001 "; then
    check_ok "端口 5001 正在监听"
    lsof -i:5001 2>/dev/null | head -2 || netstat -tuln 2>/dev/null | grep ":5001 " | head -1
else
    check_error "端口 5001 未监听"
fi

# 检查 80 端口
if lsof -ti:80 > /dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":80 "; then
    check_ok "端口 80 (HTTP) 正在监听"
else
    check_warning "端口 80 未监听"
fi

# 检查 443 端口
if lsof -ti:443 > /dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":443 "; then
    check_ok "端口 443 (HTTPS) 正在监听"
else
    check_warning "端口 443 未监听（可能未配置 HTTPS）"
fi

# ==================== 4. 环境变量检查 ====================
echo ""
echo "=========================================="
echo "4. 环境变量配置检查"
echo "=========================================="

# 检查 .env 文件
if [ -f "${APP_DIR}/.env" ]; then
    check_ok ".env 文件存在"
    
    # 检查关键配置
    if grep -q "^AUTO_FETCH_ENABLED=true" "${APP_DIR}/.env"; then
        check_ok "AUTO_FETCH_ENABLED=true"
    else
        check_error "AUTO_FETCH_ENABLED 未设置为 true"
    fi
    
    # 检查其他配置
    required_vars=("AUTO_FETCH_SCHEDULE" "AUTO_FETCH_BILIBILI_SCHEDULE")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" "${APP_DIR}/.env"; then
            value=$(grep "^${var}=" "${APP_DIR}/.env" | cut -d'=' -f2)
            check_ok "$var=$value"
        else
            check_warning "$var 未配置"
        fi
    done
else
    check_error ".env 文件不存在"
fi

# 检查 systemd 服务配置
if grep -q "EnvironmentFile" /etc/systemd/system/embodiedpulse.service 2>/dev/null; then
    check_ok "systemd 服务配置包含 EnvironmentFile"
else
    check_error "systemd 服务配置缺少 EnvironmentFile（环境变量不会加载）"
fi

# ==================== 5. 定时任务检查 ====================
echo ""
echo "=========================================="
echo "5. 定时任务状态检查"
echo "=========================================="

# 检查日志中是否有定时任务启动信息
if journalctl -u embodiedpulse --no-pager -n 100 2>/dev/null | grep -qi "定时任务调度器已启动\|scheduler.*启动\|Gunicorn服务器已就绪"; then
    check_ok "定时任务调度器已启动"
    
    # 显示相关日志
    echo ""
    check_info "最近的定时任务日志："
    journalctl -u embodiedpulse --no-pager -n 50 2>/dev/null | grep -i "定时任务\|scheduler\|AUTO_FETCH" | tail -5 || echo "  未找到相关日志"
else
    check_warning "未找到定时任务启动日志（可能未启用或未启动）"
fi

# ==================== 6. Nginx 配置检查 ====================
echo ""
echo "=========================================="
echo "6. Nginx 配置检查"
echo "=========================================="

# 检查配置语法
if nginx -t 2>&1 | grep -q "successful"; then
    check_ok "Nginx 配置语法正确"
else
    check_error "Nginx 配置有错误"
    nginx -t 2>&1 | tail -5
fi

# 检查配置文件是否存在
if [ -f "/etc/nginx/sites-available/embodiedpulse.conf" ]; then
    check_ok "Nginx 站点配置文件存在"
    
    # 检查所有域名配置
    domains=("login.gradmotion.com" "essay.gradmotion.com" "blibli.gradmotion.com" "admin123.gradmotion.com")
    for domain in "${domains[@]}"; do
        if grep -q "server_name $domain" /etc/nginx/sites-available/embodiedpulse.conf; then
            check_ok "$domain 配置存在"
        else
            check_error "$domain 配置缺失"
        fi
    done
else
    check_error "Nginx 站点配置文件不存在"
fi

# ==================== 7. HTTPS 证书检查 ====================
echo ""
echo "=========================================="
echo "7. HTTPS 证书检查"
echo "=========================================="

if command -v certbot &> /dev/null; then
    cert_count=$(certbot certificates 2>/dev/null | grep -c "Certificate Name:" || echo "0")
    if [ "$cert_count" -gt 0 ]; then
        check_ok "找到 $cert_count 个 SSL 证书"
        certbot certificates 2>/dev/null | grep -A 3 "Certificate Name:" | head -20
    else
        check_warning "未找到 SSL 证书（可能需要配置 HTTPS）"
    fi
else
    check_warning "Certbot 未安装（HTTPS 可能未配置）"
fi

# ==================== 8. 域名 DNS 检查 ====================
echo ""
echo "=========================================="
echo "8. 域名 DNS 解析检查"
echo "=========================================="

domains=("login.gradmotion.com" "essay.gradmotion.com" "blibli.gradmotion.com" "admin123.gradmotion.com")
SERVER_IP="101.200.222.139"

for domain in "${domains[@]}"; do
    if command -v dig &> /dev/null; then
        resolved_ip=$(dig +short "$domain" | tail -1)
        if [ -n "$resolved_ip" ]; then
            if [ "$resolved_ip" == "$SERVER_IP" ]; then
                check_ok "$domain → $resolved_ip"
            else
                check_warning "$domain → $resolved_ip (期望: $SERVER_IP)"
            fi
        else
            check_error "$domain DNS 解析失败"
        fi
    else
        check_info "$domain (需要 dig 命令检查)"
    fi
done

# ==================== 9. 代码和依赖检查 ====================
echo ""
echo "=========================================="
echo "9. 代码和依赖检查"
echo "=========================================="

# 检查代码目录
if [ -d "$APP_DIR" ]; then
    check_ok "应用目录存在: $APP_DIR"
    
    # 检查 Git 状态
    cd "$APP_DIR"
    if [ -d ".git" ]; then
        current_branch=$(git branch --show-current 2>/dev/null || echo "unknown")
        check_ok "Git 仓库正常 (分支: $current_branch)"
    fi
    
    # 检查虚拟环境
    if [ -d "$VENV_DIR" ]; then
        check_ok "虚拟环境存在"
        
        # 检查关键依赖
        if [ -f "${VENV_DIR}/bin/gunicorn" ]; then
            check_ok "Gunicorn 已安装"
        else
            check_error "Gunicorn 未安装"
        fi
        
        if [ -f "${VENV_DIR}/bin/flask" ]; then
            check_ok "Flask 已安装"
        else
            check_error "Flask 未安装"
        fi
    else
        check_error "虚拟环境不存在"
    fi
else
    check_error "应用目录不存在"
fi

# ==================== 10. 功能测试 ====================
echo ""
echo "=========================================="
echo "10. 功能可用性检查"
echo "=========================================="

# 检查本地服务是否响应
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5001/ | grep -qE "200|301|302"; then
    check_ok "本地服务响应正常 (http://127.0.0.1:5001/)"
else
    check_error "本地服务无响应"
fi

# 检查 API 端点
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5001/api/papers | grep -qE "200|401"; then
    check_ok "论文 API 端点可访问"
else
    check_warning "论文 API 端点无响应"
fi

# ==================== 11. 日志检查 ====================
echo ""
echo "=========================================="
echo "11. 最近错误日志检查"
echo "=========================================="

error_count=$(journalctl -u embodiedpulse --no-pager -n 100 --priority=err 2>/dev/null | wc -l)
if [ "$error_count" -gt 0 ]; then
    check_warning "发现 $error_count 条错误日志"
    journalctl -u embodiedpulse --no-pager -n 20 --priority=err 2>/dev/null | tail -5
else
    check_ok "未发现错误日志"
fi

# ==================== 总结 ====================
echo ""
echo "=========================================="
echo "检查总结"
echo "=========================================="

echo ""
echo "数据库状态:"
if [ $DB_EXISTS -eq ${#DB_FILES[@]} ]; then
    check_ok "所有数据库文件都存在"
else
    check_warning "数据库文件不完整，需要检查"
fi

echo ""
echo "服务状态:"
if systemctl is-active --quiet embodiedpulse && systemctl is-active --quiet nginx; then
    check_ok "所有服务运行正常"
else
    check_error "部分服务未运行"
fi

echo ""
echo "配置状态:"
env_ok=true
if [ ! -f "${APP_DIR}/.env" ]; then
    env_ok=false
fi
if ! grep -q "EnvironmentFile" /etc/systemd/system/embodiedpulse.service 2>/dev/null; then
    env_ok=false
fi

if [ "$env_ok" = true ]; then
    check_ok "环境变量配置正确"
else
    check_error "环境变量配置有问题"
fi

echo ""
echo "=========================================="
echo "上线前待办事项"
echo "=========================================="

# 生成待办清单
todo_count=0

if [ $DB_EXISTS -lt ${#DB_FILES[@]} ]; then
    echo "  [ ] 迁移数据库文件到服务器"
    todo_count=$((todo_count + 1))
fi

if ! systemctl is-active --quiet embodiedpulse; then
    echo "  [ ] 启动 embodiedpulse 服务"
    todo_count=$((todo_count + 1))
fi

if ! grep -q "EnvironmentFile" /etc/systemd/system/embodiedpulse.service 2>/dev/null; then
    echo "  [ ] 修复 systemd 服务配置（添加 EnvironmentFile）"
    todo_count=$((todo_count + 1))
fi

if ! lsof -ti:443 > /dev/null 2>&1; then
    echo "  [ ] 配置 HTTPS 证书"
    todo_count=$((todo_count + 1))
fi

if [ "$cert_count" -eq 0 ] 2>/dev/null; then
    echo "  [ ] 申请 SSL 证书"
    todo_count=$((todo_count + 1))
fi

if [ $todo_count -eq 0 ]; then
    check_ok "所有检查项都通过！可以准备上线了！"
else
    check_warning "还有 $todo_count 项待完成"
fi

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="

