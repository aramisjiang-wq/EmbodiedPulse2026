#!/bin/bash
# 从本地SQLite文件迁移到服务器PostgreSQL（完整方案）

set -e

# 配置
LOCAL_DIR="/Users/dong/Documents/Cursor/Embodied Pulse"
SERVER_USER="root"
SERVER_IP="101.200.222.139"
SERVER_DIR="/srv/EmbodiedPulse2026"
DB_PASSWORD='MyStrongPass123!@#'  # ⚠️ 修改为你的密码

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "从本地SQLite迁移到服务器PostgreSQL"
echo "=========================================="
echo ""
echo "此脚本会："
echo "  1. 从本地复制SQLite文件到服务器"
echo "  2. 在服务器上执行迁移到PostgreSQL"
echo ""
read -p "是否继续? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

# 1. 检查本地SQLite文件
echo ""
echo "=========================================="
echo "1. 检查本地SQLite文件"
echo "=========================================="

cd "$LOCAL_DIR"

if [ ! -f "papers.db" ]; then
    echo -e "${RED}❌ 本地papers.db不存在${NC}"
    exit 1
fi

if [ ! -f "bilibili.db" ]; then
    echo -e "${YELLOW}⚠${NC}  本地bilibili.db不存在（可选）"
fi

# 检查本地数据量
echo "检查本地数据量..."
python3 << 'EOF'
from models import get_session, Paper
from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo

try:
    session = get_session()
    papers_count = session.query(Paper).count()
    session.close()
    print(f"本地论文数据: {papers_count} 篇")
except Exception as e:
    print(f"无法查询论文数据: {e}")

try:
    bilibili_session = get_bilibili_session()
    ups_count = bilibili_session.query(BilibiliUp).count()
    videos_count = bilibili_session.query(BilibiliVideo).count()
    bilibili_session.close()
    print(f"本地UP主数据: {ups_count} 个")
    print(f"本地视频数据: {videos_count} 个")
except Exception as e:
    print(f"无法查询B站数据: {e}")
EOF

# 2. 复制SQLite文件到服务器
echo ""
echo "=========================================="
echo "2. 复制SQLite文件到服务器"
echo "=========================================="

echo "复制papers.db..."
scp papers.db "${SERVER_USER}@${SERVER_IP}:${SERVER_DIR}/"

if [ -f "bilibili.db" ]; then
    echo "复制bilibili.db..."
    scp bilibili.db "${SERVER_USER}@${SERVER_IP}:${SERVER_DIR}/"
fi

echo -e "${GREEN}✅ 文件复制完成${NC}"

# 3. 在服务器上执行迁移
echo ""
echo "=========================================="
echo "3. 在服务器上执行迁移"
echo "=========================================="

ssh "${SERVER_USER}@${SERVER_IP}" << EOF
cd $SERVER_DIR
source venv/bin/activate

# 设置密码
DB_PASSWORD='$DB_PASSWORD'
ENCODED_PASSWORD=\$(python3 -c "import urllib.parse; print(urllib.parse.quote('\$DB_PASSWORD', safe=''))")

# 设置环境变量
export DATABASE_URL="postgresql://embodied_user:\$ENCODED_PASSWORD@localhost:5432/embodied_pulse"
export BILIBILI_DATABASE_URL="postgresql://embodied_user:\$ENCODED_PASSWORD@localhost:5432/embodied_pulse"

# 执行迁移
python3 migrate_sqlite_to_postgresql.py

# 验证数据
python3 << 'PYEOF'
import os
from models import get_session, Paper
from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo

session = get_session()
papers_count = session.query(Paper).count()
session.close()
print(f"\n✅ PostgreSQL论文数据: {papers_count} 篇")

bilibili_session = get_bilibili_session()
ups_count = bilibili_session.query(BilibiliUp).count()
videos_count = bilibili_session.query(BilibiliVideo).count()
bilibili_session.close()
print(f"✅ PostgreSQL UP主数据: {ups_count} 个")
print(f"✅ PostgreSQL视频数据: {videos_count} 个")
PYEOF
EOF

echo ""
echo "=========================================="
echo -e "${GREEN}✅ 迁移完成！${NC}"
echo "=========================================="

