#!/bin/bash
# PostgreSQL安装和迁移完整脚本（小白友好版）

set -e

APP_DIR="/srv/EmbodiedPulse2026"
DB_NAME="embodied_pulse"
DB_USER="embodied_user"

# ⚠️ 重要：请修改为你的强密码（包含大小写字母、数字、特殊字符）
DB_PASSWORD="ChangeThisPassword123!"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "PostgreSQL安装和迁移脚本"
echo "=========================================="
echo ""
echo "⚠️  重要提示:"
echo "  1. 请先修改脚本中的 DB_PASSWORD（第8行）"
echo "  2. 确保已备份数据库文件"
echo "  3. 此操作会迁移数据，请谨慎执行"
echo ""
read -p "是否继续? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

cd "$APP_DIR"

# 1. 备份数据库
echo ""
echo "=========================================="
echo "1. 备份当前数据库"
echo "=========================================="
mkdir -p backups/postgresql_migration
BACKUP_TIME=$(date +%Y%m%d_%H%M%S)

if [ -f "papers.db" ]; then
    cp papers.db "backups/postgresql_migration/papers_backup_${BACKUP_TIME}.db"
    echo -e "${GREEN}✓${NC}  论文数据库已备份"
fi

if [ -f "bilibili.db" ]; then
    cp bilibili.db "backups/postgresql_migration/bilibili_backup_${BACKUP_TIME}.db"
    echo -e "${GREEN}✓${NC}  B站数据库已备份"
fi

if [ -f "instance/papers.db" ]; then
    cp instance/papers.db "backups/postgresql_migration/auth_backup_${BACKUP_TIME}.db"
    echo -e "${GREEN}✓${NC}  认证数据库已备份"
fi

echo -e "${GREEN}✅ 备份完成${NC}"

# 2. 安装PostgreSQL
echo ""
echo "=========================================="
echo "2. 安装PostgreSQL"
echo "=========================================="

if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓${NC}  PostgreSQL已安装: $(psql --version)"
else
    echo "安装PostgreSQL..."
    apt update
    apt install -y postgresql postgresql-contrib
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PostgreSQL安装成功${NC}"
    else
        echo -e "${RED}❌ PostgreSQL安装失败${NC}"
        exit 1
    fi
fi

# 启动服务
systemctl start postgresql
systemctl enable postgresql

if systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✓${NC}  PostgreSQL服务运行正常"
else
    echo -e "${RED}❌ PostgreSQL服务启动失败${NC}"
    exit 1
fi

# 3. 创建数据库和用户
echo ""
echo "=========================================="
echo "3. 创建数据库和用户"
echo "=========================================="

# 检查数据库是否已存在
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null || echo "0")

if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${YELLOW}⚠${NC}  数据库 $DB_NAME 已存在"
    read -p "是否删除并重新创建? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null || true
        sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;" 2>/dev/null || true
    else
        echo "跳过数据库创建"
    fi
fi

# 创建数据库和用户
if [ "$DB_EXISTS" != "1" ] || [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo -u postgres psql << EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER USER $DB_USER CREATEDB;
\q
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 数据库和用户创建成功${NC}"
    else
        echo -e "${RED}❌ 数据库创建失败${NC}"
        exit 1
    fi
fi

# 4. 安装Python依赖
echo ""
echo "=========================================="
echo "4. 安装Python依赖"
echo "=========================================="

source venv/bin/activate

if python3 -c "import psycopg2" 2>/dev/null; then
    echo -e "${GREEN}✓${NC}  psycopg2已安装"
else
    echo "安装psycopg2-binary..."
    pip install psycopg2-binary
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ psycopg2安装成功${NC}"
    else
        echo -e "${RED}❌ psycopg2安装失败${NC}"
        exit 1
    fi
fi

# 5. 初始化表结构
echo ""
echo "=========================================="
echo "5. 初始化PostgreSQL表结构"
echo "=========================================="

export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"

python3 init_database.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 表结构创建成功${NC}"
else
    echo -e "${RED}❌ 表结构创建失败${NC}"
    exit 1
fi

# 6. 迁移数据
echo ""
echo "=========================================="
echo "6. 迁移数据（这可能需要几分钟）"
echo "=========================================="

python3 migrate_sqlite_to_postgresql.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 数据迁移完成${NC}"
else
    echo -e "${RED}❌ 数据迁移失败${NC}"
    echo "可以从备份恢复: cp backups/postgresql_migration/*.db ."
    exit 1
fi

# 7. 更新.env文件
echo ""
echo "=========================================="
echo "7. 更新.env文件"
echo "=========================================="

# 备份.env文件
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# 更新DATABASE_URL
sed -i "s|DATABASE_URL=sqlite:///./papers.db|DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME|" .env

# 验证更新
if grep -q "postgresql://" .env; then
    echo -e "${GREEN}✅ .env文件已更新${NC}"
    echo "新的DATABASE_URL:"
    grep DATABASE_URL .env | head -1
else
    echo -e "${RED}❌ .env文件更新失败${NC}"
    exit 1
fi

# 8. 重启服务
echo ""
echo "=========================================="
echo "8. 重启服务"
echo "=========================================="

systemctl restart embodiedpulse
sleep 3

if systemctl is-active --quiet embodiedpulse; then
    echo -e "${GREEN}✅ 服务重启成功${NC}"
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    echo "查看日志: journalctl -u embodiedpulse -n 50"
    exit 1
fi

# 9. 验证数据
echo ""
echo "=========================================="
echo "9. 验证数据"
echo "=========================================="

python3 << EOF
import os
os.environ['DATABASE_URL'] = 'postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME'

try:
    from models import get_session, Paper
    from bilibili_models import get_bilibili_session, BilibiliUp
    
    # 检查论文数据
    session = get_session()
    papers_count = session.query(Paper).count()
    session.close()
    print(f"✅ 论文数据: {papers_count} 篇")
    
    # 检查B站数据
    bilibili_session = get_bilibili_session()
    ups_count = bilibili_session.query(BilibiliUp).count()
    bilibili_session.close()
    print(f"✅ UP主数据: {ups_count} 个")
    
except Exception as e:
    print(f"❌ 验证失败: {e}")
    exit(1)
EOF

echo ""
echo "=========================================="
echo -e "${GREEN}✅ PostgreSQL安装和迁移完成！${NC}"
echo "=========================================="
echo ""
echo "数据库信息:"
echo "  数据库名: $DB_NAME"
echo "  用户名: $DB_USER"
echo "  连接URL: postgresql://$DB_USER:***@localhost:5432/$DB_NAME"
echo ""
echo "备份位置: backups/postgresql_migration/"
echo ""
echo "下一步:"
echo "  1. 访问网站验证: https://essay.gradmotion.com"
echo "  2. 检查服务日志: journalctl -u embodiedpulse -n 50"
echo "  3. 如有问题，查看: docs/项目文档/06-安装部署/配置指南/PostgreSQL安装与迁移小白教程_20251217_v1.0.md"

