#!/usr/bin/env python3
"""
Bilibili数据完整性检查脚本
检查数据库中UP主的统计数据是否完整，以及是否有指定日期的数据
"""
import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 尝试导入依赖，如果失败则给出友好提示
try:
    from sqlalchemy import func
    from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
except ImportError as e:
    print("❌ 导入依赖失败，请确保已安装所需依赖")
    print(f"   错误: {e}")
    print("\n建议:")
    print("   1. 使用虚拟环境运行: venv/bin/python3 scripts/check_bilibili_data_integrity.py")
    print("   2. 或安装依赖: pip install psycopg2-binary sqlalchemy")
    sys.exit(1)

def check_up_stats():
    """检查UP主的统计数据"""
    print("=" * 60)
    print("1. 检查UP主统计数据")
    print("=" * 60)
    
    try:
        session = get_bilibili_session()
    except Exception as e:
        print(f"❌ 无法连接数据库: {e}")
        print("\n可能的原因:")
        print("   1. 数据库连接配置错误")
        print("   2. 缺少数据库驱动 (psycopg2 或 sqlite3)")
        print("   3. 数据库服务未启动")
        print("\n建议:")
        print("   1. 使用虚拟环境运行: venv/bin/python3 scripts/check_bilibili_data_integrity.py")
        print("   2. 或安装依赖: pip install psycopg2-binary sqlalchemy")
        return
    
    try:
        ups = session.query(BilibiliUp).filter_by(is_active=True).all()
        
        if not ups:
            print("❌ 数据库中没有活跃的UP主")
            return
        
        print(f"\n找到 {len(ups)} 个活跃UP主\n")
        
        issues = []
        for up in ups:
            has_issue = False
            issue_msgs = []
            
            # 检查视频数
            if up.videos_count is None or up.videos_count == 0:
                has_issue = True
                issue_msgs.append("视频数为0或NULL")
            
            # 检查总播放数
            if up.views_count is None or up.views_count == 0:
                has_issue = True
                issue_msgs.append("总播放数为0或NULL")
            
            # 检查最后抓取时间
            if not up.last_fetch_at:
                has_issue = True
                issue_msgs.append("未记录最后抓取时间")
            else:
                # 检查是否超过24小时未更新
                hours_since_update = (datetime.now() - up.last_fetch_at).total_seconds() / 3600
                if hours_since_update > 24:
                    has_issue = True
                    issue_msgs.append(f"超过{int(hours_since_update)}小时未更新")
            
            # 检查错误信息
            if up.fetch_error:
                has_issue = True
                issue_msgs.append(f"有错误信息: {up.fetch_error[:50]}")
            
            status = "✅" if not has_issue else "❌"
            print(f"{status} {up.name} (UID: {up.uid})")
            print(f"   视频数: {up.videos_count or 0}")
            print(f"   总播放数: {up.views_count or 0} ({up.views_formatted or 'N/A'})")
            print(f"   最后更新: {up.last_fetch_at.strftime('%Y-%m-%d %H:%M:%S') if up.last_fetch_at else 'N/A'}")
            
            if has_issue:
                print(f"   问题: {', '.join(issue_msgs)}")
                issues.append({
                    'up': up,
                    'issues': issue_msgs
                })
            print()
        
        if issues:
            print(f"\n⚠️  发现 {len(issues)} 个UP主有数据问题：")
            for item in issues:
                print(f"   - {item['up'].name}: {', '.join(item['issues'])}")
        else:
            print("\n✅ 所有UP主的统计数据正常")
        
    finally:
        session.close()

def check_date_data(target_date=None):
    """检查指定日期的数据"""
    print("=" * 60)
    print("2. 检查指定日期的数据")
    print("=" * 60)
    
    if target_date is None:
        # 默认检查今天和昨天
        target_date = datetime.now().date()
        yesterday = target_date - timedelta(days=1)
        dates_to_check = [yesterday, target_date]
    else:
        dates_to_check = [target_date]
    
    try:
        session = get_bilibili_session()
    except Exception as e:
        print(f"❌ 无法连接数据库: {e}")
        return
    
    try:
        for date_to_check in dates_to_check:
            print(f"\n检查日期: {date_to_check}")
            
            # 统计该日期的视频数
            video_count = session.query(func.count(BilibiliVideo.bvid)).filter(
                func.date(BilibiliVideo.pubdate) == date_to_check
            ).scalar()
            
            # 获取该日期的视频列表
            videos = session.query(BilibiliVideo).filter(
                func.date(BilibiliVideo.pubdate) == date_to_check
            ).limit(10).all()
            
            print(f"   视频数量: {video_count}")
            
            if video_count > 0:
                print(f"   前10个视频:")
                for video in videos:
                    print(f"     - {video.title[:50]} (播放量: {video.play_formatted or video.play})")
            else:
                print(f"   ⚠️  该日期没有视频数据")
            
            # 检查该日期是否有UP主更新了数据
            ups_updated = session.query(BilibiliUp).filter(
                func.date(BilibiliUp.last_fetch_at) == date_to_check
            ).count()
            
            print(f"   该日期更新的UP主数: {ups_updated}")
        
    finally:
        session.close()

