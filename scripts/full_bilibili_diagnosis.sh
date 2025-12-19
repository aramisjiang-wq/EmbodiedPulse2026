#!/bin/bash
# 完整的B站数据问题诊断脚本
# 检查：后端代码、数据库、数据更新链路、缓存等

cd /srv/EmbodiedPulse2026 || exit 1

echo "============================================================"
echo "B站数据完整诊断报告"
echo "日期: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"
echo ""

# ==================== 1. 服务状态检查 ====================
echo "【1. 服务状态检查】"
echo "============================================================"
echo ""

echo "1.1 检查服务运行状态"
echo "----------------------------------------"
if systemctl is-active --quiet embodiedpulse; then
    echo "✅ 服务正在运行"
    systemctl status embodiedpulse --no-pager -l | head -15
else
    echo "❌ 服务未运行"
    systemctl status embodiedpulse --no-pager -l | head -15
fi

echo ""
echo "1.2 检查Gunicorn进程"
echo "----------------------------------------"
ps aux | grep gunicorn | grep -v grep || echo "⚠️  未发现Gunicorn进程"

echo ""
echo "1.3 检查端口占用"
echo "----------------------------------------"
netstat -tlnp | grep 5001 || echo "⚠️  端口5001未监听"

echo ""
echo "1.4 检查最近的错误日志"
echo "----------------------------------------"
journalctl -u embodiedpulse --since "1 hour ago" --no-pager | grep -i "error\|exception\|traceback" | tail -20 || echo "   最近1小时无错误"

# ==================== 2. 代码检查 ====================
echo ""
echo "【2. 代码检查】"
echo "============================================================"
echo ""

echo "2.1 检查代码语法"
echo "----------------------------------------"
python3 -m py_compile bilibili_models.py 2>&1 && echo "✅ bilibili_models.py 语法正确" || {
    echo "❌ bilibili_models.py 有语法错误:"
    python3 -m py_compile bilibili_models.py 2>&1 | head -5
}

python3 -m py_compile auth_routes.py 2>&1 && echo "✅ auth_routes.py 语法正确" || {
    echo "❌ auth_routes.py 有语法错误:"
    python3 -m py_compile auth_routes.py 2>&1 | head -5
}

python3 -m py_compile app.py 2>&1 && echo "✅ app.py 语法正确" || {
    echo "❌ app.py 有语法错误:"
    python3 -m py_compile app.py 2>&1 | head -5
}

echo ""
echo "2.2 检查关键代码修复"
echo "----------------------------------------"
if grep -q "try:" bilibili_models.py && grep -A 3 "try:" bilibili_models.py | grep -q "from bilibili_client import format_number"; then
    echo "✅ bilibili_models.py 包含format_number修复"
else
    echo "❌ bilibili_models.py 缺少format_number修复"
fi

if grep -q "pubdate_raw.desc().nullslast()" auth_routes.py; then
    echo "✅ auth_routes.py 使用pubdate_raw排序"
else
    echo "⚠️  auth_routes.py 可能使用pubdate排序"
fi

# ==================== 3. 数据库检查 ====================
echo ""
echo "【3. 数据库检查】"
echo "============================================================"
echo ""

