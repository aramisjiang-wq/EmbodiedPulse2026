#!/usr/bin/env python3
"""
检查Bilibili数据完整性
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Bilibili数据完整性检查")
print("=" * 60)
print()

try:
    from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
    from bilibili_client import BilibiliClient
    
    bilibili_session = get_bilibili_session()
    
    # 1. 检查UP主数据
    print("=" * 60)
    print("1. UP主数据检查")
    print("=" * 60)
    print()
    
    total_ups = bilibili_session.query(BilibiliUp).count()
    active_ups = bilibili_session.query(BilibiliUp).filter_by(is_active=True).all()
    
    print(f"📊 总UP主数: {total_ups} 个")
    print(f"📊 活跃UP主数: {len(active_ups)} 个")
    print()
    
    # 检查每个UP主的详细信息
    print("📋 UP主详细信息:")
    for up in active_ups:
        video_count = bilibili_session.query(BilibiliVideo).filter(
            BilibiliVideo.uid == up.uid,
            BilibiliVideo.is_deleted == False
        ).count()
        
        latest_video = bilibili_session.query(BilibiliVideo).filter(
            BilibiliVideo.uid == up.uid,
            BilibiliVideo.is_deleted == False
        ).order_by(BilibiliVideo.pubdate.desc()).first()
        
        print(f"   {up.name} (UID: {up.uid})")
        print(f"      视频数: {video_count} 个")
        print(f"      粉丝数: {up.fans or 'N/A'}")
        print(f"      最后更新: {up.updated_at}")
        if latest_video:
            print(f"      最新视频: {latest_video.title[:50]}...")
            print(f"      发布时间: {latest_video.pubdate}")
        else:
            print(f"      ⚠️  没有视频数据")
        print()
    
    # 2. 检查视频数据
    print("=" * 60)
    print("2. 视频数据检查")
    print("=" * 60)
    print()
    
    total_videos = bilibili_session.query(BilibiliVideo).count()
    active_videos = bilibili_session.query(BilibiliVideo).filter_by(is_deleted=False).count()
    deleted_videos = bilibili_session.query(BilibiliVideo).filter_by(is_deleted=True).count()
    
    print(f"📊 总视频数: {total_videos} 个")
    print(f"📊 未删除视频数: {active_videos} 个")
    print(f"📊 已删除视频数: {deleted_videos} 个")
    print()
    
    # 检查最近30天的视频
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_videos = bilibili_session.query(BilibiliVideo).filter(
        BilibiliVideo.pubdate >= thirty_days_ago,
        BilibiliVideo.is_deleted == False
    ).count()
    print(f"📅 最近30天视频数: {recent_videos} 个")
    
    # 检查每个UP主的视频数量分布
    print()
    print("📋 各UP主视频数量分布:")
    for up in active_ups:
        video_count = bilibili_session.query(BilibiliVideo).filter(
            BilibiliVideo.uid == up.uid,
            BilibiliVideo.is_deleted == False
        ).count()
        print(f"   {up.name}: {video_count} 个")
    
    # 3. 对比API数据（可选，需要网络）
    print()
    print("=" * 60)
    print("3. 与API数据对比（需要网络）")
    print("=" * 60)
    print()
    
    try:
        client = BilibiliClient()
        
        for up in active_ups[:3]:  # 只检查前3个UP主
            print(f"📡 检查 {up.name} (UID: {up.uid})...")
            try:
                api_data = client.get_all_data(up.uid, video_count=10)
                if api_data and 'videos' in api_data:
                    api_video_count = len(api_data['videos'])
                    db_video_count = bilibili_session.query(BilibiliVideo).filter(
                        BilibiliVideo.uid == up.uid,
                        BilibiliVideo.is_deleted == False
                    ).count()
                    
                    print(f"   API返回视频数: {api_video_count} 个")
                    print(f"   数据库视频数: {db_video_count} 个")
                    
                    if api_video_count > db_video_count:
                        print(f"   ⚠️  数据库视频数少于API，可能丢失了 {api_video_count - db_video_count} 个视频")
                    else:
                        print(f"   ✅ 数据一致")
            except Exception as e:
                print(f"   ❌ API请求失败: {e}")
            print()
    except Exception as e:
        print(f"⚠️  无法连接API进行对比: {e}")
    
    # 4. 检查数据更新时间
    print("=" * 60)
    print("4. 数据更新时间检查")
    print("=" * 60)
    print()
    
    for up in active_ups:
        print(f"   {up.name}: {up.updated_at}")
    
    bilibili_session.close()
    
    print()
    print("=" * 60)
    print("✅ 检查完成")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()

