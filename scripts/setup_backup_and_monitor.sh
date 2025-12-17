#!/bin/bash
# 设置数据库自动备份和监控告警

set -e

APP_DIR="/srv/EmbodiedPulse2026"
BACKUP_SCRIPT="${APP_DIR}/scripts/backup_databases.sh"
MONITOR_SCRIPT="${APP_DIR}/scripts/monitor_system.sh"

echo "=========================================="
echo "设置数据库自动备份和监控告警"
echo "=========================================="
echo ""

# 1. 设置脚本执行权限
echo "1. 设置脚本执行权限..."
chmod +x "$BACKUP_SCRIPT"
chmod +x "$MONITOR_SCRIPT"
echo "✅ 脚本权限已设置"

# 2. 设置数据库自动备份（每天凌晨2点）
echo ""
echo "2. 设置数据库自动备份..."
(crontab -l 2>/dev/null | grep -v "backup_databases.sh"; echo "0 2 * * * $BACKUP_SCRIPT >> ${APP_DIR}/logs/backup.log 2>&1") | crontab -
echo "✅ 数据库自动备份已设置（每天凌晨2点）"

# 3. 设置系统监控（每30分钟检查一次）
echo ""
echo "3. 设置系统监控..."
(crontab -l 2>/dev/null | grep -v "monitor_system.sh"; echo "*/30 * * * * $MONITOR_SCRIPT >> ${APP_DIR}/logs/monitor.log 2>&1") | crontab -
echo "✅ 系统监控已设置（每30分钟检查一次）"

# 4. 显示当前crontab配置
echo ""
echo "4. 当前定时任务配置:"
crontab -l | grep -E "backup|monitor" || echo "  未找到相关配置"

echo ""
echo "=========================================="
echo "✅ 设置完成！"
echo "=========================================="
echo ""
echo "备份任务: 每天凌晨2点执行"
echo "监控任务: 每30分钟执行一次"
echo ""
echo "日志文件:"
echo "  - 备份日志: ${APP_DIR}/logs/backup.log"
echo "  - 监控日志: ${APP_DIR}/logs/monitor.log"
echo ""
echo "手动执行:"
echo "  - 备份: bash $BACKUP_SCRIPT"
echo "  - 监控: bash $MONITOR_SCRIPT"

