#!/bin/bash
# 服务器端B站数据问题诊断脚本
# 需要在服务器上执行

echo "============================================================"
echo "B站数据问题诊断脚本 - 服务器端"
echo "============================================================"
echo ""

# 设置项目路径（根据实际情况修改）
PROJECT_DIR="/srv/EmbodiedPulse2026"
cd "$PROJECT_DIR" || exit 1

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "【1. 检查项目目录和Python环境】"
echo "----------------------------------------"
echo "项目目录: $PROJECT_DIR"
echo "当前目录: $(pwd)"
echo "Python版本: $(python3 --version)"
echo ""

echo "【2. 测试数据库连接】"
echo "----------------------------------------"
python3 << 'PYEOF'
import sys
import os
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
    from bilibili_models import BILIBILI_DATABASE_URL
    
    print(f"数据库URL: {BILIBILI_DATABASE_URL}")
    
    session = get_bilibili_session()
    up_count = session.query(BilibiliUp).count()
    video_count = session.query(BilibiliVideo).count()
    
    print(f"✅ 数据库连接成功")
    print(f"   UP主总数: {up_count}")
    print(f"   视频总数: {video_count}")
    
    session.close()
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo ""
echo "【3. 测试数据完整性】"
echo "----------------------------------------"
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from sqlalchemy import func

session = get_bilibili_session()

try:
    # 检查孤立视频
    all_video_uids = set([uid[0] for uid in session.query(BilibiliVideo.uid).distinct().all()])
    all_up_uids = set([uid[0] for uid in session.query(BilibiliUp.uid).all()])
    orphan_videos = all_video_uids - all_up_uids
    
    if orphan_videos:
        print(f"⚠️  发现 {len(orphan_videos)} 个孤立视频（UP主不存在）")
        for uid in list(orphan_videos)[:5]:
            count = session.query(BilibiliVideo).filter_by(uid=uid).count()
            print(f"   UID {uid}: {count} 个视频")
    else:
        print("✅ 没有发现孤立视频")
    
    # 检查NULL值
    null_pubdate = session.query(BilibiliVideo).filter(BilibiliVideo.pubdate == None).count()
    null_pubdate_raw = session.query(BilibiliVideo).filter(BilibiliVideo.pubdate_raw == None).count()
    
    if null_pubdate > 0:
        print(f"⚠️  发现 {null_pubdate} 个视频的 pubdate 为 NULL")
    if null_pubdate_raw > 0:
        print(f"⚠️  发现 {null_pubdate_raw} 个视频的 pubdate_raw 为 NULL")
    
    if null_pubdate == 0 and null_pubdate_raw == 0:
        print("✅ 所有视频都有有效的发布时间")
        
