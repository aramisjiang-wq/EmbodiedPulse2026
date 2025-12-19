#!/usr/bin/env python3
"""
调试API返回0的问题
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_models import get_bilibili_session, BilibiliUp
from bilibili_client import format_number

def debug_api_logic():
    """调试API逻辑"""
    print("=" * 60)
    print("调试API返回0问题")
    print("=" * 60)
    
    session = get_bilibili_session()
    
    try:
        up = session.query(BilibiliUp).filter_by(is_active=True).first()
        
        if not up:
            print("❌ 没有找到UP主")
            return
        
        print(f"\nUP主: {up.name}")
        print(f"UID: {up.uid}")
        print()
        
        # 检查原始值
        print("数据库原始值:")
        print(f"  videos_count = {up.videos_count} (type: {type(up.videos_count).__name__})")
        print(f"  views_count = {up.views_count} (type: {type(up.views_count).__name__})")
        print(f"  views_formatted = {up.views_formatted!r} (type: {type(up.views_formatted).__name__})")
        print(f"  likes_count = {up.likes_count} (type: {type(up.likes_count).__name__})")
        print(f"  likes_formatted = {up.likes_formatted!r} (type: {type(up.likes_formatted).__name__})")
        print()
        
        # 测试format_number
        print("测试format_number函数:")
        try:
            test_videos = format_number(49)
            test_views = format_number(3307108)
            print(f"  format_number(49) = {test_videos!r}")
            print(f"  format_number(3307108) = {test_views!r}")
        except Exception as e:
            print(f"  ❌ format_number测试失败: {e}")
        print()
        
        # 模拟API逻辑
        print("模拟API逻辑:")
        print("  代码: videos = format_number(up.videos_count) if up.videos_count else '0'")
        videos = format_number(up.videos_count) if up.videos_count else '0'
        print(f"  结果: videos = {videos!r}")
        print()
        
        print("  代码: views = up.views_formatted or (format_number(up.views_count) if up.views_count else '0')")
        views = up.views_formatted or (format_number(up.views_count) if up.views_count else '0')
        print(f"  结果: views = {views!r}")
        print()
        
        print("  代码: likes = up.likes_formatted or (format_number(up.likes_count) if up.likes_count else '0')")
        likes = up.likes_formatted or (format_number(up.likes_count) if up.likes_count else '0')
        print(f"  结果: likes = {likes!r}")
        print()
        
        # 完整模拟API返回
        print("完整API返回:")
        user_stat = {
            'videos': format_number(up.videos_count) if up.videos_count else '0',
            'likes': up.likes_formatted or (format_number(up.likes_count) if up.likes_count else '0'),
            'views': up.views_formatted or (format_number(up.views_count) if up.views_count else '0'),
        }
        print(f"  user_stat = {user_stat}")
        print()
        
        # 检查问题
        if user_stat['videos'] == '0' and up.videos_count:
            print("⚠️  问题: videos返回'0'但videos_count有值")
            print(f"     videos_count = {up.videos_count}")
            print(f"     format_number({up.videos_count}) = {format_number(up.videos_count)!r}")
        
        if user_stat['views'] == '0' and (up.views_formatted or up.views_count):
            print("⚠️  问题: views返回'0'但views_formatted或views_count有值")
            print(f"     views_formatted = {up.views_formatted!r}")
            print(f"     views_count = {up.views_count}")
            if up.views_formatted:
                print(f"     为什么views_formatted有值但返回'0'？")
            elif up.views_count:
                print(f"     format_number({up.views_count}) = {format_number(up.views_count)!r}")
        
    finally:
        session.close()

if __name__ == '__main__':
    debug_api_logic()

