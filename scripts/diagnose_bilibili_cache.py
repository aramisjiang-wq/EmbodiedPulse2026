#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断B站数据缓存问题
检查数据库、后端API、缓存状态
"""

import sys
import os
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 80)
print("B站数据缓存诊断")
print("=" * 80)
print()

# 1. 检查数据库
print("【1. 检查数据库】")
print("-" * 80)
try:
    from bilibili_models import get_bilibili_session, BilibiliVideo
    
    session = get_bilibili_session()
    video = session.query(BilibiliVideo).filter_by(bvid='BV1L8qEBKEFW').first()
    
    if video:
        print(f"✅ 数据库中找到视频:")
        print(f"   BV号: {video.bvid}")
        print(f"   标题: {video.title}")
        print(f"   播放量: {video.play:,}")
        print(f"   播放量(格式化): {video.play_formatted}")
        print(f"   更新时间: {video.updated_at}")
        db_play = video.play
    else:
        print("❌ 数据库中未找到视频")
        db_play = None
    
    session.close()
except Exception as e:
    print(f"❌ 数据库检查失败: {e}")
    db_play = None

print()

# 2. 检查后端缓存
print("【2. 检查后端缓存】")
print("-" * 80)
try:
    import app
    
    with app.bilibili_cache_lock:
        cached_data = app.bilibili_cache.get('all_data')
        cache_expires_at = app.bilibili_cache.get('all_expires_at')
        
        if cached_data:
            print(f"✅ 缓存存在")
            if cache_expires_at:
                expires_time = datetime.fromtimestamp(cache_expires_at)
                now = datetime.now()
                remaining = (expires_time - now).total_seconds()
                print(f"   过期时间: {expires_time}")
                print(f"   剩余时间: {int(remaining)}秒")
                
                if remaining > 0:
                    print(f"   ⚠️  缓存仍有效，可能返回旧数据")
                else:
                    print(f"   ✅ 缓存已过期")
            
            # 检查缓存中的目标视频
            cards = cached_data.get('data', [])
            found_in_cache = False
            for card in cards:
                if card.get('user_info', {}).get('mid') == 1172054289:
                    videos = card.get('videos', [])
                    for video in videos:
                        if video.get('bvid') == 'BV1L8qEBKEFW':
                            found_in_cache = True
                            print(f"\n   缓存中的视频数据:")
                            print(f"   播放量(play): {video.get('play')}")
                            print(f"   播放量(play_raw): {video.get('play_raw')}")
                            
                            if db_play and video.get('play_raw') != db_play:
                                print(f"   ⚠️  缓存数据与数据库不一致！")
                                print(f"      数据库: {db_play:,}")
                                print(f"      缓存: {video.get('play_raw')}")
                            break
                    break
            
            if not found_in_cache:
                print("   ⚠️  缓存中未找到目标视频")
        else:
            print("❌ 缓存不存在")
    
except Exception as e:
    print(f"❌ 缓存检查失败: {e}")
    import traceback
    traceback.print_exc()

print()

# 3. 检查后端API（使用force=1）
print("【3. 检查后端API（force=1，清除缓存）】")
print("-" * 80)
try:
    url = 'http://localhost:5001/api/bilibili/all?force=1'
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            cards = data.get('data', [])
            found_in_api = False
            for card in cards:
                if card.get('user_info', {}).get('mid') == 1172054289:
                    videos = card.get('videos', [])
                    for video in videos:
                        if video.get('bvid') == 'BV1L8qEBKEFW':
                            found_in_api = True
                            print(f"✅ API返回视频数据:")
                            print(f"   BV号: {video.get('bvid')}")
                            print(f"   标题: {video.get('title')}")
                            print(f"   播放量(play): {video.get('play')}")
                            print(f"   播放量(play_raw): {video.get('play_raw')}")
                            
                            if db_play and video.get('play_raw') != db_play:
                                print(f"   ⚠️  API数据与数据库不一致！")
                                print(f"      数据库: {db_play:,}")
                                print(f"      API: {video.get('play_raw')}")
                            else:
                                print(f"   ✅ API数据与数据库一致")
                            break
                    break
            
            if not found_in_api:
                print("❌ API返回数据中未找到目标视频")
        else:
            print(f"❌ API返回失败: {data.get('error', '未知错误')}")
    else:
        print(f"❌ API请求失败: HTTP {response.status_code}")
except Exception as e:
    print(f"❌ API检查失败: {e}")
    import traceback
    traceback.print_exc()

print()

# 4. 建议
print("=" * 80)
print("诊断建议")
print("=" * 80)

if db_play and db_play >= 170000:
    print("✅ 数据库数据已更新")
    
    print("\n如果前端仍显示旧数据，请执行:")
    print("1. 清除后端缓存:")
    print("   python3 << 'EOF'")
    print("   import sys, os")
    print("   sys.path.insert(0, '/srv/EmbodiedPulse2026')")
    print("   import app")
    print("   with app.bilibili_cache_lock:")
    print("       app.bilibili_cache['all_data'] = None")
    print("       app.bilibili_cache['all_expires_at'] = None")
    print("   print('缓存已清除')")
    print("   EOF")
    print()
    print("2. 重启服务:")
    print("   systemctl restart embodiedpulse")
    print()
    print("3. 在前端使用force参数:")
    print("   访问: https://essay.gradmotion.com/bilibili?force=1")
    print("   或在浏览器控制台运行:")
    print("   fetch('/api/bilibili/all?force=1').then(r => r.json()).then(console.log)")
else:
    print("⚠️  数据库数据可能未更新，请先更新数据库")

print("=" * 80)

