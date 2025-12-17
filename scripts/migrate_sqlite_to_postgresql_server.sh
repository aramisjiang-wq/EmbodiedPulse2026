#!/bin/bash
# 服务器端：从SQLite迁移到PostgreSQL（完整方案，确保配置正确）

set -e

APP_DIR="/srv/EmbodiedPulse2026"
DB_NAME="embodied_pulse"
DB_USER="embodied_user"
DB_PASSWORD='MyStrongPass123!@#'  # ⚠️ 修改为你的密码

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "SQLite → PostgreSQL 迁移（服务器端）"
echo "=========================================="
echo ""
echo "⚠️  此脚本会："
echo "  1. 检查当前SQLite数据量"
echo "  2. 确保PostgreSQL已安装并运行"
echo "  3. 创建PostgreSQL数据库和用户（如果不存在）"
echo "  4. 初始化PostgreSQL表结构"
echo "  5. 迁移SQLite数据到PostgreSQL"
echo "  6. 更新.env文件配置"
echo "  7. 验证配置和数据"
echo "  8. 重启服务"
echo ""
read -p "是否继续? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

cd "$APP_DIR"

# 1. 检查当前SQLite数据量
echo ""
echo "=========================================="
echo "1. 检查当前SQLite数据量"
echo "=========================================="

source venv/bin/activate

python3 << 'EOF'
import os
os.environ['DATABASE_URL'] = 'sqlite:///./papers.db'
os.environ['BILIBILI_DATABASE_URL'] = 'sqlite:///./bilibili.db'

try:
    from models import get_session, Paper
    session = get_session()
    papers_count = session.query(Paper).count()
    session.close()
    print(f"✅ SQLite论文数据: {papers_count} 篇")
except Exception as e:
    print(f"⚠️  无法查询论文数据: {e}")

try:
    from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
    bilibili_session = get_bilibili_session()
    ups_count = bilibili_session.query(BilibiliUp).count()
    videos_count = bilibili_session.query(BilibiliVideo).count()
    bilibili_session.close()
    print(f"✅ SQLite UP主数据: {ups_count} 个")
    print(f"✅ SQLite视频数据: {videos_count} 个")
except Exception as e:
    print(f"⚠️  无法查询B站数据: {e}")
EOF

# 2. 检查PostgreSQL
echo ""
echo "=========================================="
echo "2. 检查PostgreSQL"
echo "=========================================="

if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓${NC}  PostgreSQL已安装"
    if systemctl is-active --quiet postgresql; then
        echo -e "${GREEN}✓${NC}  PostgreSQL服务运行正常"
    else
        echo "启动PostgreSQL服务..."
        systemctl start postgresql
        sleep 3
        if systemctl is-active --quiet postgresql; then
            echo -e "${GREEN}✅ PostgreSQL服务已启动${NC}"
        else
            echo -e "${RED}❌ PostgreSQL服务启动失败${NC}"
            exit 1
        fi
    fi
else
    echo "安装PostgreSQL..."
    apt update
    apt install -y postgresql postgresql-contrib
    systemctl start postgresql
    systemctl enable postgresql
    echo -e "${GREEN}✅ PostgreSQL安装完成${NC}"
fi

# 3. 创建数据库和用户
echo ""
echo "=========================================="
echo "3. 创建数据库和用户"
echo "=========================================="

DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null || echo "0")

if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${YELLOW}⚠${NC}  数据库 $DB_NAME 已存在"
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

# 4. 安装Python依赖
echo ""
echo "=========================================="
echo "4. 安装Python依赖"
echo "=========================================="

if python3 -c "import psycopg2" 2>/dev/null; then
    echo -e "${GREEN}✓${NC}  psycopg2已安装"
else
    pip install psycopg2-binary
    echo -e "${GREEN}✅ psycopg2安装成功${NC}"
fi

# 5. 初始化PostgreSQL表结构
echo ""
echo "=========================================="
echo "5. 初始化PostgreSQL表结构"
echo "=========================================="

# 编码密码
ENCODED_PASSWORD=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$DB_PASSWORD', safe=''))")

