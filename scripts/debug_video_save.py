#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试视频保存过程
检查为什么视频没有被保存到数据库
"""

import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_models import get_bilibili_session, BilibiliVideo, BilibiliUp
from bilibili_client import BilibiliClient
from bilibili_client import format_number

def debug_video_save(bvid='BV1L8qEBKEFW', uid=1172054289):
    """调试视频保存过程"""
    print("=" * 80)
    print(f"调试视频保存过程: {bvid}")
    print("=" * 80)
    
    session = get_bilibili_session()
    client = BilibiliClient()
    
    try:
        # 1. 检查数据库中是否已存在
        print("\n【1. 检查数据库中是否已存在】")
        print("-" * 80)
        existing = session.query(BilibiliVideo).filter_by(bvid=bvid).first()
        if existing:
            print(f"✅ 数据库中已存在: {existing.title}")
            print(f"   播放量: {existing.play:,}")
            print(f"   更新时间: {existing.updated_at}")
            return
        else:
            print(f"❌ 数据库中不存在")
        
        # 2. 从API获取视频数据
        print("\n【2. 从API获取视频数据】")
        print("-" * 80)
        
        # 方法1：通过 get_all_data 获取
        print("方法1: 通过 get_all_data 获取（fetch_all=True）...")
        data = client.get_all_data(uid, fetch_all=True)
        
        if not data:
            print("❌ get_all_data 返回 None")
            return
        
        videos = data.get('videos', [])
        print(f"✅ 获取到 {len(videos)} 个视频")
        
        # 查找目标视频
        target_video = None
        for v in videos:
            if v.get('bvid') == bvid:
                target_video = v
                break
        
        if not target_video:
            print(f"❌ 在返回的 {len(videos)} 个视频中未找到 {bvid}")
            print(f"   前5个视频的BV号: {[v.get('bvid') for v in videos[:5]]}")
            return
        
        print(f"✅ 找到目标视频: {target_video.get('title')}")
        print(f"   数据格式: {target_video}")
        
        # 3. 模拟保存过程
        print("\n【3. 模拟保存过程】")
        print("-" * 80)
        
        video_data = target_video
        bvid_check = video_data.get('bvid', '')
        print(f"BV号检查: '{bvid_check}' (长度: {len(bvid_check)})")
        
        if not bvid_check:
            print("❌ BV号为空，跳过保存")
            return
        
        # 检查字段
        print(f"字段检查:")
        print(f"  bvid: {video_data.get('bvid')}")
        print(f"  title: {video_data.get('title')}")
        print(f"  play: {video_data.get('play')}")
        print(f"  aid: {video_data.get('aid')}")
        print(f"  pubdate: {video_data.get('pubdate')}")
        
        # 4. 尝试保存
        print("\n【4. 尝试保存到数据库】")
        print("-" * 80)
        
        try:
            # 查找或创建视频记录
            video = session.query(BilibiliVideo).filter_by(bvid=bvid).first()
            is_new = False
            if not video:
                print("创建新视频记录...")
                video = BilibiliVideo(bvid=bvid, uid=uid)
                session.add(video)
                is_new = True
            else:
                print("更新已存在的视频记录...")
            
            # 更新视频信息
            video.aid = video_data.get('aid', 0)
            video.title = video_data.get('title', '')
            video.pic = video_data.get('pic', '')
            video.description = video_data.get('description', '')
            video.length = video_data.get('length', '')
            
            # 统计数据
            play_raw = video_data.get('play', 0) or 0
            print(f"播放量: {play_raw}")
            if play_raw > 0:
                video.play = play_raw
                video.play_formatted = format_number(play_raw)
            
            video.video_review = video_data.get('video_review', 0) or 0
            video.video_review_formatted = format_number(video.video_review)
            video.favorites = video_data.get('favorites', 0) or 0
            video.favorites_formatted = format_number(video.favorites)
            
            # 时间
            pubdate_raw = video_data.get('pubdate', 0)
            if pubdate_raw:
                video.pubdate_raw = pubdate_raw
                video.pubdate = datetime.fromtimestamp(pubdate_raw)
            
            video.url = f"https://www.bilibili.com/video/{bvid}"
            video.is_deleted = False
            video.updated_at = datetime.now()
            
            print("准备提交...")
            session.commit()
            print(f"✅ 保存成功！{'新增' if is_new else '更新'}")
            
            # 验证
            saved = session.query(BilibiliVideo).filter_by(bvid=bvid).first()
            if saved:
                print(f"✅ 验证成功: 数据库中已存在，播放量: {saved.play:,}")
            else:
                print(f"❌ 验证失败: 提交后数据库中仍不存在")
                
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            import traceback
            traceback.print_exc()
            session.rollback()
        
    finally:
        session.close()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='调试视频保存过程')
    parser.add_argument('--bvid', default='BV1L8qEBKEFW', help='视频BV号')
    parser.add_argument('--uid', type=int, default=1172054289, help='UP主UID')
    
    args = parser.parse_args()
    debug_video_save(args.bvid, args.uid)

