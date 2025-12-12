#!/bin/bash
# 在服务器上设置自动部署（通过cron定时检查GitHub更新）

set -e

PROJECT_DIR="/opt/EmbodiedPulse"
SCRIPT_PATH="${PROJECT_DIR}/scripts/server_auto_deploy.sh"

echo "=========================================="
echo "设置服务器自动部署"
echo "=========================================="

# 1. 确保项目目录存在
if [ ! -d "${PROJECT_DIR}" ]; then
    echo "项目目录不存在，正在克隆..."
    mkdir -p /opt
    cd /opt
    git clone https://github.com/aramisjiang-wq/EmbodiedPulse2026.git EmbodiedPulse
    cd EmbodiedPulse
else
    cd ${PROJECT_DIR}
    # 更新代码
    if [ -d ".git" ]; then
        git pull origin main || echo "更新代码失败，继续..."
    fi
fi

# 2. 确保自动部署脚本存在
if [ ! -f "${SCRIPT_PATH}" ]; then
    echo "自动部署脚本不存在，创建中..."
    mkdir -p ${PROJECT_DIR}/scripts
fi

# 3. 设置脚本权限
chmod +x ${SCRIPT_PATH}

# 4. 检查cron任务是否已存在
CRON_CMD="*/5 * * * * ${SCRIPT_PATH} >> /var/log/embodied-pulse-deploy.log 2>&1"
CRON_EXISTS=$(crontab -l 2>/dev/null | grep -F "${SCRIPT_PATH}" || echo "")

if [ -z "$CRON_EXISTS" ]; then
    echo "添加cron任务..."
    (crontab -l 2>/dev/null; echo "${CRON_CMD}") | crontab -
    echo "✅ Cron任务已添加（每5分钟检查一次）"
else
    echo "✅ Cron任务已存在"
fi

# 5. 显示当前cron任务
echo ""
echo "当前cron任务:"
crontab -l | grep "${SCRIPT_PATH}" || echo "未找到相关任务"

# 6. 测试执行一次
echo ""
echo "测试执行自动部署脚本..."
bash ${SCRIPT_PATH}

echo ""
echo "=========================================="
echo "✅ 自动部署设置完成！"
echo "=========================================="
echo "服务器将每5分钟自动检查GitHub更新"
echo "如果检测到新代码，会自动部署"
echo ""
echo "查看日志: tail -f /var/log/embodied-pulse-deploy.log"
echo "=========================================="