python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    from bilibili_models import BILIBILI_DATABASE_URL, get_bilibili_session, BilibiliUp, BilibiliVideo
    from sqlalchemy import func
    from datetime import datetime
    
    print("3.1 数据库配置")
    print("----------------------------------------")
    print(f"数据库URL: {BILIBILI_DATABASE_URL}")
    
    print("\n3.2 数据库连接测试")
    print("----------------------------------------")
    session = get_bilibili_session()
    try:
        up_count = session.query(BilibiliUp).count()
        video_count = session.query(BilibiliVideo).count()
        print(f"✅ 数据库连接成功")
        print(f"   UP主总数: {up_count}")
        print(f"   视频总数: {video_count}")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n3.3 数据完整性检查")
    print("----------------------------------------")
    # 检查孤立视频
    all_video_uids = set([uid[0] for uid in session.query(BilibiliVideo.uid).distinct().all()])
    all_up_uids = set([uid[0] for uid in session.query(BilibiliUp.uid).all()])
    orphan_videos = all_video_uids - all_up_uids
    
    if orphan_videos:
        print(f"⚠️  发现 {len(orphan_videos)} 个孤立视频（UP主不存在）")
    else:
        print("✅ 没有孤立视频")
    
    # 检查NULL值
    null_pubdate = session.query(BilibiliVideo).filter(BilibiliVideo.pubdate == None).count()
    null_pubdate_raw = session.query(BilibiliVideo).filter(BilibiliVideo.pubdate_raw == None).count()
    
    if null_pubdate > 0:
        print(f"⚠️  发现 {null_pubdate} 个视频的 pubdate 为 NULL")
    if null_pubdate_raw > 0:
        print(f"⚠️  发现 {null_pubdate_raw} 个视频的 pubdate_raw 为 NULL")
    if null_pubdate == 0 and null_pubdate_raw == 0:
        print("✅ 所有视频都有有效的发布时间")
    
    print("\n3.4 数据新鲜度检查")
    print("----------------------------------------")
    ups = session.query(BilibiliUp).filter_by(is_active=True).all()
    now = datetime.now()
    stale_count = 0
    very_stale_count = 0
    
    print(f"活跃UP主数量: {len(ups)}")
    print("\nUP主数据更新情况:")
    for up in ups[:15]:
        if up.last_fetch_at:
            age_hours = (now - up.last_fetch_at).total_seconds() / 3600
            age_days = age_hours / 24
            if age_hours < 24:
                status = "✅"
            elif age_hours < 168:  # 7天
                status = "⚠️"
                stale_count += 1
            else:
                status = "❌"
                very_stale_count += 1
            
            print(f"   {status} {up.name}: {age_days:.1f} 天前更新 (最后更新: {up.last_fetch_at.strftime('%Y-%m-%d %H:%M:%S')})")
            
            if up.fetch_error:
                print(f"      错误信息: {up.fetch_error[:100]}")
        else:
            print(f"   ❌ {up.name}: 从未更新")
            very_stale_count += 1
    
    if stale_count == 0 and very_stale_count == 0:
        print("\n✅ 所有UP主数据都是最新的（24小时内）")
    else:
        print(f"\n⚠️  有 {stale_count} 个UP主数据需要更新（超过1天）")
        print(f"❌  有 {very_stale_count} 个UP主数据严重过时（超过7天或从未更新）")
    
    print("\n3.5 最新视频检查")
    print("----------------------------------------")
    # 检查最近7天的视频
    seven_days_ago = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = seven_days_ago.replace(day=seven_days_ago.day - 7)
    
    recent_videos = session.query(BilibiliVideo).filter(
        BilibiliVideo.pubdate >= seven_days_ago,
        BilibiliVideo.is_deleted == False
    ).order_by(BilibiliVideo.pubdate.desc()).limit(10).all()
    
    print(f"最近7天发布的视频数量: {len(recent_videos)}")
    if recent_videos:
        print("\n最新10个视频:")
        for i, video in enumerate(recent_videos[:10], 1):
            print(f"   {i}. {video.bvid}: {video.title[:50]}...")
            print(f"      发布时间: {video.pubdate.strftime('%Y-%m-%d %H:%M:%S') if video.pubdate else 'N/A'}")
            print(f"      播放量: {video.play:,}")
    else:
        print("⚠️  最近7天没有新视频")
    
    print("\n3.6 逐际动力数据检查（重点）")
    print("----------------------------------------")
    limx_uid = 1172054289
    limx_up = session.query(BilibiliUp).filter_by(uid=limx_uid).first()
    
    if limx_up:
        print(f"UP主: {limx_up.name}")
        print(f"粉丝数: {limx_up.fans:,}")
        print(f"视频数: {limx_up.videos_count}")
        print(f"总播放量: {limx_up.views_count:,}")
        print(f"最后更新: {limx_up.last_fetch_at.strftime('%Y-%m-%d %H:%M:%S') if limx_up.last_fetch_at else '从未更新'}")
        if limx_up.fetch_error:
            print(f"错误信息: {limx_up.fetch_error}")
        
        # 检查视频
        limx_videos = session.query(BilibiliVideo).filter_by(
            uid=limx_uid,
            is_deleted=False
        ).order_by(BilibiliVideo.pubdate_raw.desc()).limit(5).all()
        
        print(f"\n最新5个视频:")
        for i, video in enumerate(limx_videos, 1):
            print(f"   {i}. {video.bvid}: {video.title[:50]}...")
            print(f"      发布时间: {video.pubdate.strftime('%Y-%m-%d %H:%M:%S') if video.pubdate else 'N/A'}")
            print(f"      播放量: {video.play:,}")
            print(f"      更新时间: {video.updated_at.strftime('%Y-%m-%d %H:%M:%S') if video.updated_at else 'N/A'}")
    else:
        print("❌ 未找到逐际动力UP主")
    
    session.close()
    
