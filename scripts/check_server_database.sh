#!/bin/bash
# 检查服务器当前数据库类型和数据量

set -e

APP_DIR="/srv/EmbodiedPulse2026"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "服务器数据库检查"
echo "=========================================="
echo ""

cd "$APP_DIR"

# 检查.env文件
if [ -f ".env" ]; then
    echo "📄 .env文件配置:"
    echo "   DATABASE_URL: $(grep '^DATABASE_URL=' .env | head -1 | cut -d'=' -f2- || echo '未设置')"
    echo "   BILIBILI_DATABASE_URL: $(grep '^BILIBILI_DATABASE_URL=' .env | head -1 | cut -d'=' -f2- || echo '未设置')"
    echo ""
else
    echo -e "${YELLOW}⚠${NC}  .env文件不存在"
    echo ""
fi

# 检查SQLite文件
echo "📁 SQLite文件检查:"
if [ -f "papers.db" ]; then
    PAPERS_SIZE=$(du -h papers.db | cut -f1)
    echo -e "   ${GREEN}✓${NC}  papers.db 存在 (大小: $PAPERS_SIZE)"
else
    echo -e "   ${YELLOW}⚠${NC}  papers.db 不存在"
fi

if [ -f "bilibili.db" ]; then
    BILIBILI_SIZE=$(du -h bilibili.db | cut -f1)
    echo -e "   ${GREEN}✓${NC}  bilibili.db 存在 (大小: $BILIBILI_SIZE)"
else
    echo -e "   ${YELLOW}⚠${NC}  bilibili.db 不存在"
fi
echo ""

# 检查PostgreSQL
echo "🐘 PostgreSQL检查:"
if command -v psql &> /dev/null; then
    echo -e "   ${GREEN}✓${NC}  PostgreSQL已安装"
    if systemctl is-active --quiet postgresql 2>/dev/null; then
        echo -e "   ${GREEN}✓${NC}  PostgreSQL服务运行中"
        
        # 检查数据库是否存在
        DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='embodied_pulse'" 2>/dev/null || echo "0")
        if [ "$DB_EXISTS" = "1" ]; then
            echo -e "   ${GREEN}✓${NC}  数据库 'embodied_pulse' 存在"
        else
            echo -e "   ${YELLOW}⚠${NC}  数据库 'embodied_pulse' 不存在"
        fi
    else
        echo -e "   ${YELLOW}⚠${NC}  PostgreSQL服务未运行"
    fi
else
    echo -e "   ${YELLOW}⚠${NC}  PostgreSQL未安装"
fi
echo ""

# 检查数据量
echo "📊 数据量统计:"
echo ""

source venv/bin/activate

# 检查当前使用的数据库
python3 << 'EOF'
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

print("=" * 60)
print("当前数据库配置和数据量")
print("=" * 60)
print()

# 1. 检查具身论文数据库
papers_db_url = os.getenv('DATABASE_URL', 'sqlite:///./papers.db')
print("📚 具身论文数据库:")
print(f"   配置: {papers_db_url}")

if papers_db_url.startswith('postgresql://') or papers_db_url.startswith('postgres://'):
    print("   ✅ 使用: PostgreSQL")
    try:
        from models import get_session, Paper
        session = get_session()
        papers_count = session.query(Paper).count()
        session.close()
        print(f"   📊 论文数量: {papers_count} 篇")
    except Exception as e:
        print(f"   ❌ 无法查询: {e}")
else:
    print("   ✅ 使用: SQLite")
    import os.path
    db_file = papers_db_url.replace('sqlite:///', '').replace('sqlite:///', '')
    if os.path.exists(db_file):
        size = os.path.getsize(db_file) / (1024 * 1024)
        print(f"   文件: {db_file}")
        print(f"   大小: {size:.2f} MB")
        try:
            from models import get_session, Paper
            session = get_session()
            papers_count = session.query(Paper).count()
            session.close()
            print(f"   📊 论文数量: {papers_count} 篇")
        except Exception as e:
            print(f"   ❌ 无法查询: {e}")
    else:
        print(f"   ⚠️  文件不存在: {db_file}")

print()

# 2. 检查具身视频数据库
bilibili_db_url = os.getenv('BILIBILI_DATABASE_URL', 'sqlite:///./bilibili.db')
print("📹 具身视频数据库:")
print(f"   配置: {bilibili_db_url}")

if bilibili_db_url.startswith('postgresql://') or bilibili_db_url.startswith('postgres://'):
    print("   ✅ 使用: PostgreSQL")
    try:
        from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
        bilibili_session = get_bilibili_session()
        ups_count = bilibili_session.query(BilibiliUp).count()
        videos_count = bilibili_session.query(BilibiliVideo).count()
        bilibili_session.close()
        print(f"   📊 UP主数量: {ups_count} 个")
        print(f"   📊 视频数量: {videos_count} 个")
    except Exception as e:
        print(f"   ❌ 无法查询: {e}")
else:
    print("   ✅ 使用: SQLite")
    db_file = bilibili_db_url.replace('sqlite:///', '').replace('sqlite:///', '')
    if os.path.exists(db_file):
        size = os.path.getsize(db_file) / (1024 * 1024)
        print(f"   文件: {db_file}")
        print(f"   大小: {size:.2f} MB")
        try:
            from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
            bilibili_session = get_bilibili_session()
            ups_count = bilibili_session.query(BilibiliUp).count()
            videos_count = bilibili_session.query(BilibiliVideo).count()
            bilibili_session.close()
            print(f"   📊 UP主数量: {ups_count} 个")
            print(f"   📊 视频数量: {videos_count} 个")
        except Exception as e:
            print(f"   ❌ 无法查询: {e}")
    else:
        print(f"   ⚠️  文件不存在: {db_file}")

print()
print("=" * 60)
EOF

echo ""
echo "✅ 检查完成"