except Exception as e:
    print(f"❌ 数据完整性检查失败: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
PYEOF

echo ""
echo "【4. 测试管理后台视频列表查询（模拟API逻辑）】"
echo "----------------------------------------"
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo

session = get_bilibili_session()

try:
    print("测试1: 使用INNER JOIN + pubdate排序（原始代码）")
    try:
        query = session.query(BilibiliVideo, BilibiliUp).join(
            BilibiliUp, BilibiliVideo.uid == BilibiliUp.uid
        ).order_by(BilibiliVideo.pubdate.desc())
        
        total = query.count()
        print(f"   ✅ 查询成功，总记录数: {total}")
        
        results = query.limit(10).all()
        print(f"   ✅ 成功获取前10条记录")
        
        # 检查是否有NULL pubdate
        null_count = sum(1 for video, up in results if video.pubdate is None)
        if null_count > 0:
            print(f"   ⚠️  结果中包含 {null_count} 个 pubdate 为 NULL 的视频")
        
    except Exception as e:
        print(f"   ❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n测试2: 使用INNER JOIN + pubdate_raw排序（修复方案）")
    try:
        query2 = session.query(BilibiliVideo, BilibiliUp).join(
            BilibiliUp, BilibiliVideo.uid == BilibiliUp.uid
        ).order_by(BilibiliVideo.pubdate_raw.desc())
        
        total2 = query2.count()
        print(f"   ✅ 查询成功，总记录数: {total2}")
        
        results2 = query2.limit(10).all()
        print(f"   ✅ 成功获取前10条记录")
        
        # 测试to_dict
        if results2:
            video, up = results2[0]
            try:
                video_dict = video.to_dict()
                video_dict['up_name'] = up.name
                print(f"   ✅ to_dict方法正常")
                print(f"   示例: {video_dict.get('title', '')[:40]}...")
            except Exception as e:
                print(f"   ❌ to_dict失败: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"   ❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
PYEOF

echo ""
echo "【5. 测试实际API端点（需要认证）】"
echo "----------------------------------------"
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

from app import app

with app.test_client() as client:
    # 测试前端API（不需要认证）
    print("测试 /api/bilibili/all")
    response = client.get('/api/bilibili/all?force=1')
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.get_json()
        if data and data.get('success'):
            print(f"   ✅ API返回成功")
            print(f"   数据条数: {len(data.get('data', []))}")
        else:
            print(f"   ❌ API返回失败: {data.get('error', '未知错误') if data else '无数据'}")
    else:
        print(f"   ❌ HTTP错误: {response.status_code}")
        try:
            error_text = response.data.decode('utf-8')[:200]
            print(f"   错误信息: {error_text}")
        except:
            pass
    
    # 测试管理后台API（需要认证，会返回401）
    print("\n测试 /api/admin/bilibili/videos（需要认证）")
    response2 = client.get('/api/admin/bilibili/videos?page=1&per_page=20')
    print(f"   状态码: {response2.status_code}")
    if response2.status_code == 401:
        print("   ⚠️  需要认证（这是正常的）")
    elif response2.status_code == 200:
        print("   ✅ API返回成功（已认证）")
    else:
        print(f"   ❌ HTTP错误: {response2.status_code}")
PYEOF

echo ""
echo "【6. 检查数据新鲜度】"
echo "----------------------------------------"
python3 << 'PYEOF'
import sys
from datetime import datetime
sys.path.insert(0, '/srv/EmbodiedPulse2026')

from bilibili_models import get_bilibili_session, BilibiliUp

session = get_bilibili_session()

try:
    ups = session.query(BilibiliUp).filter_by(is_active=True).all()
    print(f"活跃UP主数量: {len(ups)}")
    
    if not ups:
        print("⚠️  没有活跃的UP主")
    else:
        now = datetime.now()
        stale_count = 0
        
        print("\nUP主数据更新情况（前10个）:")
        for up in ups[:10]:
            if up.last_fetch_at:
                age_hours = (now - up.last_fetch_at).total_seconds() / 3600
                status = "✅" if age_hours < 24 else "⚠️" if age_hours < 168 else "❌"
                print(f"   {status} {up.name}: {age_hours:.1f} 小时前更新")
                
                if age_hours > 24:
                    stale_count += 1
            else:
                print(f"   ❌ {up.name}: 从未更新")
                stale_count += 1
        
        if stale_count == 0:
            print("\n✅ 所有UP主数据都是最新的（24小时内）")
        else:
            print(f"\n⚠️  有 {stale_count} 个UP主数据需要更新")
            
except Exception as e:
    print(f"❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
PYEOF

echo ""
echo "【7. 检查定时任务状态】"
echo "----------------------------------------"
# 检查systemd服务状态
if systemctl is-active --quiet embodiedpulse 2>/dev/null; then
    echo "✅ embodiedpulse 服务正在运行"
    systemctl status embodiedpulse --no-pager -l | head -10
else
    echo "⚠️  embodiedpulse 服务未运行或不存在"
fi

# 检查是否有定时任务相关的进程
echo ""
echo "检查相关进程:"
ps aux | grep -E "fetch_bilibili|scheduler|apscheduler" | grep -v grep || echo "   未发现相关进程"

echo ""
echo "【8. 检查最近的错误日志】"
echo "----------------------------------------"
# 检查应用日志
if [ -f "app.log" ]; then
    echo "最近的错误日志（app.log）:"
    tail -50 app.log | grep -i "error\|exception\|traceback\|bilibili" | tail -20 || echo "   未发现相关错误"
fi

# 检查systemd日志
if systemctl list-unit-files | grep -q embodiedpulse; then
    echo ""
    echo "最近的systemd日志:"
    journalctl -u embodiedpulse --since "24 hours ago" --no-pager | grep -i "error\|exception\|traceback\|bilibili" | tail -20 || echo "   未发现相关错误"
fi

echo ""
echo "============================================================"
echo "诊断完成"
echo "============================================================"

