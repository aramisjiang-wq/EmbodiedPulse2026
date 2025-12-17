#!/bin/bash
# 故障恢复脚本
# 用于快速恢复服务、数据库等

set -e

APP_DIR="/srv/EmbodiedPulse2026"
BACKUP_DIR="${APP_DIR}/backups"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_menu() {
    echo ""
    echo "=========================================="
    echo "故障恢复菜单"
    echo "=========================================="
    echo "1. 恢复服务（重启所有服务）"
    echo "2. 恢复数据库（从备份恢复）"
    echo "3. 修复端口占用"
    echo "4. 修复环境变量"
    echo "5. 修复Nginx配置"
    echo "6. 完整系统检查"
    echo "7. 查看最近备份"
    echo "8. 查看服务日志"
    echo "0. 退出"
    echo "=========================================="
    echo ""
    read -p "请选择操作 [0-8]: " choice
    echo ""
}

restart_services() {
    echo "=========================================="
    echo "恢复服务"
    echo "=========================================="
    
    echo "1. 停止服务..."
    systemctl stop embodiedpulse || true
    
    echo "2. 修复端口占用..."
    lsof -ti:5001 | xargs kill -9 2>/dev/null || true
    sleep 2
    
    echo "3. 启动服务..."
    systemctl start embodiedpulse
    sleep 3
    
    echo "4. 检查服务状态..."
    if systemctl is-active --quiet embodiedpulse; then
        echo -e "${GREEN}✅ 服务已恢复${NC}"
    else
        echo -e "${RED}❌ 服务启动失败${NC}"
        echo "查看日志: journalctl -u embodiedpulse -n 50"
        return 1
    fi
}

restore_database() {
    echo "=========================================="
    echo "恢复数据库"
    echo "=========================================="
    
    # 列出可用备份
    echo "可用备份文件:"
    ls -lht "$BACKUP_DIR"/*.db.gz 2>/dev/null | head -10 | awk '{print NR ". " $9 " (" $5 ", " $6 " " $7 " " $8 ")"}'
    
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A $BACKUP_DIR/*.db.gz 2>/dev/null)" ]; then
        echo -e "${RED}❌ 没有找到备份文件${NC}"
        return 1
    fi
    
    echo ""
    read -p "请选择备份文件编号（或输入完整文件名）: " backup_choice
    
    # 确定备份文件
    if [[ "$backup_choice" =~ ^[0-9]+$ ]]; then
        backup_file=$(ls -t "$BACKUP_DIR"/*.db.gz | sed -n "${backup_choice}p")
    else
        backup_file="$BACKUP_DIR/$backup_choice"
    fi
    
    if [ ! -f "$backup_file" ]; then
        echo -e "${RED}❌ 备份文件不存在: $backup_file${NC}"
        return 1
    fi
    
    # 确定目标数据库
    echo ""
    echo "选择要恢复的数据库:"
    echo "1. papers.db (论文数据库)"
    echo "2. bilibili.db (B站数据库)"
    echo "3. instance/papers.db (认证数据库)"
    read -p "请选择 [1-3]: " db_choice
    
    case $db_choice in
        1)
            target_db="${APP_DIR}/papers.db"
            ;;
        2)
            target_db="${APP_DIR}/bilibili.db"
            ;;
        3)
            target_db="${APP_DIR}/instance/papers.db"
            ;;
        *)
            echo -e "${RED}❌ 无效选择${NC}"
            return 1
            ;;
    esac
    
    # 确认恢复
    echo ""
    echo "备份文件: $backup_file"
    echo "目标数据库: $target_db"
    read -p "确认恢复? (y/n) " confirm
    
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        echo "已取消"
        return 0
    fi
    
    # 备份当前数据库
    echo ""
    echo "备份当前数据库..."
    cp "$target_db" "${target_db}.backup.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
    
    # 停止服务
    echo "停止服务..."
    systemctl stop embodiedpulse
    
    # 解压并恢复
    echo "恢复数据库..."
    gunzip -c "$backup_file" > "$target_db"
    
    # 设置权限
    chmod 644 "$target_db"
    chown root:root "$target_db"
    
    # 启动服务
    echo "启动服务..."
    systemctl start embodiedpulse
    
    echo -e "${GREEN}✅ 数据库已恢复${NC}"
}

fix_port() {
    echo "=========================================="
    echo "修复端口占用"
    echo "=========================================="
    
    echo "1. 停止服务..."
    systemctl stop embodiedpulse
    
    echo "2. 查找占用5001端口的进程..."
    pid=$(lsof -ti:5001 || true)
    
    if [ -n "$pid" ]; then
        echo "发现进程: PID=$pid"
        kill -9 $pid
        echo "进程已终止"
    else
        echo "端口未被占用"
    fi
    
    echo "3. 启动服务..."
    systemctl start embodiedpulse
    
    echo -e "${GREEN}✅ 端口问题已修复${NC}"
}

fix_env() {
    echo "=========================================="
    echo "修复环境变量"
    echo "=========================================="
    
    echo "1. 检查 .env 文件..."
    if [ ! -f "${APP_DIR}/.env" ]; then
        echo -e "${RED}❌ .env 文件不存在${NC}"
        return 1
    fi
    
    echo "2. 检查 systemd 服务配置..."
    if grep -q "EnvironmentFile" /etc/systemd/system/embodiedpulse.service; then
        echo "✅ 服务配置包含 EnvironmentFile"
    else
        echo "⚠️  服务配置缺少 EnvironmentFile，正在修复..."
        sed -i '/\[Service\]/a EnvironmentFile='${APP_DIR}'/.env' /etc/systemd/system/embodiedpulse.service
        systemctl daemon-reload
        echo "✅ 已修复"
    fi
    
    echo "3. 重启服务..."
    systemctl restart embodiedpulse
    
    echo -e "${GREEN}✅ 环境变量已修复${NC}"
}

fix_nginx() {
    echo "=========================================="
    echo "修复Nginx配置"
    echo "=========================================="
    
    echo "1. 测试Nginx配置..."
    if nginx -t; then
        echo "✅ Nginx配置正确"
    else
        echo "⚠️  Nginx配置有误，使用修复脚本..."
        bash "${APP_DIR}/scripts/nginx_config_fix.sh"
    fi
    
    echo "2. 重载Nginx..."
    systemctl reload nginx
    
    echo -e "${GREEN}✅ Nginx已修复${NC}"
}

full_check() {
    echo "=========================================="
    echo "完整系统检查"
    echo "=========================================="
    
    bash "${APP_DIR}/scripts/check_deployment_status.sh"
}

list_backups() {
    echo "=========================================="
    echo "最近备份文件"
    echo "=========================================="
    
    if [ -d "$BACKUP_DIR" ]; then
        ls -lht "$BACKUP_DIR"/*.db.gz 2>/dev/null | head -20 | awk '{print $9 " (" $5 ", " $6 " " $7 " " $8 ")"}'
    else
        echo "备份目录不存在"
    fi
}

view_logs() {
    echo "=========================================="
    echo "查看服务日志"
    echo "=========================================="
    
    echo "最近50条日志:"
    journalctl -u embodiedpulse -n 50 --no-pager
}

# 主循环
while true; do
    show_menu
    
    case $choice in
        1)
            restart_services
            ;;
        2)
            restore_database
            ;;
        3)
            fix_port
            ;;
        4)
            fix_env
            ;;
        5)
            fix_nginx
            ;;
        6)
            full_check
            ;;
        7)
            list_backups
            ;;
        8)
            view_logs
            ;;
        0)
            echo "退出"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选择${NC}"
            ;;
    esac
    
    read -p "按回车键继续..."
done

