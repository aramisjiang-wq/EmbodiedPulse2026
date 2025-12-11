#!/usr/bin/env python3
"""
测试刷新新闻功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_news import fetch_and_save_news
from news_models import get_news_session, News

def test_refresh_news():
    """测试刷新新闻"""
    print("=" * 60)
    print("测试刷新新闻功能")
    print("=" * 60)
    
    # 检查当前新闻数量
    session = get_news_session()
    before_count = session.query(News).count()
    session.close()
    print(f"刷新前新闻数量: {before_count} 条")
    
    # 执行刷新
    print("\n开始执行刷新...")
    try:
        fetch_and_save_news()
        print("✅ 刷新完成")
    except Exception as e:
        print(f"❌ 刷新失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 检查刷新后新闻数量
    session = get_news_session()
    after_count = session.query(News).count()
    session.close()
    print(f"刷新后新闻数量: {after_count} 条")
    
    print(f"\n变化: {after_count - before_count} 条")
    print("=" * 60)

if __name__ == "__main__":
    test_refresh_news()
