#!/bin/bash
# 生成完整的B站数据问题诊断报告

cd /srv/EmbodiedPulse2026 || exit 1

REPORT_FILE="/tmp/bilibili_full_report_$(date +%Y%m%d_%H%M%S).txt"

{
echo "============================================================"
echo "B站数据问题完整诊断报告"
echo "生成时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"
echo ""

# ==================== 1. 服务状态 ====================
echo "【1. 服务状态】"
echo "============================================================"
systemctl status embodiedpulse --no-pager -l | head -20
echo ""

# ==================== 2. 数据新鲜度 ====================
echo "【2. 数据新鲜度检查】"
echo "============================================================"
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')
from bilibili_models import get_bilibili_session, BilibiliUp
from datetime import datetime

session = get_bilibili_session()
ups = session.query(BilibiliUp).filter_by(is_active=True).all()
now = datetime.now()

for up in ups:
    if up.last_fetch_at:
        age_hours = (now - up.last_fetch_at).total_seconds() / 3600
        print(f"{up.name}: {age_hours:.1f} 小时前更新 ({up.last_fetch_at.strftime('%Y-%m-%d %H:%M:%S')})")
    else:
        print(f"{up.name}: 从未更新")

session.close()
PYEOF

# ==================== 3. 视频播放量检查 ====================
echo ""
echo "【3. 视频播放量检查（重点）】"
echo "============================================================"
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')
from bilibili_models import get_bilibili_session, BilibiliVideo
from datetime import datetime, timedelta

session = get_bilibili_session()

# 检查逐际动力的最新视频
limx_uid = 1172054289
videos = session.query(BilibiliVideo).filter_by(
    uid=limx_uid,
    is_deleted=False
).order_by(BilibiliVideo.pubdate_raw.desc()).limit(5).all()

print("逐际动力最新5个视频:")
for i, video in enumerate(videos, 1):
    video_age_days = (datetime.now() - video.pubdate).total_seconds() / 86400 if video.pubdate else 0
    update_age_hours = (datetime.now() - video.updated_at).total_seconds() / 3600 if video.updated_at else 999
    
    print(f"\n{i}. {video.bvid}")
    print(f"   标题: {video.title[:60]}...")
    print(f"   发布时间: {video.pubdate.strftime('%Y-%m-%d %H:%M:%S') if video.pubdate else 'N/A'}")
    print(f"   视频发布距今: {video_age_days:.1f} 天")
    print(f"   播放量: {video.play:,} (格式化: {video.play_formatted})")
    print(f"   播放量更新时间: {video.updated_at.strftime('%Y-%m-%d %H:%M:%S') if video.updated_at else '从未更新'}")
    print(f"   播放量更新距今: {update_age_hours:.1f} 小时")
    
    # 判断播放量是否可能过时
    if video.pubdate:
        if video_age_days > 1 and video.play < 5000:
            print(f"   ⚠️  视频发布{video_age_days:.1f}天，播放量可能过时")
        if update_age_hours > 24:
            print(f"   ⚠️  播放量已{update_age_hours:.1f}小时未更新")

session.close()
PYEOF

# ==================== 4. API返回数据检查 ====================
echo ""
echo "【4. API返回数据检查】"
echo "============================================================"
curl -s "http://localhost:5001/api/bilibili/all?force=1" | python3 << 'PYEOF'
import sys, json
data = json.load(sys.stdin)

if data.get('success') and data.get('data'):
    print(f"✅ API返回成功")
    print(f"UP主数量: {len(data['data'])}")
    
    # 检查逐际动力的数据
    limx_data = None
    for up_data in data['data']:
        if up_data.get('user_info', {}).get('name') == '逐际动力':
            limx_data = up_data
            break
    
    if limx_data:
        print(f"\n逐际动力数据:")
        print(f"  视频数量: {len(limx_data.get('videos', []))}")
        print(f"  更新时间: {limx_data.get('updated_at')}")
        
        if limx_data.get('videos'):
            latest = limx_data['videos'][0]
            print(f"\n  最新视频:")
            print(f"    BV号: {latest.get('bvid')}")
            print(f"    标题: {latest.get('title', '')[:60]}...")
            print(f"    播放量: {latest.get('play')}")
            print(f"    发布时间: {latest.get('pubdate')}")
            
            # 检查播放量
            play_raw = latest.get('play_raw', 0)
            if play_raw < 10000:
                print(f"    ⚠️  播放量较低 ({play_raw:,})，可能需要更新")
else:
    print(f"❌ API返回失败: {data.get('error', '未知错误')}")
PYEOF

# ==================== 5. 代码检查 ====================
echo ""
echo "【5. 代码检查】"
echo "============================================================"
python3 -m py_compile bilibili_models.py 2>&1 && echo "✅ bilibili_models.py 语法正确" || {
    echo "❌ bilibili_models.py 有语法错误"
    python3 -m py_compile bilibili_models.py 2>&1 | head -3
}

# ==================== 6. 缓存检查 ====================
echo ""
echo "【6. 缓存检查】"
echo "============================================================"
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    from app import bilibili_cache, bilibili_cache_lock
    from datetime import datetime
    
    with bilibili_cache_lock:
        all_data_cache = bilibili_cache.get('all_data')
        all_expires_at = bilibili_cache.get('all_expires_at')
        
        if all_data_cache:
            print("⚠️  内存缓存存在")
            if all_expires_at:
                age_seconds = datetime.now().timestamp() - all_expires_at
                if age_seconds < 0:
                    print(f"   缓存剩余时间: {abs(age_seconds):.0f} 秒")
                else:
                    print(f"   缓存已过期: {abs(age_seconds):.0f} 秒")
        else:
            print("✅ 内存缓存不存在（已清除）")
except Exception as e:
    print(f"⚠️  无法检查缓存: {e}")
PYEOF

# ==================== 7. 总结 ====================
echo ""
echo "============================================================"
echo "【7. 诊断总结】"
echo "============================================================"
echo ""
echo "根据检查结果："
echo "1. 如果数据新鲜度正常但前端显示旧数据："
echo "   - 可能是视频播放量未更新"
echo "   - 建议: 执行 python3 scripts/update_video_play_counts.py --uids 1172054289 --force"
echo ""
echo "2. 如果API返回的数据与数据库不一致："
echo "   - 检查API缓存"
echo "   - 建议: 重启服务 systemctl restart embodiedpulse"
echo ""
echo "3. 如果前端仍显示旧数据："
echo "   - 清除浏览器缓存"
echo "   - 使用 force=1 参数访问"
echo "   - 检查浏览器控制台的API请求"

} | tee "$REPORT_FILE"

echo ""
echo "报告已保存到: $REPORT_FILE"

