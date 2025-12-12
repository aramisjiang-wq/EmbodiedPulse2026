#!/bin/bash
# 服务器端自动部署脚本
# 此脚本应该在服务器上通过cron定时执行，或者通过GitHub webhook触发
# 建议通过cron每5分钟检查一次：*/5 * * * * /opt/EmbodiedPulse/server_auto_deploy.sh

set -e

PROJECT_DIR="/opt/EmbodiedPulse"
LOG_FILE="/var/log/embodied-pulse-deploy.log"

# 记录日志
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a ${LOG_FILE}
}

log "=========================================="
log "开始检查GitHub更新..."

cd ${PROJECT_DIR} || {
    log "错误: 项目目录不存在: ${PROJECT_DIR}"
    exit 1
}

# 获取当前commit hash
CURRENT_COMMIT=$(git rev-parse HEAD)
log "当前commit: ${CURRENT_COMMIT}"

# 获取远程最新commit hash
git fetch origin main > /dev/null 2>&1
REMOTE_COMMIT=$(git rev-parse origin/main)
log "远程commit: ${REMOTE_COMMIT}"

# 检查是否有更新
if [ "${CURRENT_COMMIT}" = "${REMOTE_COMMIT}" ]; then
    log "✅ 代码已是最新，无需部署"
    exit 0
fi

log "🔄 检测到新代码，开始自动部署..."

# 拉取最新代码
git pull origin main || {
    log "❌ Git pull失败"
    exit 1
}

log "✅ 代码更新成功"

# 停止旧容器
log "停止旧容器..."
docker-compose down || true

# 构建并启动新容器
log "构建并启动新容器..."
docker-compose up -d --build || {
    log "❌ Docker部署失败"
    exit 1
}

# 等待服务启动
log "等待服务启动..."
sleep 20

# 初始化数据库（如果需要）
log "检查数据库..."
docker-compose exec -T web python3 init_database.py || log "⚠️ 数据库初始化跳过（可能已存在）"

# 检查服务状态
log "检查服务状态..."
docker-compose ps

log "✅ 自动部署完成！"
log "=========================================="

