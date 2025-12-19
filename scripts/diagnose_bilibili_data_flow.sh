#!/bin/bash
# 诊断B站数据流问题：前端显示老数据和500错误

set -e

APP_DIR="/srv/EmbodiedPulse2026"
cd "$APP_DIR"
source venv/bin/activate

echo "=========================================="
echo "B站数据流完整诊断"
echo "=========================================="
echo ""

# 1. 检查代码是否已更新
echo "【1. 检查代码更新】"
if grep -q "from dotenv import load_dotenv" bilibili_models.py; then
    echo "✅ bilibili_models.py 已包含.env加载逻辑"
else
    echo "❌ bilibili_models.py 未包含.env加载逻辑"
    echo "需要更新代码"
fi

# 2. 检查实际使用的数据库
echo ""
echo "【2. 检查实际使用的数据库】"
python3 << 'PYEOF'
import os
from bilibili_models import BILIBILI_DATABASE_URL, get_bilibili_engine

print(f"代码中的BILIBILI_DATABASE_URL: {BILIBILI_DATABASE_URL}")
engine = get_bilibili_engine()
print(f"实际使用的数据库: {engine.url}")

if 'postgres' in str(engine.url).lower():
    print("✅ 使用PostgreSQL")
else:
    print("❌ 使用SQLite（需要切换到PostgreSQL）")
PYEOF

# 3. 测试数据库连接
echo ""
echo "【3. 测试数据库连接】"
python3 << 'PYEOF'
try:
    from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
    
    session = get_bilibili_session()
    
    # 测试查询
    ups_count = session.query(BilibiliUp).count()
    videos_count = session.query(BilibiliVideo).count()
    
    print(f"✅ 数据库连接成功")
    print(f"   UP主数量: {ups_count}")
    print(f"   视频数量: {videos_count}")
    
    # 查询特定视频
    video = session.query(BilibiliVideo).filter_by(bvid='BV1L8qEBKEFW').first()
    if video:
        print(f"✅ 找到视频 BV1L8qEBKEFW:")
        print(f"   play: {video.play:,}")
        print(f"   play_formatted: {video.play_formatted}")
    else:
        print("⚠️  未找到视频 BV1L8qEBKEFW")
    
    session.close()
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    import traceback
    traceback.print_exc()
PYEOF

# 4. 测试API端点（模拟）
echo ""
echo "【4. 测试API端点逻辑】"
python3 << 'PYEOF'
try:
    from bilibili_models import get_bilibili_session, BilibiliVideo, BilibiliUp
    
    session = get_bilibili_session()
    
    try:
        # 模拟 /api/admin/bilibili/videos 的逻辑
        page = 1
        per_page = 20
        
        query = session.query(BilibiliVideo).filter(BilibiliVideo.is_deleted == False)
        total = query.count()
        videos = query.order_by(BilibiliVideo.pubdate.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        print(f"✅ API逻辑测试成功")
        print(f"   总视频数: {total}")
        print(f"   当前页视频数: {len(videos)}")
        
        if videos:
            video = videos[0]
            print(f"   第一条视频:")
            print(f"     BV号: {video.bvid}")
            print(f"     标题: {video.title[:50]}...")
            print(f"     播放量: {video.play:,}")
            
            # 测试to_dict方法
            try:
                video_dict = video.to_dict()
                print(f"   to_dict()成功")
                print(f"     play字段: {video_dict.get('play')}")
                print(f"     play_raw字段: {video_dict.get('play_raw')}")
            except Exception as e:
                print(f"   ❌ to_dict()失败: {e}")
                import traceback
                traceback.print_exc()
        
    finally:
        session.close()
        
except Exception as e:
    print(f"❌ API逻辑测试失败: {e}")
    import traceback
    traceback.print_exc()
PYEOF

# 5. 检查服务状态和日志
echo ""
echo "【5. 检查服务状态】"
if systemctl is-active --quiet embodiedpulse; then
    echo "✅ 服务正在运行"
else
    echo "❌ 服务未运行"
fi

echo ""
echo "【6. 检查最近的错误日志】"
journalctl -u embodiedpulse -n 50 --no-pager | grep -i "error\|exception\|traceback\|bilibili" | tail -20 || echo "未找到相关错误日志"

# 7. 测试实际API端点
echo ""
echo "【7. 测试实际API端点】"
echo "测试 /api/bilibili/all:"
curl -s "http://localhost:5001/api/bilibili/all?force=1" | python3 -m json.tool | head -50 || echo "API请求失败"

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="

