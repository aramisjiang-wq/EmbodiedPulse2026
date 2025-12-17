#!/bin/bash
# 数据库迁移脚本 - 从本地复制数据库到服务器

set -e

# 配置信息
SERVER_IP="101.200.222.139"
SERVER_USER="root"
SERVER_PASSWORD="XLj4kUnh"
SERVER_DIR="/srv/EmbodiedPulse2026"
LOCAL_DIR="/Users/dong/Documents/Cursor/Embodied Pulse"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "数据库迁移到服务器"
echo "=========================================="
echo ""

# 检查本地数据库文件
echo "1. 检查本地数据库文件..."
echo ""

PAPERS_DB="${LOCAL_DIR}/papers.db"
BILIBILI_DB="${LOCAL_DIR}/bilibili.db"

if [ ! -f "$PAPERS_DB" ]; then
    echo -e "${RED}❌ 错误: 论文数据库不存在: $PAPERS_DB${NC}"
    exit 1
fi

if [ ! -f "$BILIBILI_DB" ]; then
    echo -e "${RED}❌ 错误: B站数据库不存在: $BILIBILI_DB${NC}"
    exit 1
fi

# 检查数据库大小
PAPERS_SIZE=$(du -h "$PAPERS_DB" | cut -f1)
BILIBILI_SIZE=$(du -h "$BILIBILI_DB" | cut -f1)

echo -e "${GREEN}✓${NC} 论文数据库: $PAPERS_DB (大小: $PAPERS_SIZE)"
echo -e "${GREEN}✓${NC} B站数据库: $BILIBILI_DB (大小: $BILIBILI_SIZE)"
echo ""

# 检查数据库内容
echo "2. 检查数据库内容..."
echo ""

python3 << EOF
import sqlite3
import os

# 检查论文数据库
papers_db = "$PAPERS_DB"
if os.path.exists(papers_db):
    conn = sqlite3.connect(papers_db)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM papers")
        count = cursor.fetchone()[0]
        print(f"  论文数量: {count}")
    except Exception as e:
        print(f"  论文数据库查询失败: {e}")
    finally:
        conn.close()

# 检查B站数据库
bilibili_db = "$BILIBILI_DB"
if os.path.exists(bilibili_db):
    conn = sqlite3.connect(bilibili_db)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM bilibili_up")
        up_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM bilibili_video")
        video_count = cursor.fetchone()[0]
        print(f"  UP主数量: {up_count}")
        print(f"  视频数量: {video_count}")
    except Exception as e:
        print(f"  B站数据库查询失败: {e}")
    finally:
        conn.close()
EOF

echo ""

# 确认上传
echo "3. 准备上传到服务器..."
echo "   服务器: ${SERVER_USER}@${SERVER_IP}"
echo "   目标目录: ${SERVER_DIR}"
echo ""
read -p "是否继续上传? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消上传"
    exit 0
fi

# 上传论文数据库
echo ""
echo "4. 上传论文数据库..."
scp "$PAPERS_DB" "${SERVER_USER}@${SERVER_IP}:${SERVER_DIR}/" << EOF
${SERVER_PASSWORD}
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} 论文数据库上传成功"
else
    echo -e "${RED}❌ 论文数据库上传失败${NC}"
    exit 1
fi

# 上传B站数据库
echo ""
echo "5. 上传B站数据库..."
scp "$BILIBILI_DB" "${SERVER_USER}@${SERVER_IP}:${SERVER_DIR}/" << EOF
${SERVER_PASSWORD}
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} B站数据库上传成功"
else
    echo -e "${RED}❌ B站数据库上传失败${NC}"
    exit 1
fi

# 在服务器上设置权限
echo ""
echo "6. 在服务器上设置文件权限..."
ssh "${SERVER_USER}@${SERVER_IP}" << EOF
${SERVER_PASSWORD}
cd ${SERVER_DIR}
chmod 644 papers.db
chmod 644 bilibili.db
chown root:root papers.db
chown root:root bilibili.db
echo "文件权限已设置"
EOF

# 验证服务器上的数据库
echo ""
echo "7. 验证服务器上的数据库..."
ssh "${SERVER_USER}@${SERVER_IP}" << EOF
${SERVER_PASSWORD}
cd ${SERVER_DIR}
if command -v sqlite3 &> /dev/null; then
    echo "论文数据库:"
    sqlite3 papers.db "SELECT COUNT(*) FROM papers;" 2>/dev/null || echo "查询失败"
    echo ""
    echo "B站数据库:"
    sqlite3 bilibili.db "SELECT COUNT(*) FROM bilibili_ups;" 2>/dev/null || echo "UP主查询失败"
    sqlite3 bilibili.db "SELECT COUNT(*) FROM bilibili_videos;" 2>/dev/null || echo "视频查询失败"
else
    echo "sqlite3 未安装，跳过验证"
fi
EOF

echo ""
echo "=========================================="
echo -e "${GREEN}✅ 数据库迁移完成！${NC}"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. 重启服务: ssh ${SERVER_USER}@${SERVER_IP} 'systemctl restart embodiedpulse'"
echo "2. 检查服务状态: ssh ${SERVER_USER}@${SERVER_IP} 'systemctl status embodiedpulse'"
echo "3. 验证数据: 访问网站检查数据是否正常显示"

