#!/bin/bash
# 系统监控脚本
# 检查服务状态、磁盘空间、内存使用等，发送告警

set -e

# 配置
APP_DIR="/srv/EmbodiedPulse2026"
LOG_FILE="${APP_DIR}/logs/monitor.log"
ALERT_EMAIL=""  # 告警邮箱（可选）
DISK_THRESHOLD=80  # 磁盘使用率告警阈值（%）
MEMORY_THRESHOLD=90  # 内存使用率告警阈值（%）

# 创建日志目录
mkdir -p "${APP_DIR}/logs"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

alert() {
    local level=$1
    local message=$2
    log "[$level] $message"
    
    # 如果配置了邮箱，可以发送邮件告警
    # if [ -n "$ALERT_EMAIL" ]; then
    #     echo "$message" | mail -s "[$level] Embodied Pulse Alert" "$ALERT_EMAIL"
    # fi
}

# 检查服务状态
check_service() {
    local service_name=$1
    local display_name=$2
    
    if systemctl is-active --quiet "$service_name"; then
        log "✓ $display_name 服务运行正常"
        return 0
    else
        alert "ERROR" "$display_name 服务未运行！"
        return 1
    fi
}

# 检查端口监听
check_port() {
    local port=$1
    local service_name=$2
    
    if lsof -i:$port > /dev/null 2>&1; then
        log "✓ 端口 $port ($service_name) 正在监听"
        return 0
    else
        alert "ERROR" "端口 $port ($service_name) 未监听！"
        return 1
    fi
}

# 检查磁盘空间
check_disk() {
    local usage=$(df -h "$APP_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -ge "$DISK_THRESHOLD" ]; then
        alert "WARNING" "磁盘使用率: ${usage}% (超过阈值 ${DISK_THRESHOLD}%)"
        return 1
    else
        log "✓ 磁盘使用率: ${usage}%"
        return 0
    fi
}

# 检查内存使用
check_memory() {
    local usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ "$usage" -ge "$MEMORY_THRESHOLD" ]; then
        alert "WARNING" "内存使用率: ${usage}% (超过阈值 ${MEMORY_THRESHOLD}%)"
        return 1
    else
        log "✓ 内存使用率: ${usage}%"
        return 0
    fi
}

# 检查数据库文件
check_database() {
    local db_file=$1
    local db_name=$2
    
    if [ ! -f "$db_file" ]; then
        alert "ERROR" "$db_name 数据库文件不存在: $db_file"
        return 1
    fi
    
    local size=$(du -h "$db_file" | cut -f1)
    log "✓ $db_name 数据库存在 (大小: $size)"
    return 0
}

# 检查最近错误日志
check_errors() {
    local error_count=$(journalctl -u embodiedpulse --since "1 hour ago" --no-pager | grep -i "error\|exception\|failed" | wc -l)
    
    if [ "$error_count" -gt 10 ]; then
        alert "WARNING" "最近1小时发现 $error_count 条错误日志"
        return 1
    else
        log "✓ 最近1小时错误日志: $error_count 条"
        return 0
    fi
}

# 检查定时任务
check_scheduler() {
    local scheduler_running=$(journalctl -u embodiedpulse --since "1 hour ago" --no-pager | grep -i "定时任务\|scheduler" | grep -i "启动\|start" | wc -l)
    
    if [ "$scheduler_running" -eq 0 ]; then
        alert "WARNING" "定时任务可能未启动（最近1小时未发现启动日志）"
        return 1
    else
        log "✓ 定时任务运行正常"
        return 0
    fi
}

# 主检查流程
main() {
    log "=========================================="
    log "开始系统监控检查"
    log "=========================================="
    
    local errors=0
    
    # 检查服务
    log ""
    log "1. 检查服务状态..."
    check_service "embodiedpulse" "Embodied Pulse" || errors=$((errors + 1))
    check_service "nginx" "Nginx" || errors=$((errors + 1))
    
    # 检查端口
    log ""
    log "2. 检查端口监听..."
    check_port "5001" "Gunicorn" || errors=$((errors + 1))
    check_port "80" "HTTP" || errors=$((errors + 1))
    check_port "443" "HTTPS" || errors=$((errors + 1))
    
    # 检查磁盘和内存
    log ""
    log "3. 检查系统资源..."
    check_disk || errors=$((errors + 1))
    check_memory || errors=$((errors + 1))
    
    # 检查数据库
    log ""
    log "4. 检查数据库文件..."
    check_database "${APP_DIR}/papers.db" "论文" || errors=$((errors + 1))
    check_database "${APP_DIR}/bilibili.db" "B站" || errors=$((errors + 1))
    
    # 检查错误日志
    log ""
    log "5. 检查错误日志..."
    check_errors || errors=$((errors + 1))
    
    # 检查定时任务
    log ""
    log "6. 检查定时任务..."
    check_scheduler || errors=$((errors + 1))
    
    # 总结
    log ""
    log "=========================================="
    if [ $errors -eq 0 ]; then
        log "✅ 所有检查通过"
    else
        log "⚠️  发现 $errors 个问题"
    fi
    log "=========================================="
    
    return $errors
}

# 执行检查
main
exit_code=$?

# 如果发现严重错误，返回非零退出码
if [ $exit_code -ne 0 ]; then
    exit 1
fi

