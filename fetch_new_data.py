#!/usr/bin/env python3
"""
抓取新的论文和新闻数据
"""
import sys
import os
from daily_arxiv import load_config, demo
from fetch_news import fetch_and_save_news

def fetch_papers(fetch_status=None, fetch_status_lock=None):
    """
    抓取新论文
    
    Args:
        fetch_status: 用于更新抓取进度的字典（可选）
        fetch_status_lock: 用于线程安全更新的锁（可选）
    """
    print("=" * 60)
    print("开始抓取新论文...")
    print("=" * 60)
    
    config = load_config('config.yaml')
    config['max_results'] = 100
    config['update_paper_links'] = False
    config['enable_dedup'] = True
    config['enable_incremental'] = True
    config['days_back'] = 14  # 只抓取最近14天的论文
    config['fetch_semantic_scholar'] = True  # 启用Semantic Scholar数据获取
    config['publish_gitpage'] = False  # 不更新gitpage
    config['publish_wechat'] = False  # 不更新wechat
    
    # 传递进度更新参数（如果提供）
    if fetch_status is not None:
        config['fetch_status'] = fetch_status
        config['fetch_status_lock'] = fetch_status_lock
        # 设置总数（关键词数量）
        keywords = config.get('keywords', {})
        if fetch_status_lock:
            with fetch_status_lock:
                fetch_status['total'] = len(keywords)
                fetch_status['message'] = f'准备抓取 {len(keywords)} 个类别...'
        else:
            fetch_status['total'] = len(keywords)
            fetch_status['message'] = f'准备抓取 {len(keywords)} 个类别...'
        print(f"📊 将抓取 {len(keywords)} 个类别的论文")
    
    try:
        demo(**config)
        print("✅ 论文抓取完成")
    except Exception as e:
        print(f"❌ 论文抓取失败: {e}")
        import traceback
        traceback.print_exc()

def fetch_news():
    """抓取新新闻"""
    print("=" * 60)
    print("开始抓取新新闻...")
    print("=" * 60)
    
    try:
        fetch_and_save_news()
        print("✅ 新闻抓取完成")
    except Exception as e:
        print(f"❌ 新闻抓取失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='抓取新的论文和新闻数据')
    parser.add_argument('--papers', action='store_true', help='只抓取论文')
    parser.add_argument('--news', action='store_true', help='只抓取新闻')
    args = parser.parse_args()
    
    if args.papers:
        fetch_papers()
    elif args.news:
        fetch_news()
    else:
        # 默认都抓取
        fetch_papers()
        print("\n")
        fetch_news()
        print("\n" + "=" * 60)
        print("✅ 所有数据抓取完成！")
        print("=" * 60)

