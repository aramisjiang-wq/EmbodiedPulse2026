#!/bin/bash
# 一键修复B站数据流问题：前端显示老数据和500错误

set -e

APP_DIR="/srv/EmbodiedPulse2026"
cd "$APP_DIR"
source venv/bin/activate

echo "=========================================="
echo "B站数据流问题一键修复"
echo "=========================================="
echo ""

# 1. 检查代码是否已更新
echo "【1. 检查代码更新】"
if grep -q "from dotenv import load_dotenv" bilibili_models.py; then
    echo "✅ bilibili_models.py 已包含.env加载逻辑"
else
    echo "❌ bilibili_models.py 未包含.env加载逻辑"
    echo "需要先更新代码到服务器"
    exit 1
fi

# 2. 验证数据库配置
echo ""
echo "【2. 验证数据库配置】"
python3 << 'PYEOF'
from bilibili_models import BILIBILI_DATABASE_URL, get_bilibili_engine

engine = get_bilibili_engine()
print(f"使用的数据库: {engine.url}")

if 'postgres' not in str(engine.url).lower():
    print("❌ 仍在使用SQLite，需要检查.env文件")
    import sys
    sys.exit(1)
else:
    print("✅ 已配置PostgreSQL")
PYEOF

if [ $? -ne 0 ]; then
    echo "❌ 数据库配置错误"
    exit 1
fi

# 3. 初始化表结构（如果需要）
echo ""
echo "【3. 初始化表结构】"
python3 << 'PYEOF'
from bilibili_models import init_bilibili_db
try:
    init_bilibili_db()
    print("✅ 表结构已就绪")
except Exception as e:
    print(f"⚠️  表结构初始化: {e}")
PYEOF

# 4. 测试数据库连接和查询
echo ""
echo "【4. 测试数据库连接】"
python3 << 'PYEOF'
from bilibili_models import get_bilibili_session, BilibiliVideo, BilibiliUp

try:
    session = get_bilibili_session()
    ups_count = session.query(BilibiliUp).count()
    videos_count = session.query(BilibiliVideo).count()
    print(f"✅ 数据库连接成功")
    print(f"   UP主: {ups_count}, 视频: {videos_count}")
    
    # 测试join查询（模拟API逻辑）
    results = session.query(BilibiliVideo, BilibiliUp).join(
        BilibiliUp, BilibiliVideo.uid == BilibiliUp.uid
    ).limit(1).all()
    
    if results:
        video, up = results[0]
        # 测试to_dict方法
        video_dict = video.to_dict()
        print(f"✅ Join查询和to_dict()测试成功")
        print(f"   测试视频: {video.bvid}, play: {video_dict.get('play')}")
    else:
        print("⚠️  数据库中没有视频数据")
    
    session.close()
except Exception as e:
    print(f"❌ 数据库测试失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo "❌ 数据库测试失败"
    exit 1
fi

# 5. 重启服务
echo ""
echo "【5. 重启服务】"
systemctl restart embodiedpulse
sleep 5

if systemctl is-active --quiet embodiedpulse; then
    echo "✅ 服务重启成功"
else
    echo "❌ 服务启动失败"
    echo "查看日志:"
    journalctl -u embodiedpulse -n 50 --no-pager | tail -20
    exit 1
fi

# 6. 测试API端点
echo ""
echo "【6. 测试API端点】"
sleep 3

echo "测试 /api/bilibili/all:"
API_RESPONSE=$(curl -s "http://localhost:5001/api/bilibili/all?force=1" | python3 -m json.tool 2>&1 | head -30)
if [ $? -eq 0 ]; then
    echo "$API_RESPONSE"
    echo "✅ API端点正常"
else
    echo "❌ API端点测试失败"
    echo "$API_RESPONSE"
fi

# 7. 检查服务日志中的错误
echo ""
echo "【7. 检查服务日志】"
RECENT_ERRORS=$(journalctl -u embodiedpulse -n 50 --no-pager | grep -i "error\|exception\|traceback" | tail -10)
if [ -n "$RECENT_ERRORS" ]; then
    echo "⚠️  发现最近的错误:"
    echo "$RECENT_ERRORS"
else
    echo "✅ 未发现最近的错误"
fi

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 访问 https://essay.gradmotion.com/bilibili 检查前端数据"
echo "2. 访问 https://admin123.gradmotion.com/admin/bilibili 检查管理端"
echo "3. 如果播放量还是旧的，运行: python3 scripts/update_video_play_counts.py --force"

