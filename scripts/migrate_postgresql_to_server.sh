#!/bin/bash
# 从本地PostgreSQL迁移到服务器PostgreSQL（完整方案）

set -e

# 配置
LOCAL_PG_HOST="localhost"
LOCAL_PG_PORT="5432"
LOCAL_PG_USER="robotics_user"
LOCAL_PG_PASSWORD="robotics_password"
LOCAL_PG_DB="robotics_arxiv"

SERVER_USER="root"
SERVER_IP="101.200.222.139"
SERVER_DIR="/srv/EmbodiedPulse2026"
SERVER_PG_USER="embodied_user"
SERVER_PG_PASSWORD='MyStrongPass123!@#'  # ⚠️ 修改为服务器PostgreSQL密码
SERVER_PG_DB="embodied_pulse"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "从本地PostgreSQL迁移到服务器PostgreSQL"
echo "=========================================="
echo ""
echo "⚠️  请确认以下配置："
echo "  本地PostgreSQL:"
echo "    主机: $LOCAL_PG_HOST:$LOCAL_PG_PORT"
echo "    用户: $LOCAL_PG_USER"
echo "    数据库: $LOCAL_PG_DB"
echo ""
echo "  服务器PostgreSQL:"
echo "    主机: $SERVER_IP"
echo "    用户: $SERVER_PG_USER"
echo "    数据库: $SERVER_PG_DB"
echo ""
read -p "配置是否正确? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "请修改脚本中的配置后重新运行"
    exit 0
fi

# 1. 检查本地PostgreSQL连接
echo ""
echo "=========================================="
echo "1. 检查本地PostgreSQL连接"
echo "=========================================="

export PGPASSWORD="$LOCAL_PG_PASSWORD"

if psql -h "$LOCAL_PG_HOST" -p "$LOCAL_PG_PORT" -U "$LOCAL_PG_USER" -d "$LOCAL_PG_DB" -c "\q" 2>/dev/null; then
    echo -e "${GREEN}✅ 本地PostgreSQL连接成功${NC}"
else
    echo -e "${RED}❌ 本地PostgreSQL连接失败${NC}"
    echo "请检查："
    echo "  1. PostgreSQL服务是否运行"
    echo "  2. 连接信息是否正确"
    echo "  3. 密码是否正确"
    exit 1
fi

# 检查本地数据量
echo ""
echo "检查本地数据量..."
LOCAL_PAPERS=$(psql -h "$LOCAL_PG_HOST" -p "$LOCAL_PG_PORT" -U "$LOCAL_PG_USER" -d "$LOCAL_PG_DB" -tAc "SELECT COUNT(*) FROM papers;" 2>/dev/null || echo "0")
LOCAL_UPS=$(psql -h "$LOCAL_PG_HOST" -p "$LOCAL_PG_PORT" -U "$LOCAL_PG_USER" -d "$LOCAL_PG_DB" -tAc "SELECT COUNT(*) FROM bilibili_ups;" 2>/dev/null || echo "0")
LOCAL_VIDEOS=$(psql -h "$LOCAL_PG_HOST" -p "$LOCAL_PG_PORT" -U "$LOCAL_PG_USER" -d "$LOCAL_PG_DB" -tAc "SELECT COUNT(*) FROM bilibili_videos;" 2>/dev/null || echo "0")

echo "  论文数量: $LOCAL_PAPERS 篇"
echo "  UP主数量: $LOCAL_UPS 个"
echo "  视频数量: $LOCAL_VIDEOS 个"

if [ "$LOCAL_PAPERS" = "0" ] && [ "$LOCAL_UPS" = "0" ]; then
    echo -e "${YELLOW}⚠${NC}  本地数据量为0，是否继续？"
    read -p "继续? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# 2. 在服务器上执行迁移
echo ""
echo "=========================================="
echo "2. 在服务器上执行迁移"
echo "=========================================="

# 编码服务器密码
ENCODED_SERVER_PASSWORD=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$SERVER_PG_PASSWORD', safe=''))")

# 创建迁移脚本并执行
ssh "${SERVER_USER}@${SERVER_IP}" << EOF
cd $SERVER_DIR
source venv/bin/activate

