#!/usr/bin/env python3
"""
诊断数据问题：论文和视频数据
"""
import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# 尝试使用虚拟环境中的Python（如果存在）
venv_python = os.path.join(project_root, 'venv', 'bin', 'python3')
if os.path.exists(venv_python):
    # 如果虚拟环境存在，但当前不是使用虚拟环境的Python，给出提示
    if sys.executable != venv_python:
        print("⚠️  检测到虚拟环境，但当前使用的是系统Python")
        print(f"   当前Python: {sys.executable}")
        print(f"   虚拟环境Python: {venv_python}")
        print("   建议使用虚拟环境运行: source venv/bin/activate && python3 scripts/diagnose_data_issues.py")
        print("   或者直接使用: venv/bin/python3 scripts/diagnose_data_issues.py")
        print()

from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("数据问题诊断")
print("=" * 60)
print()

# 1. 检查论文数据
print("=" * 60)
print("1. 具身论文数据检查")
print("=" * 60)
print()

try:
    # 检查数据库类型
    import os
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./papers.db')
    
    # 如果是PostgreSQL，检查psycopg2是否安装
    if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
        try:
            import psycopg2
        except ImportError:
            print("❌ 缺少 psycopg2 模块（PostgreSQL驱动）")
            print("   请运行: bash scripts/install_psycopg2.sh")
            print("   或者: pip install psycopg2-binary")
            raise
    
    from models import get_session, Paper
    
    session = get_session()
    
    # 总论文数
    total_papers = session.query(Paper).count()
    print(f"📊 总论文数: {total_papers} 篇")
    
    # 检查12月17日的论文
    target_date = datetime(2025, 12, 17).date()
    papers_1217 = session.query(Paper).filter(Paper.publish_date == target_date).count()
    print(f"📅 2025-12-17 论文数: {papers_1217} 篇")
    
    # 检查最近7天的论文
    seven_days_ago = datetime.now().date() - timedelta(days=7)
    recent_papers = session.query(Paper).filter(Paper.publish_date >= seven_days_ago).count()
    print(f"📅 最近7天论文数: {recent_papers} 篇")
    
    # 检查最新论文的日期
    latest_paper = session.query(Paper).order_by(Paper.publish_date.desc()).first()
    if latest_paper:
        print(f"📅 最新论文日期: {latest_paper.publish_date}")
        print(f"   标题: {latest_paper.title[:50]}...")
    else:
        print("⚠️  没有找到论文数据")
    
    # 检查今天创建的论文（可能是今天抓取的）
    today = datetime.now().date()
    today_created = session.query(Paper).filter(
        Paper.created_at >= datetime.combine(today, datetime.min.time())
    ).count()
    print(f"📅 今天创建的论文数: {today_created} 篇")
    
    # 检查12月17日创建的论文（可能是今天抓取的12月17日的论文）
    dec17_created = session.query(Paper).filter(
        Paper.created_at >= datetime(2025, 12, 17, 0, 0, 0),
        Paper.created_at < datetime(2025, 12, 18, 0, 0, 0)
    ).count()
    print(f"📅 12月17日创建的论文数: {dec17_created} 篇")
    
    # 检查12月17日的论文详情
    if papers_1217 > 0:
        print(f"\n📋 12月17日的论文列表（前5篇）:")
        papers_list = session.query(Paper).filter(
            Paper.publish_date == target_date
        ).order_by(Paper.created_at.desc()).limit(5).all()
        for i, paper in enumerate(papers_list, 1):
            print(f"   {i}. {paper.title[:60]}...")
            print(f"      创建时间: {paper.created_at}")
            print(f"      发布日期: {paper.publish_date}")
    else:
        print("\n⚠️  没有找到12月17日的论文")
        # 检查是否有相近日期的论文
        nearby_papers = session.query(Paper).filter(
            Paper.publish_date >= target_date - timedelta(days=3),
            Paper.publish_date <= target_date + timedelta(days=3)
        ).order_by(Paper.publish_date.desc()).limit(5).all()
        if nearby_papers:
            print("\n📋 相近日期的论文:")
            for paper in nearby_papers:
                print(f"   - {paper.publish_date}: {paper.title[:50]}...")
    
    session.close()
    