def check_recent_fetch_status():
    """检查最近的数据抓取状态"""
    print("=" * 60)
    print("3. 检查最近的数据抓取状态")
    print("=" * 60)
    
    try:
        session = get_bilibili_session()
    except Exception as e:
        print(f"❌ 无法连接数据库: {e}")
        return
    
    try:
        # 获取最近更新的UP主
        recent_ups = session.query(BilibiliUp).filter_by(is_active=True).order_by(
            BilibiliUp.last_fetch_at.desc()
        ).limit(5).all()
        
        if not recent_ups:
            print("❌ 没有找到最近更新的UP主")
            return
        
        print("\n最近更新的5个UP主:")
        for up in recent_ups:
            hours_ago = (datetime.now() - up.last_fetch_at).total_seconds() / 3600 if up.last_fetch_at else None
            status = "✅" if not up.fetch_error else "❌"
            print(f"{status} {up.name}")
            print(f"   最后更新: {up.last_fetch_at.strftime('%Y-%m-%d %H:%M:%S') if up.last_fetch_at else 'N/A'}")
            if hours_ago:
                print(f"   更新于: {int(hours_ago)}小时前")
            if up.fetch_error:
                print(f"   错误: {up.fetch_error[:100]}")
            print()
        
        # 统计总体情况
        total_ups = session.query(func.count(BilibiliUp.uid)).filter_by(is_active=True).scalar()
        ups_with_error = session.query(func.count(BilibiliUp.uid)).filter_by(
            is_active=True
        ).filter(BilibiliUp.fetch_error.isnot(None)).scalar()
        
        print(f"\n总体统计:")
        print(f"   活跃UP主总数: {total_ups}")
        print(f"   有错误的UP主数: {ups_with_error}")
        print(f"   正常UP主数: {total_ups - ups_with_error}")
        
    finally:
        session.close()

def check_database_stats():
    """检查数据库总体统计"""
    print("=" * 60)
    print("4. 检查数据库总体统计")
    print("=" * 60)
    
    try:
        session = get_bilibili_session()
    except Exception as e:
        print(f"❌ 无法连接数据库: {e}")
        return
    
    try:
        # 总UP主数
        total_ups = session.query(func.count(BilibiliUp.uid)).scalar()
        active_ups = session.query(func.count(BilibiliUp.uid)).filter_by(is_active=True).scalar()
        
        # 总视频数
        total_videos = session.query(func.count(BilibiliVideo.bvid)).scalar()
        
        # 总播放量
        total_plays = session.query(func.sum(BilibiliVideo.play)).scalar() or 0
        
        # 最近7天的视频数
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_videos = session.query(func.count(BilibiliVideo.bvid)).filter(
            BilibiliVideo.pubdate >= seven_days_ago
        ).scalar()
        
        print(f"\n数据库统计:")
        print(f"   总UP主数: {total_ups} (活跃: {active_ups})")
        print(f"   总视频数: {total_videos}")
        print(f"   总播放量: {total_plays:,}")
        print(f"   最近7天视频数: {recent_videos}")
        
        # 检查统计数据完整性
        ups_with_stats = session.query(func.count(BilibiliUp.uid)).filter_by(
            is_active=True
        ).filter(
            BilibiliUp.videos_count > 0,
            BilibiliUp.views_count > 0
        ).scalar()
        
        print(f"\n统计数据完整性:")
        print(f"   有完整统计数据的UP主数: {ups_with_stats}/{active_ups}")
        
        if ups_with_stats < active_ups:
            print(f"   ⚠️  有 {active_ups - ups_with_stats} 个UP主缺少统计数据")
        
    finally:
        session.close()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='检查Bilibili数据完整性')
    parser.add_argument('--date', type=str, help='检查指定日期 (格式: YYYY-MM-DD)')
    parser.add_argument('--all', action='store_true', help='执行所有检查')
    
    args = parser.parse_args()
    
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            print(f"❌ 日期格式错误，请使用 YYYY-MM-DD 格式")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Bilibili数据完整性检查")
    print("=" * 60)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 执行检查
    check_up_stats()
    print()
    
    check_date_data(target_date)
    print()
    
    check_recent_fetch_status()
    print()
    
    check_database_stats()
    print()
    
    print("=" * 60)
    print("检查完成")
    print("=" * 60)

if __name__ == '__main__':
    main()