# 设置环境变量
export DATABASE_URL="postgresql://$DB_USER:$ENCODED_PASSWORD@localhost:5432/$DB_NAME"
export BILIBILI_DATABASE_URL="postgresql://$DB_USER:$ENCODED_PASSWORD@localhost:5432/$DB_NAME"

# 初始化表结构
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
    exit 1
fi

# 7. 备份并更新.env文件
echo ""
echo "=========================================="
echo "7. 更新.env文件配置"
echo "=========================================="

# 备份.env文件
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# 删除旧配置
sed -i '/^DATABASE_URL=/d' .env
sed -i '/^BILIBILI_DATABASE_URL=/d' .env

# 添加新配置
echo "" >> .env
echo "# PostgreSQL配置（从SQLite迁移）" >> .env
echo "DATABASE_URL=postgresql://$DB_USER:$ENCODED_PASSWORD@localhost:5432/$DB_NAME" >> .env
echo "BILIBILI_DATABASE_URL=postgresql://$DB_USER:$ENCODED_PASSWORD@localhost:5432/$DB_NAME" >> .env

echo -e "${GREEN}✅ .env文件已更新${NC}"
echo ""
echo "新的配置:"
grep -E "^DATABASE_URL|^BILIBILI_DATABASE_URL" .env | tail -2

# 8. 验证配置和数据
echo ""
echo "=========================================="
echo "8. 验证配置和数据"
echo "=========================================="

# 重新加载.env（确保使用新配置）
export DATABASE_URL="postgresql://$DB_USER:$ENCODED_PASSWORD@localhost:5432/$DB_NAME"
export BILIBILI_DATABASE_URL="postgresql://$DB_USER:$ENCODED_PASSWORD@localhost:5432/$DB_NAME"

python3 << 'EOF'
import os
from models import get_session, Paper
from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo

try:
    # 检查论文数据
    session = get_session()
    papers_count = session.query(Paper).count()
    session.close()
    print(f"✅ PostgreSQL论文数据: {papers_count} 篇")
    
    # 检查B站数据
    bilibili_session = get_bilibili_session()
    ups_count = bilibili_session.query(BilibiliUp).count()
    videos_count = bilibili_session.query(BilibiliVideo).count()
    bilibili_session.close()
    print(f"✅ PostgreSQL UP主数据: {ups_count} 个")
    print(f"✅ PostgreSQL视频数据: {videos_count} 个")
    
    print("\n✅ 数据验证成功！")
except Exception as e:
    print(f"❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
EOF

# 9. 重启服务
echo ""
echo "=========================================="
echo "9. 重启服务"
echo "=========================================="

echo "重启服务使新配置生效..."
systemctl restart embodiedpulse
sleep 5

if systemctl is-active --quiet embodiedpulse; then
    echo -e "${GREEN}✅ 服务重启成功${NC}"
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    echo "查看日志: journalctl -u embodiedpulse -n 50"
    exit 1
fi

# 10. 最终验证
echo ""
echo "=========================================="
echo "10. 最终验证"
echo "=========================================="

echo "检查服务状态..."
systemctl status embodiedpulse --no-pager -l | head -20

echo ""
echo "检查环境变量..."
systemctl show embodiedpulse | grep EnvironmentFile || echo "⚠️  未找到EnvironmentFile配置"

echo ""
echo "=========================================="
echo -e "${GREEN}✅ 迁移完成！${NC}"
echo "=========================================="
echo ""
echo "📝 迁移总结:"
echo "  - SQLite数据已迁移到PostgreSQL"
echo "  - .env文件已更新"
echo "  - 服务已重启"
echo ""
echo "📊 下一步:"
echo "  1. 访问网站验证: https://essay.gradmotion.com"
echo "  2. 检查B站页面: https://blibli.gradmotion.com"
echo "  3. 查看服务日志: journalctl -u embodiedpulse -n 50"
echo ""
echo "💡 提示:"
echo "  - SQLite文件已保留作为备份"
echo "  - 如果遇到问题，可以回滚.env文件: cp .env.backup.* .env"
echo "  - 检查数据库: python3 scripts/check_current_database.py"

