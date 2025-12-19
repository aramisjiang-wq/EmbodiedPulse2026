#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查特定视频的播放量数据
对比：数据库、API、前端显示
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_models import get_bilibili_session, BilibiliVideo
from bilibili_client import BilibiliClient, format_number
import requests

def check_video(bvid):
    """检查特定视频的数据"""
    print("=" * 80)
    print(f"检查视频: {bvid}")
    print("=" * 80)
    
    # 1. 检查数据库
    print("\n【1. 数据库中的数据】")
    print("-" * 80)
    session = get_bilibili_session()
    try:
        video = session.query(BilibiliVideo).filter_by(bvid=bvid).first()
        if video:
            print(f"BV号: {video.bvid}")
            print(f"标题: {video.title}")
            print(f"UP主UID: {video.uid}")
            print(f"播放量(原始): {video.play:,}")
            print(f"播放量(格式化): {video.play_formatted}")
            print(f"评论数: {video.video_review:,}")
            print(f"收藏数: {video.favorites:,}")
            print(f"更新时间: {video.updated_at}")
            print(f"发布时间: {video.pubdate}")
            db_play = video.play
        else:
            print(f"❌ 数据库中未找到该视频")
            db_play = None
    finally:
        session.close()
    
    # 2. 检查Bilibili API
    print("\n【2. Bilibili API返回的数据】")
    print("-" * 80)
    try:
        client = BilibiliClient()
        url = "https://api.bilibili.com/x/web-interface/view"
        params = {"bvid": bvid}
        
        data = client._request_json(url, params=params)
        if data and data.get('code') == 0:
            video_data = data.get('data', {})
            stat = video_data.get('stat', {})
            
            api_play = stat.get('view', 0)
            api_title = video_data.get('title', 'N/A')
            api_owner = video_data.get('owner', {})
            api_owner_name = api_owner.get('name', 'N/A')
            
            print(f"标题: {api_title}")
            print(f"UP主: {api_owner_name}")
            print(f"播放量(原始): {api_play:,}")
            print(f"评论数: {stat.get('reply', 0):,}")
            print(f"收藏数: {stat.get('favorite', 0):,}")
            print(f"点赞数: {stat.get('like', 0):,}")
            print(f"投币数: {stat.get('coin', 0):,}")
            print(f"分享数: {stat.get('share', 0):,}")
        else:
            print(f"❌ API请求失败: {data}")
            api_play = None
    except Exception as e:
        print(f"❌ API请求异常: {e}")
        import traceback
        traceback.print_exc()
        api_play = None
    
    # 3. 检查后端API返回的数据
    print("\n【3. 后端API (/api/bilibili/all) 返回的数据】")
    print("-" * 80)
    try:
        # 模拟后端API的逻辑
        session = get_bilibili_session()
        try:
            video = session.query(BilibiliVideo).filter_by(bvid=bvid).first()
            if video:
                backend_format = {
                    'bvid': video.bvid,
                    'title': video.title or '',
                    'play': video.play_formatted or '0',
                    'play_raw': video.play or 0,
                    'video_review': video.video_review_formatted or '0',
                    'favorites': video.favorites_formatted or '0',
                }
                print(f"BV号: {backend_format['bvid']}")
                print(f"标题: {backend_format['title']}")
                print(f"播放量(格式化): {backend_format['play']}")
                print(f"播放量(原始): {backend_format['play_raw']:,}")
                print(f"评论数: {backend_format['video_review']}")
                print(f"收藏数: {backend_format['favorites']}")
                backend_play = backend_format['play_raw']
            else:
                print(f"❌ 数据库中未找到该视频")
                backend_play = None
        finally:
            session.close()
    except Exception as e:
        print(f"❌ 检查后端API格式失败: {e}")
        backend_play = None
    
    # 4. 前端显示逻辑
    print("\n【4. 前端显示逻辑】")
    print("-" * 80)
    if backend_play is not None:
        # 模拟前端逻辑
        play_value = backend_play  # 前端使用 play_raw 优先
        play_formatted = format_number(play_value) if isinstance(play_value, int) else str(play_value)
        print(f"前端会使用: play_raw ({backend_play:,})")
        print(f"前端显示: {play_formatted}")
        frontend_play = backend_play
    else:
        print(f"❌ 无法确定前端显示值")
        frontend_play = None
    
    # 5. 数据对比
    print("\n【5. 数据对比】")
    print("-" * 80)
    print(f"数据库播放量: {db_play:,}" if db_play is not None else "数据库播放量: N/A")
    print(f"Bilibili API播放量: {api_play:,}" if api_play is not None else "Bilibili API播放量: N/A")
    print(f"后端API播放量: {backend_play:,}" if backend_play is not None else "后端API播放量: N/A")
    print(f"前端显示播放量: {frontend_play:,}" if frontend_play is not None else "前端显示播放量: N/A")
    
    if db_play is not None and api_play is not None:
        if db_play == api_play:
            print(f"\n✅ 数据库和API数据一致")
        else:
            diff = api_play - db_play
            print(f"\n⚠️  数据不一致！")
            print(f"   差异: {diff:,} ({'+' if diff > 0 else ''}{diff:,})")
            print(f"   数据库需要更新")
    
    if backend_play is not None and api_play is not None:
        if backend_play == api_play:
            print(f"✅ 后端API和Bilibili API数据一致")
        else:
            diff = api_play - backend_play
            print(f"⚠️  后端API数据过时（差异: {diff:,}）")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='检查特定视频的播放量数据')
    parser.add_argument('bvid', help='视频BV号')
    
    args = parser.parse_args()
    check_video(args.bvid)

