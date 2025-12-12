#!/usr/bin/env python3
"""
测试APITube API功能
参考文档: https://docs.apitube.io
"""
import requests
import json
from datetime import datetime, timedelta

API_KEY = "api_live_ZHYtQHN5TrwshXBtkya8hTxhBf1UKeoRh1pv6Z4W0Hpb0FF5J9wY"
BASE_URL = "https://api.apitube.io/v1"

def test_apitube_api():
    """
    测试APITube API的基本功能
    """
    print("=" * 60)
    print("APITube API 功能测试")
    print("=" * 60)
    print(f"API Key: {API_KEY[:30]}...")
    print(f"Base URL: {BASE_URL}")
    print()
    
    headers = {
        "X-API-Key": API_KEY
    }
    
    # 测试1: 获取最新新闻
    print("测试1: 获取最新新闻（everything端点）")
    print("-" * 60)
    try:
        url = f"{BASE_URL}/news/everything"
        params = {
            "per_page": 5,  # 只获取5条用于测试
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功获取数据")
            print(f"响应结构: {list(data.keys())}")
            
            if 'data' in data:
                articles = data['data']
                print(f"新闻数量: {len(articles)}")
                if articles:
                    print(f"\n第一条新闻示例:")
                    article = articles[0]
                    print(f"  标题: {article.get('title', 'N/A')}")
                    print(f"  来源: {article.get('source', {}).get('name', 'N/A')}")
                    print(f"  发布时间: {article.get('published_at', 'N/A')}")
                    print(f"  URL: {article.get('url', 'N/A')[:80]}...")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应: {response.text[:500]}")
    
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    print()
    
    # 测试2: 按关键词搜索（机器人相关）
    print("测试2: 搜索机器人相关新闻")
    print("-" * 60)
    try:
        url = f"{BASE_URL}/news/everything"
        params = {
            "title": "robot OR robotics OR embodied AI",
            "language.code": "en",
            "per_page": 5,
            "sort": "published_at",  # 按发布时间排序
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                articles = data['data']
                print(f"✅ 找到 {len(articles)} 条相关新闻")
                for i, article in enumerate(articles[:3], 1):
                    print(f"\n{i}. {article.get('title', 'N/A')}")
                    print(f"   来源: {article.get('source', {}).get('name', 'N/A')}")
                    print(f"   时间: {article.get('published_at', 'N/A')}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应: {response.text[:500]}")
    
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    print()
    
    # 测试3: 获取今天的新闻
    print("测试3: 获取今天的新闻")
    print("-" * 60)
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        url = f"{BASE_URL}/news/everything"
        params = {
            "title": "robot OR robotics",
            "published_at.from": today,
            "published_at.to": today,
            "per_page": 5,
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                articles = data['data']
                print(f"✅ 今天找到 {len(articles)} 条新闻")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_apitube_api()







