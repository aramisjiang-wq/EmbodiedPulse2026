#!/bin/bash
# PostgreSQL直接切换脚本（无需迁移，自动重新抓取数据）

set -e

APP_DIR="/srv/EmbodiedPulse2026"
DB_NAME="embodied_pulse"
DB_USER="embodied_user"

# ⚠️ 重要：请修改为你的强密码
DB_PASSWORD='MyStrongPass123!@#'

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "PostgreSQL直接切换（无需迁移）"
echo "=========================================="
echo ""
echo "⚠️  此方案会："
echo "  1. 切换到PostgreSQL"
echo "  2. 创建新的空数据库"
echo "  3. 系统会自动重新抓取数据"
echo ""
echo "💡 适用场景："
echo "  - 数据量少（< 1000条）"
echo "  - 数据可以重新抓取"
echo "  - 或者数据不重要"
echo ""
read -p "是否继续? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

cd "$APP_DIR"

# 1. 检查PostgreSQL是否安装
echo ""
echo "=========================================="
echo "1. 检查PostgreSQL"
echo "=========================================="

if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓${NC}  PostgreSQL已安装"
else
    echo "安装PostgreSQL..."
    apt update
    apt install -y postgresql postgresql-contrib
    systemctl start postgresql
    systemctl enable postgresql
    echo -e "${GREEN}✅ PostgreSQL安装完成${NC}"
fi

# 2. 创建数据库和用户
echo ""
echo "=========================================="
echo "2. 创建数据库和用户"
echo "=========================================="

DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null || echo "0")

if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${YELLOW}⚠${NC}  数据库已存在，跳过创建"
else
    sudo -u postgres psql << EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER USER $DB_USER CREATEDB;
\q
EOF
    echo -e "${GREEN}✅ 数据库和用户创建成功${NC}"
fi

# 3. 安装Python依赖
echo ""
echo "=========================================="
echo "3. 安装Python依赖"
echo "=========================================="

source venv/bin/activate

if python3 -c "import psycopg2" 2>/dev/null; then
    echo -e "${GREEN}✓${NC}  psycopg2已安装"
else
    pip install psycopg2-binary
    echo -e "${GREEN}✅ psycopg2安装成功${NC}"
fi

# 4. 更新.env文件
echo ""
echo "=========================================="
echo "4. 更新.env文件"
echo "=========================================="

# 备份.env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# 编码密码
ENCODED_PASSWORD=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$DB_PASSWORD', safe=''))")

# 删除旧配置
sed -i '/^DATABASE_URL=/d' .env
sed -i '/^BILIBILI_DATABASE_URL=/d' .env

# 添加新配置
echo "" >> .env
echo "# PostgreSQL配置" >> .env
echo "DATABASE_URL=postgresql://$DB_USER:$ENCODED_PASSWORD@localhost:5432/$DB_NAME" >> .env
echo "BILIBILI_DATABASE_URL=postgresql://$DB_USER:$ENCODED_PASSWORD@localhost:5432/$DB_NAME" >> .env

echo -e "${GREEN}✅ .env文件已更新${NC}"
echo "新的配置:"
grep DATABASE_URL .env | tail -2

# 5. 初始化表结构
echo ""
echo "=========================================="
echo "5. 初始化PostgreSQL表结构"
echo "=========================================="

export DATABASE_URL="postgresql://$DB_USER:$ENCODED_PASSWORD@localhost:5432/$DB_NAME"
export BILIBILI_DATABASE_URL="postgresql://$DB_USER:$ENCODED_PASSWORD@localhost:5432/$DB_NAME"

python3 init_database.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 表结构创建成功${NC}"
else
    echo -e "${RED}❌ 表结构创建失败${NC}"
    exit 1
fi

# 6. 重启服务
echo ""
echo "=========================================="
echo "6. 重启服务"
echo "=========================================="

systemctl restart embodiedpulse
sleep 5

if systemctl is-active --quiet embodiedpulse; then
    echo -e "${GREEN}✅ 服务重启成功${NC}"
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    echo "查看日志: journalctl -u embodiedpulse -n 50"
    exit 1
fi

# 7. 验证
echo ""
echo "=========================================="
echo "7. 验证配置"
echo "=========================================="

python3 scripts/check_current_database.py

echo ""
echo "=========================================="
echo -e "${GREEN}✅ PostgreSQL切换完成！${NC}"
echo "=========================================="
echo ""
echo "📝 下一步："
echo "  1. 访问网站触发数据抓取:"
echo "     - 论文: https://essay.gradmotion.com (点击'刷新论文数据')"
echo "     - B站: https://blibli.gradmotion.com"
echo ""
echo "  2. 或者等待定时任务自动抓取"
echo ""
echo "  3. 检查数据量:"
echo "     python3 scripts/check_current_database.py"
echo ""
echo "💡 提示:"
echo "  - SQLite文件已保留作为备份"
echo "  - 数据会自动重新抓取，需要一些时间"
echo "  - 论文数据约需30-60分钟，B站数据约需10-20分钟"

