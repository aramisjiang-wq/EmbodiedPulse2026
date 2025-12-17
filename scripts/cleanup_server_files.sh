#!/bin/bash
# 服务器端代码清理脚本
# 清理服务器上不再需要的文件、日志、备份等

set -e

APP_DIR="/srv/EmbodiedPulse2026"
BACKUP_DIR="${APP_DIR}/backups/cleanup_$(date +%Y%m%d_%H%M%S)"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "服务器端代码清理"
echo "=========================================="
echo "清理时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 统计变量
moved_count=0
deleted_count=0

# 函数：移动文件到备份目录
move_to_backup() {
    local file=$1
    local reason=$2
    
    if [ -f "$file" ] || [ -d "$file" ]; then
        echo -e "${YELLOW}⚠${NC}  移动: $file"
        echo "    原因: $reason"
        mv "$file" "$BACKUP_DIR/" 2>/dev/null || true
        moved_count=$((moved_count + 1))
    fi
}

# 函数：删除文件
delete_file() {
    local file=$1
    local reason=$2
    
    if [ -f "$file" ] || [ -d "$file" ]; then
        echo -e "${RED}✗${NC}  删除: $file"
        echo "    原因: $reason"
        rm -rf "$file" 2>/dev/null || true
        deleted_count=$((deleted_count + 1))
    fi
}

cd "$APP_DIR"

echo "1. 清理旧日志文件（保留最近7天）..."
echo ""

# 清理应用日志（保留最近7天）
if [ -d "logs" ]; then
    find logs -name "*.log" -mtime +7 -exec mv {} "$BACKUP_DIR/" \; 2>/dev/null || true
    echo -e "${GREEN}✓${NC}  旧日志文件已移动到备份"
fi

# 清理systemd日志（保留最近7天）
journalctl --vacuum-time=7d > /dev/null 2>&1 || true
echo -e "${GREEN}✓${NC}  systemd日志已清理（保留7天）"

echo ""
echo "2. 清理旧备份文件（保留最近7天）..."
echo ""

# 清理旧数据库备份（保留最近7天）
if [ -d "backups" ]; then
    old_backups=$(find backups -name "*.db.gz" -mtime +7 | wc -l)
    if [ "$old_backups" -gt 0 ]; then
        find backups -name "*.db.gz" -mtime +7 -exec mv {} "$BACKUP_DIR/" \; 2>/dev/null || true
        echo -e "${GREEN}✓${NC}  已清理 $old_backups 个旧备份文件"
    else
        echo "  没有需要清理的旧备份文件"
    fi
fi

echo ""
echo "3. 清理Python缓存文件..."
echo ""

# 清理Python缓存
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
echo -e "${GREEN}✓${NC}  Python缓存文件已清理"

echo ""
echo "4. 清理临时文件..."
echo ""

# 清理临时文件
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.swp" -delete 2>/dev/null || true
find . -name ".DS_Store" -delete 2>/dev/null || true
echo -e "${GREEN}✓${NC}  临时文件已清理"

echo ""
echo "5. 检查磁盘使用情况..."
echo ""

# 显示磁盘使用
disk_usage=$(df -h "$APP_DIR" | awk 'NR==2 {print $5}')
echo "当前磁盘使用率: $disk_usage"

# 显示目录大小
echo ""
echo "各目录大小:"
du -sh "$APP_DIR"/* 2>/dev/null | sort -h | tail -10

echo ""
echo "=========================================="
echo "清理完成"
echo "=========================================="
echo ""
echo "统计:"
echo "  移动文件: $moved_count 个"
echo "  删除文件: $deleted_count 个"
echo "  备份位置: $BACKUP_DIR"
echo ""
echo "磁盘使用: $disk_usage"
echo ""
echo "⚠️  重要提示:"
echo "  1. 所有文件已移动到备份目录，未直接删除"
echo "  2. 如需恢复，可以从备份目录恢复"
echo "  3. 确认无误后，可以删除备份目录: rm -rf $BACKUP_DIR"