except Exception as e:
    print(f"❌ 数据库检查失败: {e}")
    import traceback
    traceback.print_exc()
PYEOF

# ==================== 4. API端点测试 ====================
echo ""
echo "【4. API端点测试】"
echo "============================================================"
echo ""

echo "4.1 测试前端API (/api/bilibili/all)"
echo "----------------------------------------"
HTTP_CODE=$(curl -s -o /tmp/bilibili_api_response.json -w "%{http_code}" http://localhost:5001/api/bilibili/all?force=1)
echo "HTTP状态码: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ API响应正常"
    python3 << 'PYEOF'
import json
try:
    with open('/tmp/bilibili_api_response.json', 'r') as f:
        data = json.load(f)
    
    if data.get('success'):
        up_count = len(data.get('data', []))
        print(f"   返回UP主数量: {up_count}")
        
        if up_count > 0:
            first_up = data['data'][0]
            video_count = len(first_up.get('videos', []))
            print(f"   第一个UP主: {first_up.get('user_info', {}).get('name', 'N/A')}")
            print(f"   视频数量: {video_count}")
            print(f"   更新时间: {first_up.get('updated_at', 'N/A')}")
            
            if video_count > 0:
                latest_video = first_up['videos'][0]
                print(f"   最新视频: {latest_video.get('title', 'N/A')[:50]}...")
                print(f"   发布时间: {latest_video.get('pubdate', 'N/A')}")
        else:
            print("   ⚠️  返回数据为空")
    else:
        print(f"   ❌ API返回失败: {data.get('error', '未知错误')}")
except Exception as e:
    print(f"   ❌ 解析响应失败: {e}")
PYEOF
else
    echo "❌ API响应异常"
    if [ -f /tmp/bilibili_api_response.json ]; then
        echo "响应内容:"
        head -20 /tmp/bilibili_api_response.json
    fi
fi

echo ""
echo "4.2 测试管理后台API (需要认证)"
echo "----------------------------------------"
# 这里无法测试，因为需要token
echo "⚠️  需要认证token，无法直接测试"

# ==================== 5. 定时任务检查 ====================
echo ""
echo "【5. 定时任务检查】"
echo "============================================================"
echo ""

echo "5.1 检查定时任务配置"
echo "----------------------------------------"
if [ -f .env ]; then
    AUTO_FETCH_ENABLED=$(grep "AUTO_FETCH_ENABLED" .env | cut -d '=' -f2)
    BILIBILI_SCHEDULE=$(grep "AUTO_FETCH_BILIBILI_SCHEDULE" .env | cut -d '=' -f2)
    echo "AUTO_FETCH_ENABLED: ${AUTO_FETCH_ENABLED:-未设置}"
    echo "AUTO_FETCH_BILIBILI_SCHEDULE: ${BILIBILI_SCHEDULE:-未设置（默认每6小时）}"
else
    echo "⚠️  .env文件不存在"
fi

echo ""
echo "5.2 检查定时任务进程"
echo "----------------------------------------"
ps aux | grep -E "fetch_bilibili|scheduler|apscheduler" | grep -v grep || echo "   未发现定时任务相关进程"

echo ""
echo "5.3 检查最近的定时任务执行记录"
echo "----------------------------------------"
if [ -f "app.log" ]; then
    echo "最近的定时任务日志:"
    grep -i "定时.*bilibili\|scheduled.*bilibili\|fetch.*bilibili" app.log | tail -10 || echo "   未发现相关日志"
else
    echo "⚠️  app.log文件不存在"
fi

# ==================== 6. 缓存检查 ====================
echo ""
echo "【6. 缓存检查】"
echo "============================================================"
echo ""

python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    from app import bilibili_cache, bilibili_cache_lock
    from datetime import datetime
    
    print("6.1 检查内存缓存状态")
    print("----------------------------------------")
    with bilibili_cache_lock:
        data_cache = bilibili_cache.get('data')
        all_data_cache = bilibili_cache.get('all_data')
        expires_at = bilibili_cache.get('expires_at')
        all_expires_at = bilibili_cache.get('all_expires_at')
        
        if data_cache:
            print(f"✅ /api/bilibili 缓存存在")
            if expires_at:
                age_seconds = datetime.now().timestamp() - expires_at
                if age_seconds < 0:
                    print(f"   缓存剩余时间: {abs(age_seconds):.0f} 秒")
                else:
                    print(f"   ⚠️  缓存已过期 {age_seconds:.0f} 秒")
        else:
            print("⚠️  /api/bilibili 缓存不存在")
        
        if all_data_cache:
            print(f"✅ /api/bilibili/all 缓存存在")
            if all_expires_at:
                age_seconds = datetime.now().timestamp() - all_expires_at
                if age_seconds < 0:
                    print(f"   缓存剩余时间: {abs(age_seconds):.0f} 秒")
                else:
                    print(f"   ⚠️  缓存已过期 {age_seconds:.0f} 秒")
        else:
            print("⚠️  /api/bilibili/all 缓存不存在")
            
except Exception as e:
    print(f"⚠️  无法检查缓存: {e}")
PYEOF

# ==================== 7. 数据更新脚本检查 ====================
echo ""
echo "【7. 数据更新脚本检查】"
echo "============================================================"
echo ""

echo "7.1 检查数据抓取脚本"
echo "----------------------------------------"
if [ -f "fetch_bilibili_data.py" ]; then
    echo "✅ fetch_bilibili_data.py 存在"
    # 检查脚本语法
    python3 -m py_compile fetch_bilibili_data.py 2>&1 && echo "   语法正确" || echo "   ⚠️  有语法错误"
else
    echo "❌ fetch_bilibili_data.py 不存在"
fi

echo ""
echo "7.2 检查最近的手动抓取记录"
echo "----------------------------------------"
if [ -f "app.log" ]; then
    echo "最近的手动抓取日志:"
    grep -i "抓取.*bilibili\|fetch.*bilibili" app.log | tail -10 || echo "   未发现相关日志"
fi

# ==================== 8. 总结和建议 ====================
echo ""
echo "============================================================"
echo "【8. 诊断总结和建议】"
echo "============================================================"
echo ""

python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    from bilibili_models import get_bilibili_session, BilibiliUp
    from datetime import datetime
    
    session = get_bilibili_session()
    
    # 检查数据新鲜度
    ups = session.query(BilibiliUp).filter_by(is_active=True).all()
    now = datetime.now()
    stale_count = 0
    
    for up in ups:
        if up.last_fetch_at:
            age_hours = (now - up.last_fetch_at).total_seconds() / 3600
            if age_hours > 24:
                stale_count += 1
        else:
            stale_count += 1
    
    print("问题诊断:")
    print("----------------------------------------")
    
    if stale_count > 0:
        print(f"❌ 数据过时问题: {stale_count} 个UP主数据超过24小时未更新")
        print("   建议: 手动执行数据抓取脚本更新数据")
        print("   命令: python3 fetch_bilibili_data.py --video-count 50")
    else:
        print("✅ 数据新鲜度正常")
    
    # 检查服务状态
    import subprocess
    result = subprocess.run(['systemctl', 'is-active', 'embodiedpulse'], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ 服务未运行")
        print("   建议: 启动服务 systemctl start embodiedpulse")
    else:
        print("✅ 服务运行正常")
    
    # 检查代码
    import os
    if os.path.exists('bilibili_models.py'):
        with open('bilibili_models.py', 'r') as f:
            content = f.read()
            if 'try:' in content and 'except ImportError:' in content:
                print("✅ 代码包含format_number修复")
            else:
                print("❌ 代码缺少format_number修复")
                print("   建议: 从git拉取最新代码或手动修复")
    
    session.close()
    
except Exception as e:
    print(f"总结生成失败: {e}")
PYEOF

echo ""
echo "============================================================"
echo "诊断完成"
echo "============================================================"

