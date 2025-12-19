#!/usr/bin/env python3
"""
诊断具身视频页面的所有问题
1. 检查统计数据是否正确
2. 检查12月18日的视频
3. 检查API返回的数据格式
"""
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import func

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
    from bilibili_client import format_number
except ImportError as e:
    print("❌ 导入依赖失败，请确保已安装所需依赖")
    print(f"   错误: {e}")
    sys.exit(1)

def check_stats_data():
    """检查统计数据"""
    print("=" * 60)
    print("1. 检查UP主统计数据")
    print("=" * 60)
    
    session = get_bilibili_session()
    try:
        ups = session.query(BilibiliUp).filter_by(is_active=True).all()
        
        print(f"\n检查 {len(ups)} 个UP主的统计数据:\n")
        
        issues = []
        for up in ups:
            # 从视频表实际统计
            actual_video_count = session.query(func.count(BilibiliVideo.bvid)).filter_by(
                uid=up.uid,
                is_deleted=False
            ).scalar()
            
            actual_total_views = session.query(func.sum(BilibiliVideo.play)).filter_by(
                uid=up.uid,
                is_deleted=False
            ).scalar() or 0
            
            db_videos_count = up.videos_count or 0
            db_views_count = up.views_count or 0
            
            has_issue = False
            issue_msgs = []
            
            if db_videos_count == 0:
                has_issue = True
                issue_msgs.append(f"videos_count为0（实际应有{actual_video_count}个）")
            
            if db_views_count == 0:
                has_issue = True
                issue_msgs.append(f"views_count为0（实际应有{actual_total_views:,}）")
            
            status = "❌" if has_issue else "✅"
            print(f"{status} {up.name}")
            print(f"   数据库: videos_count={db_videos_count}, views_count={db_views_count:,}")
            print(f"   实际值: videos={actual_video_count}, views={actual_total_views:,}")
            
            if has_issue:
                print(f"   ⚠️  问题: {', '.join(issue_msgs)}")
                issues.append({
                    'up': up,
                    'db_videos_count': db_videos_count,
                    'db_views_count': db_views_count,
                    'actual_video_count': actual_video_count,
                    'actual_total_views': actual_total_views
                })
            print()
        
        if issues:
            print(f"\n⚠️  发现 {len(issues)} 个UP主有统计数据问题")
            return False
        else:
            print("\n✅ 所有UP主的统计数据都正常")
            return True
            
    finally:
        session.close()

def check_dec18_videos():
    """检查12月18日的视频"""
    print("=" * 60)
    print("2. 检查12月18日的视频")
    print("=" * 60)
    
    session = get_bilibili_session()
    try:
        date_1218 = datetime(2025, 12, 18).date()
        
        # 统计12月18日的视频数
        count = session.query(func.count(BilibiliVideo.bvid)).filter(
            func.date(BilibiliVideo.pubdate) == date_1218
        ).scalar()
        
        print(f"\n12月18日的视频数: {count}")
        
        if count > 0:
            videos = session.query(BilibiliVideo).filter(
                func.date(BilibiliVideo.pubdate) == date_1218
            ).order_by(BilibiliVideo.pubdate_raw.desc()).limit(10).all()
            
            print(f"\n前10个视频:")
            for i, v in enumerate(videos, 1):
                up = session.query(BilibiliUp).filter_by(uid=v.uid).first()
                up_name = up.name if up else f"UID:{v.uid}"
                print(f"   {i}. [{up_name}] {v.title[:60]}")
                print(f"      发布时间: {v.pubdate}")
                print(f"      播放量: {v.play_formatted or v.play}")
            
            return True
        else:
            print("\n⚠️  数据库中没有12月18日的视频")
            
            # 检查最近几天的视频
            print("\n检查最近7天的视频分布:")
            for i in range(7):
                check_date = datetime.now().date() - timedelta(days=i)
                count = session.query(func.count(BilibiliVideo.bvid)).filter(
                    func.date(BilibiliVideo.pubdate) == check_date
                ).scalar()
                print(f"   {check_date}: {count} 个视频")
            
            return False
            
    finally:
        session.close()

def check_api_response_format():
    """检查API返回的数据格式"""
    print("=" * 60)
    print("3. 检查API返回的数据格式")
    print("=" * 60)
    
    session = get_bilibili_session()
    try:
        # 模拟API返回的数据结构
        up = session.query(BilibiliUp).filter_by(is_active=True).first()
        
        if not up:
            print("❌ 没有找到UP主数据")
            return False
        
        # 模拟API返回格式
        user_stat = {
            'videos': format_number(up.videos_count) if up.videos_count else '0',
            'likes': up.likes_formatted or '0',
            'views': up.views_formatted or '0',
        }
        
        print(f"\nUP主: {up.name}")
        print(f"API返回的user_stat:")
        print(f"  videos: {user_stat['videos']}")
        print(f"  views: {user_stat['views']}")
        print(f"  likes: {user_stat['likes']}")
        
        # 检查字段是否为空
        if user_stat['videos'] == '0' and up.videos_count == 0:
            print(f"\n⚠️  videos字段为0，但数据库中videos_count={up.videos_count}")
        
        if user_stat['views'] == '0' and up.views_count == 0:
            print(f"\n⚠️  views字段为0，但数据库中views_count={up.views_count}")
        
        return True
        
    finally:
        session.close()

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("具身视频页面问题诊断")
    print("=" * 60)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 检查统计数据
    stats_ok = check_stats_data()
    print()
    
    # 2. 检查12月18日的视频
    videos_ok = check_dec18_videos()
    print()
    
    # 3. 检查API返回格式
    api_ok = check_api_response_format()
    print()
    
    # 总结
    print("=" * 60)
    print("诊断总结")
    print("=" * 60)
    print(f"统计数据: {'✅ 正常' if stats_ok else '❌ 有问题'}")
    print(f"12月18日视频: {'✅ 存在' if videos_ok else '❌ 不存在'}")
    print(f"API格式: {'✅ 正常' if api_ok else '❌ 有问题'}")
    print()
    
    if not stats_ok:
        print("建议: 运行 scripts/fix_bilibili_stats.py 修复统计数据")
    
    if not videos_ok:
        print("建议: 运行 python3 fetch_bilibili_data.py --video-count 50 抓取最新数据")
    
    print("=" * 60)

if __name__ == '__main__':
    main()