# 设置环境变量
export PGPASSWORD='$SERVER_PG_PASSWORD'
export DATABASE_URL="postgresql://$SERVER_PG_USER:$ENCODED_SERVER_PASSWORD@localhost:5432/$SERVER_PG_DB"
export BILIBILI_DATABASE_URL="postgresql://$SERVER_PG_USER:$ENCODED_SERVER_PASSWORD@localhost:5432/$SERVER_PG_DB"

# 检查服务器PostgreSQL连接
if psql -h localhost -U $SERVER_PG_USER -d $SERVER_PG_DB -c "\q" 2>/dev/null; then
    echo "✅ 服务器PostgreSQL连接成功"
else
    echo "❌ 服务器PostgreSQL连接失败"
    exit 1
fi

# 使用pg_dump和psql迁移数据
echo ""
echo "开始迁移数据..."

# 从本地导出数据（使用pg_dump）
# 注意：这需要在本地执行，然后传输到服务器
EOF

# 3. 导出本地数据
echo ""
echo "=========================================="
echo "3. 导出本地PostgreSQL数据"
echo "=========================================="

DUMP_FILE="/tmp/embodied_pulse_dump_$(date +%Y%m%d_%H%M%S).sql"
echo "导出数据到: $DUMP_FILE"

pg_dump -h "$LOCAL_PG_HOST" -p "$LOCAL_PG_PORT" -U "$LOCAL_PG_USER" -d "$LOCAL_PG_DB" \
    --no-owner --no-acl \
    -t papers -t bilibili_ups -t bilibili_videos \
    -t jobs -t news -t datasets \
    > "$DUMP_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 数据导出成功${NC}"
    DUMP_SIZE=$(du -h "$DUMP_FILE" | cut -f1)
    echo "  文件大小: $DUMP_SIZE"
else
    echo -e "${RED}❌ 数据导出失败${NC}"
    exit 1
fi

# 4. 传输到服务器
echo ""
echo "=========================================="
echo "4. 传输数据到服务器"
echo "=========================================="

scp "$DUMP_FILE" "${SERVER_USER}@${SERVER_IP}:/tmp/"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 文件传输成功${NC}"
else
    echo -e "${RED}❌ 文件传输失败${NC}"
    exit 1
fi

# 5. 在服务器上导入数据
echo ""
echo "=========================================="
echo "5. 在服务器上导入数据"
echo "=========================================="

DUMP_FILENAME=$(basename "$DUMP_FILE")

ssh "${SERVER_USER}@${SERVER_IP}" << EOF
cd $SERVER_DIR
source venv/bin/activate

export PGPASSWORD='$SERVER_PG_PASSWORD'

# 导入数据
echo "导入数据到PostgreSQL..."
psql -h localhost -U $SERVER_PG_USER -d $SERVER_PG_DB < /tmp/$DUMP_FILENAME

if [ \$? -eq 0 ]; then
    echo "✅ 数据导入成功"
    
    # 验证数据
    echo ""
    echo "验证数据..."
    PAPERS_COUNT=\$(psql -h localhost -U $SERVER_PG_USER -d $SERVER_PG_DB -tAc "SELECT COUNT(*) FROM papers;" 2>/dev/null || echo "0")
    UPS_COUNT=\$(psql -h localhost -U $SERVER_PG_USER -d $SERVER_PG_DB -tAc "SELECT COUNT(*) FROM bilibili_ups;" 2>/dev/null || echo "0")
    VIDEOS_COUNT=\$(psql -h localhost -U $SERVER_PG_USER -d $SERVER_PG_DB -tAc "SELECT COUNT(*) FROM bilibili_videos;" 2>/dev/null || echo "0")
    
    echo "  论文数量: \$PAPERS_COUNT 篇"
    echo "  UP主数量: \$UPS_COUNT 个"
    echo "  视频数量: \$VIDEOS_COUNT 个"
else
    echo "❌ 数据导入失败"
    exit 1
fi

# 清理临时文件
rm -f /tmp/$DUMP_FILENAME
EOF

# 清理本地临时文件
rm -f "$DUMP_FILE"

echo ""
echo "=========================================="
echo -e "${GREEN}✅ 迁移完成！${NC}"
echo "=========================================="
echo ""
echo "下一步:"
echo "  1. 重启服务: ssh ${SERVER_USER}@${SERVER_IP} 'systemctl restart embodiedpulse'"
echo "  2. 验证网站: https://essay.gradmotion.com"
echo "  3. 检查B站页面: https://blibli.gradmotion.com"

