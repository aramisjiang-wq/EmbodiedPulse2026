#!/usr/bin/env python3
"""
API端点测试
测试所有API端点的可用性和响应格式
"""
import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:5001"
TIMEOUT = 10

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def test_endpoint(name, method, endpoint, expected_status=200, data=None, params=None):
    """
    测试API端点
    
    Args:
        name: 测试名称
        method: HTTP方法
        endpoint: 端点路径
        expected_status: 期望的HTTP状态码
        data: POST数据
        params: 查询参数
    """
    try:
        url = f"{BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, params=params, timeout=TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=data, params=params, timeout=TIMEOUT)
        else:
            print_error(f"{name}: 不支持的HTTP方法 {method}")
            return False
        
        if response.status_code == expected_status:
            try:
                result = response.json()
                print_success(f"{name}: {method} {endpoint} - 状态码 {response.status_code}")
                return True
            except json.JSONDecodeError:
                print_warning(f"{name}: 响应不是JSON格式")
                return True  # 某些端点可能返回非JSON
        else:
            print_error(f"{name}: {method} {endpoint} - 状态码 {response.status_code} (期望 {expected_status})")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error(f"{name}: 无法连接到服务器 {BASE_URL}")
        return False
    except requests.exceptions.Timeout:
        print_error(f"{name}: 请求超时")
        return False
    except Exception as e:
        print_error(f"{name}: 错误 - {str(e)}")
        return False

def run_all_tests():
    """运行所有API端点测试"""
    print_info("=" * 60)
    print_info("开始API端点测试")
    print_info("=" * 60)
    print()
    
    tests = [
        # 核心API
        ("首页", "GET", "/", 200),
        ("论文列表", "GET", "/api/papers", 200, None, {"limit": 10}),
        ("统计数据", "GET", "/api/stats", 200),
        ("搜索", "GET", "/api/search", 200, None, {"q": "robot"}),
        
        # 新闻API
        ("新闻列表", "GET", "/api/news", 200, None, {"limit": 10}),
        ("新闻抓取状态", "GET", "/api/fetch-news-status", 200),
        
        # 岗位API
        ("岗位列表", "GET", "/api/jobs", 200, None, {"limit": 10}),
        
        # 数据集API
        ("数据集列表", "GET", "/api/datasets", 200, None, {"limit": 10}),
        
        # Bilibili API
        ("Bilibili数据", "GET", "/api/bilibili", 200),
        
        # 抓取状态API
        ("抓取状态", "GET", "/api/fetch-status", 200),
        ("刷新状态", "GET", "/api/refresh-status", 200),
    ]
    
    results = []
    for test in tests:
        name, method, endpoint, expected_status = test[:4]
        data = test[4] if len(test) > 4 else None
        params = test[5] if len(test) > 5 else None
        
        result = test_endpoint(name, method, endpoint, expected_status, data, params)
        results.append((name, result))
        print()
    
    # 统计结果
    print_info("=" * 60)
    print_info("测试结果统计")
    print_info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}: 通过")
        else:
            print_error(f"{name}: 失败")
    
    print()
    print_info(f"总计: {passed}/{total} 通过")
    
    if passed == total:
        print_success("所有API端点测试通过！")
        return True
    else:
        print_error(f"有 {total - passed} 个测试失败")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)




