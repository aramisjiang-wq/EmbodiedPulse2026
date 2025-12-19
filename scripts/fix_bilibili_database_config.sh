#!/bin/bash
# 修复B站数据库配置：确保使用PostgreSQL而不是SQLite

set -e

APP_DIR="/srv/EmbodiedPulse2026"
cd "$APP_DIR"

echo "=========================================="
echo "修复B站数据库配置"
echo "=========================================="
echo ""

# 1. 检查.env文件
echo "【1. 检查.env文件】"
if [ ! -f .env ]; then
    echo "❌ .env文件不存在"
    exit 1
fi

BILIBILI_DB_URL=$(grep "^BILIBILI_DATABASE_URL=" .env | head -1 | cut -d'=' -f2-)
if [ -z "$BILIBILI_DB_URL" ]; then
    echo "❌ .env文件中未找到BILIBILI_DATABASE_URL配置"
    exit 1
fi

if echo "$BILIBILI_DB_URL" | grep -qi "postgres"; then
    echo "✅ .env文件配置了PostgreSQL"
else
    echo "⚠️  .env文件配置的不是PostgreSQL"
fi

# 2. 检查代码是否已修复
echo ""
echo "【2. 检查代码修复】"
if grep -q "from dotenv import load_dotenv" bilibili_models.py; then
    echo "✅ 代码已包含.env文件加载逻辑"
else
    echo "❌ 代码未包含.env文件加载逻辑，需要更新"
    exit 1
fi

# 3. 验证修复后的代码
echo ""
echo "【3. 验证修复后的代码】"
source venv/bin/activate

python3 << 'PYEOF'
from bilibili_models import BILIBILI_DATABASE_URL, get_bilibili_engine

print(f"代码中的BILIBILI_DATABASE_URL: {BILIBILI_DATABASE_URL}")
engine = get_bilibili_engine()
print(f"实际使用的数据库: {engine.url}")

if 'postgres' in str(engine.url).lower():
    print("✅ 已切换到PostgreSQL")
else:
    print("❌ 仍在使用SQLite")
    exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo "❌ 验证失败"
    exit 1
fi

# 4. 重启服务
echo ""
echo "【4. 重启服务】"
systemctl restart embodiedpulse
sleep 5

if systemctl is-active --quiet embodiedpulse; then
    echo "✅ 服务重启成功"
else
    echo "❌ 服务启动失败"
    echo "查看日志: journalctl -u embodiedpulse -n 50"
    exit 1
fi

# 5. 验证服务使用的数据库
echo ""
echo "【5. 验证服务使用的数据库】"
sleep 3

python3 << 'PYEOF'
from bilibili_models import BILIBILI_DATABASE_URL, get_bilibili_engine

engine = get_bilibili_engine()
print(f"服务使用的数据库: {engine.url}")

if 'postgres' in str(engine.url).lower():
    print("✅ 服务已使用PostgreSQL")
    
    # 查询数据
    from bilibili_models import get_bilibili_session, BilibiliVideo
    session = get_bilibili_session()
    video = session.query(BilibiliVideo).filter_by(bvid='BV1L8qEBKEFW').first()
    if video:
        print(f"✅ PostgreSQL数据库中的视频:")
        print(f"   play: {video.play:,}")
        print(f"   play_formatted: {video.play_formatted}")
    session.close()
else:
    print("❌ 服务仍在使用SQLite")
    exit(1)
PYEOF

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "下一步：更新PostgreSQL数据库中的播放量数据"
echo "运行: python3 scripts/update_video_play_counts.py --force"