except Exception as e:
    print(f"❌ 检查论文数据失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("2. 具身视频数据检查")
print("=" * 60)
print()

try:
    # 检查数据库类型
    import os
    bilibili_db_url = os.getenv('BILIBILI_DATABASE_URL', os.getenv('DATABASE_URL', 'sqlite:///./bilibili.db'))
    
    # 如果是PostgreSQL，检查psycopg2是否安装
    if bilibili_db_url.startswith('postgresql://') or bilibili_db_url.startswith('postgres://'):
        try:
            import psycopg2
        except ImportError:
            print("❌ 缺少 psycopg2 模块（PostgreSQL驱动）")
            print("   请运行: bash scripts/install_psycopg2.sh")
            print("   或者: pip install psycopg2-binary")
            raise
    
    from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
    
    bilibili_session = get_bilibili_session()
    
    # UP主数量
    total_ups = bilibili_session.query(BilibiliUp).count()
    active_ups = bilibili_session.query(BilibiliUp).filter_by(is_active=True).count()
    print(f"📊 总UP主数: {total_ups} 个")
    print(f"📊 活跃UP主数: {active_ups} 个")
    
    # 视频数量
    total_videos = bilibili_session.query(BilibiliVideo).count()
    active_videos = bilibili_session.query(BilibiliVideo).filter_by(is_deleted=False).count()
    print(f"📊 总视频数: {total_videos} 个")
    print(f"📊 未删除视频数: {active_videos} 个")
    
    # 检查最近30天的视频
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_videos = bilibili_session.query(BilibiliVideo).filter(
        BilibiliVideo.pubdate >= thirty_days_ago,
        BilibiliVideo.is_deleted == False
    ).count()
    print(f"📅 最近30天视频数: {recent_videos} 个")
    
    # 检查每个UP主的视频数
    print(f"\n📋 各UP主的视频数量:")
    ups = bilibili_session.query(BilibiliUp).filter_by(is_active=True).all()
    for up in ups:
        video_count = bilibili_session.query(BilibiliVideo).filter(
            BilibiliVideo.uid == up.uid,
            BilibiliVideo.is_deleted == False
        ).count()
        print(f"   {up.name}: {video_count} 个视频")
    
    # 检查最新视频
    latest_video = bilibili_session.query(BilibiliVideo).filter_by(
        is_deleted=False
    ).order_by(BilibiliVideo.pubdate.desc()).first()
    if latest_video:
        print(f"\n📅 最新视频:")
        print(f"   标题: {latest_video.title[:50]}...")
        print(f"   发布时间: {latest_video.pubdate}")
        print(f"   UP主: {latest_video.uid}")
    else:
        print("\n⚠️  没有找到视频数据")
    
    # 检查数据更新时间
    print(f"\n📅 数据更新时间:")
    for up in ups[:5]:  # 只显示前5个
        print(f"   {up.name}: {up.updated_at}")
    
    bilibili_session.close()
    
except Exception as e:
    print(f"❌ 检查视频数据失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("3. 数据获取配置检查")
print("=" * 60)
print()

# 检查定时任务配置
auto_fetch_enabled = os.getenv('AUTO_FETCH_ENABLED', 'false').lower() == 'true'
print(f"📅 自动抓取启用: {'✅ 是' if auto_fetch_enabled else '❌ 否'}")

if auto_fetch_enabled:
    fetch_schedule = os.getenv('AUTO_FETCH_SCHEDULE', '未设置')
    print(f"📅 论文抓取计划: {fetch_schedule}")
    
    bilibili_schedule = os.getenv('AUTO_FETCH_BILIBILI_SCHEDULE', '未设置')
    print(f"📅 B站抓取计划: {bilibili_schedule}")

print()
print("=" * 60)
print("诊断完成")
print("=" * 60)

