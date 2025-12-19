#!/bin/bash
# 完整的B站视频数据流检查脚本
# 检查：B站API -> 后端服务 -> 数据库 -> 后端服务 -> 前端

echo "=========================================="
echo "B站视频完整数据流检查"
echo "=========================================="
echo "检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

APP_DIR="/srv/EmbodiedPulse2026"
cd "$APP_DIR"
source venv/bin/activate

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查结果统计
PASSED=0
FAILED=0
WARNINGS=0

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED++))
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

echo "【阶段1: B站API可用性检查】"
echo "=========================================="
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    from bilibili_client import BilibiliClient
    
    print("1.1 测试B站API客户端初始化...")
    client = BilibiliClient()
    print("   ✅ BilibiliClient初始化成功")
    
    # 测试获取逐际动力的数据
    print("\n1.2 测试从B站API获取逐际动力数据...")
    LIMX_UID = 1172054289
    
    try:
        # 获取UP主信息
        print("   正在获取UP主信息...")
        user_info = client.get_user_info(LIMX_UID)
        if user_info:
            print(f"   ✅ 获取UP主信息成功")
            print(f"      - 名称: {user_info.get('name', 'N/A')}")
            print(f"      - 粉丝数: {user_info.get('fans', 0):,}")
        else:
            print(f"   ❌ 获取UP主信息失败")
    except Exception as e:
        print(f"   ❌ 获取UP主信息异常: {e}")
    
    try:
        # 获取视频列表
        print("\n   正在获取视频列表（前5个）...")
        videos = client.get_user_videos(LIMX_UID, video_count=5)
        if videos and len(videos) > 0:
            print(f"   ✅ 获取视频列表成功")
            print(f"      - 视频数量: {len(videos)}")
            latest = videos[0]
            print(f"      - 最新视频: {latest.get('title', 'N/A')[:50]}")
            print(f"      - 播放量: {latest.get('play', 0):,}")
        else:
            print(f"   ⚠️  获取视频列表为空")
    except Exception as e:
        print(f"   ❌ 获取视频列表异常: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ B站API客户端测试失败: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo ""
echo "【阶段2: 数据库连接和数据检查】"
echo "=========================================="
python3 << 'PYEOF'
import sys
import os
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    from bilibili_models import BILIBILI_DATABASE_URL, get_bilibili_session, get_bilibili_engine, BilibiliUp, BilibiliVideo
    from sqlalchemy import text
    
    print("2.1 检查数据库配置...")
    print(f"   数据库URL: {BILIBILI_DATABASE_URL}")
    
    if BILIBILI_DATABASE_URL.startswith('sqlite'):
        db_file = BILIBILI_DATABASE_URL.replace('sqlite:///', '').replace('sqlite:///', '')
        if os.path.isabs(db_file):
            print(f"   ✅ 使用绝对路径: {db_file}")
        else:
            cwd = os.getcwd()
            abs_path = os.path.join(cwd, db_file)
            print(f"   ⚠️  使用相对路径: {db_file}")
            print(f"   实际路径: {abs_path}")
    
    print("\n2.2 测试数据库连接...")
    try:
        engine = get_bilibili_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("   ✅ 数据库连接成功")
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    
    print("\n2.3 检查数据库数据...")
    session = get_bilibili_session()
    try:
        up_count = session.query(BilibiliUp).count()
        video_count = session.query(BilibiliVideo).count()
        print(f"   ✅ 数据统计:")
        print(f"      - UP主数量: {up_count}")
        print(f"      - 视频数量: {video_count}")
        
        # 检查逐际动力的数据
        print("\n2.4 检查逐际动力数据...")
        LIMX_UID = 1172054289
        limx_up = session.query(BilibiliUp).filter_by(uid=LIMX_UID).first()
        
        if limx_up:
            print(f"   ✅ 找到逐际动力数据:")
            print(f"      - 名称: {limx_up.name}")
            print(f"      - 粉丝数: {limx_up.fans:,}")
            print(f"      - 视频数: {limx_up.videos_count}")
            print(f"      - 总播放量: {limx_up.views_count:,}")
            
            # 检查最新视频
            latest_video = session.query(BilibiliVideo).filter_by(
                uid=LIMX_UID, is_deleted=False
            ).order_by(BilibiliVideo.pubdate.desc()).first()
            
            if latest_video:
                print(f"\n   ✅ 最新视频:")
                print(f"      - BV号: {latest_video.bvid}")
                print(f"      - 标题: {latest_video.title[:50]}...")
                print(f"      - 播放量: {latest_video.play:,}")
                print(f"      - 发布时间: {latest_video.pubdate}")
                print(f"      - 更新时间: {latest_video.updated_at}")
            else:
                print(f"   ⚠️  未找到逐际动力的视频数据")
        else:
            print(f"   ❌ 未找到逐际动力数据")
    finally:
        session.close()
        
except Exception as e:
    print(f"❌ 数据库检查失败: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo ""
echo "【阶段3: 后端API服务检查】"
echo "=========================================="
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    from app import app
    
    print("3.1 测试后端API端点 /api/bilibili/all...")
    with app.test_client() as client:
        response = client.get('/api/bilibili/all?force=1')
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            if data and data.get('success'):
                cards = data.get('data', [])
                print(f"   ✅ API返回成功")
                print(f"      - UP主数量: {len(cards)}")
                
                # 检查数据格式
                if cards:
                    first_card = cards[0]
                    print(f"\n   3.2 检查数据格式...")
                    print(f"      - user_info存在: {bool(first_card.get('user_info'))}")
                    print(f"      - videos存在: {bool(first_card.get('videos'))}")
                    print(f"      - 视频数量: {len(first_card.get('videos', []))}")
                    
                    # 检查逐际动力的数据
                    print(f"\n   3.3 检查逐际动力数据...")
                    LIMX_UID = 1172054289
                    limx_card = next((c for c in cards if c.get('user_info', {}).get('mid') == LIMX_UID), None)
                    
                    if limx_card:
                        print(f"      ✅ 找到逐际动力数据")
                        user_info = limx_card.get('user_info', {})
                        videos = limx_card.get('videos', [])
                        print(f"      - 名称: {user_info.get('name', 'N/A')}")
                        print(f"      - 视频数量: {len(videos)}")
                        
                        if videos:
                            latest = videos[0]
                            print(f"\n      最新视频:")
                            print(f"      - BV号: {latest.get('bvid', 'N/A')}")
                            print(f"      - 标题: {latest.get('title', 'N/A')[:50]}...")
                            print(f"      - 播放量(play): {latest.get('play', 'N/A')}")
                            print(f"      - 播放量(play_raw): {latest.get('play_raw', 'N/A')}")
                            print(f"      - 发布时间: {latest.get('pubdate', 'N/A')}")
                        else:
                            print(f"      ⚠️  视频列表为空")
                    else:
                        print(f"      ❌ 未找到逐际动力数据")
                else:
                    print(f"   ⚠️  数据为空")
            else:
                error_msg = data.get('error', '未知错误') if data else '无数据'
                print(f"   ❌ API返回失败: {error_msg}")
                if data:
                    print(f"      完整响应: {data}")
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            try:
                error_text = response.data.decode('utf-8')
                print(f"      错误内容: {error_text[:500]}")
            except:
                print(f"      响应数据: {response.data[:500]}")
                
except Exception as e:
    print(f"❌ 后端API测试失败: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo ""
echo "【阶段4: 前端页面检查】"
echo "=========================================="
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    from app import app
    
    print("4.1 测试前端页面路由 /bilibili...")
    with app.test_client() as client:
        response = client.get('/bilibili')
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            content = response.data.decode('utf-8')
            print(f"   ✅ 页面返回成功")
            print(f"      - 页面大小: {len(content)} 字节")
            
            # 检查关键元素
            print(f"\n   4.2 检查页面关键元素...")
            checks = {
                'bilibili': 'bilibili' in content.lower(),
                'latest-video-title': 'latest-video-title' in content,
                'api/bilibili/all': '/api/bilibili/all' in content or 'api/bilibili/all' in content,
                'loadBilibiliAll': 'loadBilibiliAll' in content,
                'renderLatestVideos': 'renderLatestVideos' in content,
            }
            
            for key, found in checks.items():
                if found:
                    print(f"      ✅ {key}: 存在")
                else:
                    print(f"      ❌ {key}: 缺失")
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            print(f"      响应: {response.data.decode('utf-8')[:500]}")
            
except Exception as e:
    print(f"❌ 前端页面测试失败: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo ""
echo "【阶段5: 数据一致性检查】"
echo "=========================================="
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    from app import app
    from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
    
    LIMX_UID = 1172054289
    
    print("5.1 比较数据库和API返回的数据...")
    
    # 从数据库获取
    session = get_bilibili_session()
    try:
        db_up = session.query(BilibiliUp).filter_by(uid=LIMX_UID).first()
        db_latest_video = session.query(BilibiliVideo).filter_by(
            uid=LIMX_UID, is_deleted=False
        ).order_by(BilibiliVideo.pubdate.desc()).first()
    finally:
        session.close()
    
    # 从API获取
    with app.test_client() as client:
        response = client.get('/api/bilibili/all?force=1')
        if response.status_code == 200:
            data = response.get_json()
            if data and data.get('success'):
                cards = data.get('data', [])
                api_card = next((c for c in cards if c.get('user_info', {}).get('mid') == LIMX_UID), None)
                
                if db_up and api_card:
                    print(f"   ✅ 数据库和API都有数据")
                    
                    # 比较UP主信息
                    print(f"\n   5.2 比较UP主信息...")
                    api_user = api_card.get('user_info', {})
                    print(f"      数据库 - 名称: {db_up.name}, 粉丝数: {db_up.fans:,}")
                    print(f"      API    - 名称: {api_user.get('name', 'N/A')}, 粉丝数: {api_user.get('fans_raw', 'N/A')}")
                    
                    # 比较最新视频
                    if db_latest_video:
                        api_videos = api_card.get('videos', [])
                        if api_videos:
                            api_latest = api_videos[0]
                            print(f"\n   5.3 比较最新视频...")
                            print(f"      数据库:")
                            print(f"      - BV号: {db_latest_video.bvid}")
                            print(f"      - 标题: {db_latest_video.title[:50]}...")
                            print(f"      - 播放量: {db_latest_video.play:,}")
                            print(f"      API:")
                            print(f"      - BV号: {api_latest.get('bvid', 'N/A')}")
                            print(f"      - 标题: {api_latest.get('title', 'N/A')[:50]}...")
                            print(f"      - 播放量(play_raw): {api_latest.get('play_raw', 'N/A')}")
                            
                            # 检查一致性
                            if db_latest_video.bvid == api_latest.get('bvid'):
                                print(f"      ✅ BV号一致")
                            else:
                                print(f"      ⚠️  BV号不一致")
                            
                            if db_latest_video.play == api_latest.get('play_raw'):
                                print(f"      ✅ 播放量一致")
                            else:
                                print(f"      ⚠️  播放量不一致: 数据库={db_latest_video.play:,}, API={api_latest.get('play_raw', 'N/A')}")
                        else:
                            print(f"      ⚠️  API返回的视频列表为空")
                    else:
                        print(f"      ⚠️  数据库中未找到最新视频")
                else:
                    print(f"   ❌ 数据不完整")
                    if not db_up:
                        print(f"      - 数据库中未找到逐际动力")
                    if not api_card:
                        print(f"      - API中未找到逐际动力")
                        
except Exception as e:
    print(f"❌ 数据一致性检查失败: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo ""
echo "【阶段6: 服务状态检查】"
echo "=========================================="
echo "6.1 检查systemd服务状态..."
systemctl is-active embodiedpulse > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ 服务正在运行"
    systemctl status embodiedpulse --no-pager -l | head -10
else
    echo "   ❌ 服务未运行"
fi

echo ""
echo "6.2 检查最近的错误日志..."
ERROR_COUNT=$(journalctl -u embodiedpulse --since "1 hour ago" --no-pager | grep -i "error\|exception\|traceback" | wc -l)
if [ $ERROR_COUNT -eq 0 ]; then
    echo "   ✅ 最近1小时无错误"
else
    echo "   ⚠️  最近1小时有 $ERROR_COUNT 条错误日志"
    echo "   最近的错误:"
    journalctl -u embodiedpulse --since "1 hour ago" --no-pager | grep -i "error\|exception\|traceback" | tail -5
fi

echo ""
echo "6.3 检查B站相关的请求日志..."
BILIBILI_REQUESTS=$(journalctl -u embodiedpulse --since "1 hour ago" --no-pager | grep -i "bilibili\|/api/bilibili" | wc -l)
echo "   最近1小时的B站相关请求: $BILIBILI_REQUESTS 条"

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="
echo ""
echo "总结:"
echo "  - 通过: $PASSED"
echo "  - 失败: $FAILED"
echo "  - 警告: $WARNINGS"
echo ""

