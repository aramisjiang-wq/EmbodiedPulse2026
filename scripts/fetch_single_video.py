#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接通过BV号抓取单个视频信息
不依赖UP主列表API，避免412风控影响
"""

import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_models import get_bilibili_session, BilibiliVideo
from bilibili_client import BilibiliClient, format_number
import requests

def fetch_single_video_by_bvid(bvid: str, uid: int = None):
    """
    通过BV号直接抓取单个视频信息
    
    Args:
        bvid: 视频BV号
        uid: UP主UID（如果已知，可以传入；否则从API获取）
    
    Returns:
        bool: 是否成功
    """
    print("=" * 80)
    print(f"通过BV号直接抓取视频: {bvid}")
    print("=" * 80)
    
    session = get_bilibili_session()
    
    try:
        # 1. 使用公开API直接获取视频信息（不需要认证）
        print(f"\n【1. 从公开API获取视频信息】")
        print("-" * 80)
        
        url = "https://api.bilibili.com/x/web-interface/view"
        params = {"bvid": bvid}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"❌ API请求失败: {e}")
            return False
        
        if data.get('code') != 0:
            print(f"❌ API返回错误: {data.get('message', '未知错误')}")
            return False
        
        video_data = data.get('data', {})
        if not video_data:
            print(f"❌ API返回数据为空")
            return False
        
        # 提取视频信息
        stat = video_data.get('stat', {})
        owner = video_data.get('owner', {})
        
        video_info = {
            'bvid': video_data.get('bvid', ''),
            'aid': video_data.get('aid', 0),
            'title': video_data.get('title', ''),
            'pic': video_data.get('pic', ''),
            'description': video_data.get('desc', ''),
            'length': video_data.get('duration', ''),  # 格式需要转换
            'play': stat.get('view', 0),
            'video_review': stat.get('reply', 0),
            'favorites': stat.get('favorite', 0),
            'pubdate': video_data.get('pubdate', 0),  # 时间戳（秒）
            'uid': owner.get('mid', uid) if uid is None else uid,
        }
        
        print(f"✅ 获取成功:")
        print(f"   标题: {video_info['title']}")
        print(f"   UP主UID: {video_info['uid']}")
        print(f"   播放量: {video_info['play']:,}")
        print(f"   发布时间: {datetime.fromtimestamp(video_info['pubdate'])}")
        
        # 2. 保存到数据库
        print(f"\n【2. 保存到数据库】")
        print("-" * 80)
        
        # 查找或创建视频记录
        video = session.query(BilibiliVideo).filter_by(bvid=bvid).first()
        is_new = False
        if not video:
            video = BilibiliVideo(bvid=bvid, uid=video_info['uid'])
            session.add(video)
            is_new = True
            print(f"创建新视频记录...")
        else:
            print(f"更新已存在的视频记录...")
        
        # 更新视频信息
        video.aid = video_info['aid']
        video.title = video_info['title']
        video.pic = video_info['pic']
        video.description = video_info['description']
        video.length = video_info['length']
        
        # 统计数据
        video.play = video_info['play']
        video.play_formatted = format_number(video_info['play'])
        video.video_review = video_info['video_review']
        video.video_review_formatted = format_number(video_info['video_review'])
        video.favorites = video_info['favorites']
        video.favorites_formatted = format_number(video_info['favorites'])
        
        # 时间
        video.pubdate_raw = video_info['pubdate']
        video.pubdate = datetime.fromtimestamp(video_info['pubdate'])
        
        video.url = f"https://www.bilibili.com/video/{bvid}"
        video.is_deleted = False
        video.updated_at = datetime.now()
        
        session.commit()
        
        action = "新增" if is_new else "更新"
        print(f"✅ {action}成功！")
        print(f"   播放量: {video.play:,}")
        print(f"   更新时间: {video.updated_at}")
        
        return True
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='通过BV号直接抓取单个视频信息')
    parser.add_argument('bvid', help='视频BV号')
    parser.add_argument('--uid', type=int, help='UP主UID（可选，如果不提供会从API获取）')
    
    args = parser.parse_args()
    
    success = fetch_single_video_by_bvid(args.bvid, args.uid)
    if success:
        print("\n✅ 视频抓取成功！")
    else:
        print("\n❌ 视频抓取失败！")
        sys.exit(1)

