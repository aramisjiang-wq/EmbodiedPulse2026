#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查Bilibili数据库数据状态
用于诊断问题，不修改任何数据
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from sqlalchemy import func

def check_data_status():
    """检查数据库数据状态"""
    print("=" * 60)
    print("Bilibili数据库数据状态检查")
    print("=" * 60)
    
    # 加载环境变量
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    
    session = get_bilibili_session()
    
    try:
        # 1. 检查UP主数据
        print("\n【1. UP主数据统计】")
        ups = session.query(BilibiliUp).filter_by(is_active=True).all()
        print(f"活跃UP主数量: {len(ups)}")
        
        for up in ups:
            print(f"\n  UP主: {up.name} (UID: {up.uid})")
            print(f"    数据库中的统计数据:")
            print(f"      videos_count: {up.videos_count}")
            print(f"      views_count: {up.views_count}")
            print(f"      views_formatted: {up.views_formatted}")
            
            # 从视频表实际统计
            video_count = session.query(func.count(BilibiliVideo.bvid)).filter_by(
                uid=up.uid,
                is_deleted=False
            ).scalar()
            
            total_views = session.query(func.sum(BilibiliVideo.play)).filter_by(
                uid=up.uid,
                is_deleted=False
            ).scalar() or 0
            
            print(f"    实际视频表中的数据:")
            print(f"      视频数量: {video_count}")
            print(f"      总播放量: {total_views}")
            
            # 对比
            if up.videos_count != video_count:
                print(f"    ⚠️  视频数量不一致！数据库={up.videos_count}, 实际={video_count}")
            if up.views_count != total_views:
                print(f"    ⚠️  总播放量不一致！数据库={up.views_count}, 实际={total_views}")
        
        # 2. 检查视频数据
        print("\n【2. 视频数据统计】")
        total_videos = session.query(func.count(BilibiliVideo.bvid)).filter_by(
            is_deleted=False
        ).scalar()
        print(f"总视频数量: {total_videos}")
        
        # 检查有播放量的视频
        videos_with_play = session.query(func.count(BilibiliVideo.bvid)).filter(
            BilibiliVideo.is_deleted == False,
            BilibiliVideo.play > 0
        ).scalar()
        print(f"有播放量的视频: {videos_with_play}")
        
        # 检查有pubdate的视频
        videos_with_date = session.query(func.count(BilibiliVideo.bvid)).filter(
            BilibiliVideo.is_deleted == False,
            BilibiliVideo.pubdate.isnot(None)
        ).scalar()
        print(f"有发布日期的视频: {videos_with_date}")
        
        # 检查pubdate为NULL的视频
        videos_no_date = session.query(func.count(BilibiliVideo.bvid)).filter(
            BilibiliVideo.is_deleted == False,
            BilibiliVideo.pubdate.is_(None)
        ).scalar()
        if videos_no_date > 0:
            print(f"⚠️  没有发布日期的视频: {videos_no_date}")
        
        # 3. 检查最近更新的视频
        print("\n【3. 最近更新的视频（前5个）】")
        recent_videos = session.query(BilibiliVideo).filter_by(
            is_deleted=False
        ).order_by(BilibiliVideo.updated_at.desc()).limit(5).all()
        
        for video in recent_videos:
            print(f"  {video.bvid}: {video.title[:30]}")
            print(f"    播放量: {video.play} ({video.play_formatted})")
            print(f"    评论数: {video.video_review}")
            print(f"    收藏数: {video.favorites}")
            print(f"    发布时间: {video.pubdate}")
            print(f"    更新时间: {video.updated_at}")
        
        # 4. 检查数据库连接信息
        print("\n【4. 数据库连接信息】")
        db_url = os.getenv('BILIBILI_DATABASE_URL', 'sqlite:///./bilibili.db')
        if 'postgresql' in db_url.lower():
            print(f"数据库类型: PostgreSQL")
            # 隐藏密码
            if '@' in db_url:
                parts = db_url.split('@')
                if len(parts) == 2:
                    print(f"数据库地址: @{parts[1]}")
        else:
            print(f"数据库类型: SQLite")
            print(f"数据库文件: {db_url.replace('sqlite:///', '')}")
        
        print("\n" + "=" * 60)
        print("检查完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == '__main__':
    check_data_status()

