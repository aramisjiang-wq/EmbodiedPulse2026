#!/bin/bash
# 数据库自动备份脚本
# 备份所有数据库文件，压缩并保留指定天数

set -e

# 配置
APP_DIR="/srv/EmbodiedPulse2026"
BACKUP_DIR="${APP_DIR}/backups"
RETENTION_DAYS=7  # 保留7天的备份
DATE=$(date +%Y%m%d_%H%M%S)

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "数据库自动备份"
echo "=========================================="
echo "备份时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份函数
backup_database() {
    local db_file=$1
    local db_name=$2
    
    if [ ! -f "$db_file" ]; then
        echo -e "${YELLOW}⚠${NC}  数据库文件不存在: $db_file"
        return 1
    fi
    
    local backup_file="${BACKUP_DIR}/${db_name}_${DATE}.db"
    
    echo "备份: $db_name"
    echo "  源文件: $db_file"
    
    # 复制数据库文件
    cp "$db_file" "$backup_file"
    
    if [ $? -eq 0 ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        echo -e "  ${GREEN}✓${NC}  备份成功: $backup_file (大小: $size)"
        
        # 压缩备份文件
        echo "  压缩备份文件..."
        gzip "$backup_file"
        
        if [ $? -eq 0 ]; then
            local compressed_size=$(du -h "${backup_file}.gz" | cut -f1)
            echo -e "  ${GREEN}✓${NC}  压缩完成: ${backup_file}.gz (大小: $compressed_size)"
            return 0
        else
            echo -e "  ${RED}✗${NC}  压缩失败"
            return 1
        fi
    else
        echo -e "  ${RED}✗${NC}  备份失败"
        return 1
    fi
}

# 备份论文数据库
echo "1. 备份论文数据库..."
backup_database "${APP_DIR}/papers.db" "papers"

# 备份B站数据库
echo ""
echo "2. 备份B站数据库..."
backup_database "${APP_DIR}/bilibili.db" "bilibili"

# 备份认证数据库（如果存在）
if [ -f "${APP_DIR}/instance/papers.db" ]; then
    echo ""
    echo "3. 备份认证数据库..."
    backup_database "${APP_DIR}/instance/papers.db" "auth"
fi

# 清理旧备份
echo ""
echo "4. 清理旧备份（保留最近 ${RETENTION_DAYS} 天）..."
find "$BACKUP_DIR" -name "*.db.gz" -type f -mtime +${RETENTION_DAYS} -delete

deleted_count=$(find "$BACKUP_DIR" -name "*.db.gz" -type f -mtime +${RETENTION_DAYS} 2>/dev/null | wc -l)
if [ "$deleted_count" -gt 0 ]; then
    echo -e "${GREEN}✓${NC}  已删除 $deleted_count 个旧备份文件"
else
    echo "  没有需要删除的旧备份文件"
fi

# 显示备份统计
echo ""
echo "5. 备份统计:"
total_backups=$(find "$BACKUP_DIR" -name "*.db.gz" -type f | wc -l)
total_size=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "  备份文件总数: $total_backups"
echo "  备份目录大小: $total_size"

# 列出最近的备份
echo ""
echo "最近的备份文件:"
ls -lht "$BACKUP_DIR"/*.db.gz 2>/dev/null | head -5 | awk '{print "  " $9 " (" $5 ")"}'

echo ""
echo "=========================================="
echo -e "${GREEN}✅ 备份完成！${NC}"
echo "=========================================="

