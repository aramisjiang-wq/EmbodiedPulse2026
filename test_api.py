#!/usr/bin/env python3
"""
测试API功能
"""
import requests
import json

API_KEY = "api_live_ZHYtQHN5TrwshXBtkya8hTxhBf1UKeoRh1pv6Z4W0Hpb0FF5J9wY"

def test_api_endpoint(base_url, endpoint, method="GET", params=None, headers=None):
    """
    测试API端点
    
    Args:
        base_url: API基础URL
        endpoint: 端点路径
        method: HTTP方法
        params: 查询参数
        headers: 请求头
    """
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    # 默认headers
    default_headers = {
        'X-Api-Key': API_KEY,
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    if headers:
        default_headers.update(headers)
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, headers=default_headers, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=params, headers=default_headers, timeout=10)
        else:
            print(f"不支持的HTTP方法: {method}")
            return None
        
        print(f"\n{'='*60}")
        print(f"测试: {method} {url}")
        print(f"{'='*60}")
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return data
            except:
                print(f"响应文本: {response.text[:500]}")
                return response.text
        else:
            print(f"错误响应: {response.text[:500]}")
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
        return None


def discover_api():
    """
    尝试发现API的基础URL和功能
    """
    print("=" * 60)
    print("API功能探索")
    print("=" * 60)
    print(f"API Key: {API_KEY[:30]}...")
    print()
    
    # 常见的API服务基础URL
    common_apis = [
        "https://api.openai.com/v1",
        "https://api.anthropic.com/v1",
        "https://api.cohere.ai/v1",
        "https://api.serpapi.com",
        "https://api.scraperapi.com",
        "https://api.brightdata.com",
        "https://api.apify.com/v2",
        "https://api.newsapi.org/v2",
        "https://api.mediastack.com/v1",
        "https://api.currentsapi.services/v1",
    ]
    
    print("尝试常见API服务...")
    for base_url in common_apis:
        print(f"\n测试: {base_url}")
        # 尝试常见的端点
        test_endpoints = ["/test", "/status", "/health", "/info", "/"]
        for endpoint in test_endpoints:
            result = test_api_endpoint(base_url, endpoint)
            if result and isinstance(result, dict):
                print(f"✅ 找到可能的API服务: {base_url}")
                return base_url
    
    print("\n未找到匹配的API服务")
    print("请提供API文档或基础URL")
    return None


if __name__ == "__main__":
    # 先尝试发现API
    base_url = discover_api()
    
    if base_url:
        print(f"\n✅ 发现API服务: {base_url}")
        print("可以继续测试其他端点")
    else:
        print("\n需要更多信息来测试API")
        print("请提供:")
        print("1. API服务的基础URL")
        print("2. API文档链接")
        print("3. 或者告诉我这个API key的来源")







