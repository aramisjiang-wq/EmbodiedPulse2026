#!/bin/bash
# 简单的B站诊断脚本 - 直接在服务器上创建和执行
# 使用方法: 复制整个脚本内容，在服务器上执行

cd /srv/EmbodiedPulse2026 || exit 1

if [ -d "venv" ]; then
    source venv/bin/activate
fi

python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

print("=" * 60)
print("B站数据诊断")
print("=" * 60)

try:
    from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
    from sqlalchemy import func
    from datetime import datetime
    
    session = get_bilibili_session()
    
    # 1. 数据库连接
    up_count = session.query(BilibiliUp).count()
    video_count = session.query(BilibiliVideo).count()
    print(f"\n✅ 数据库连接成功")
    print(f"   UP主: {up_count}, 视频: {video_count}")
    
    # 2. 测试管理后台查询
    print("\n测试管理后台视频列表查询:")
    try:
        query = session.query(BilibiliVideo, BilibiliUp).join(
            BilibiliUp, BilibiliVideo.uid == BilibiliUp.uid
        ).order_by(BilibiliVideo.pubdate.desc())
        
        total = query.count()
        print(f"   ✅ 查询成功，总记录数: {total}")
        
        results = query.limit(5).all()
        print(f"   ✅ 成功获取前5条记录")
        
        # 测试to_dict
        for i, (video, up) in enumerate(results, 1):
            try:
                video_dict = video.to_dict()
                video_dict['up_name'] = up.name
                print(f"   {i}. {video.bvid}: {video_dict.get('title', '')[:40]}...")
            except Exception as e:
                print(f"   ❌ to_dict失败 ({video.bvid}): {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"   ❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. 检查数据新鲜度
    print("\n检查数据新鲜度（前5个UP主）:")
    ups = session.query(BilibiliUp).filter_by(is_active=True).limit(5).all()
    now = datetime.now()
    for up in ups:
        if up.last_fetch_at:
            age_hours = (now - up.last_fetch_at).total_seconds() / 3600
            status = "✅" if age_hours < 24 else "⚠️" if age_hours < 168 else "❌"
            print(f"   {status} {up.name}: {age_hours:.1f} 小时前更新")
        else:
            print(f"   ❌ {up.name}: 从未更新")
    
    session.close()
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ 诊断失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF

