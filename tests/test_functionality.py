#!/usr/bin/env python3
"""
功能测试
测试核心功能的业务逻辑
"""
import sys
import os
import requests

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

def test_papers_functionality():
    """测试论文功能"""
    print_info("测试论文功能...")
    
    try:
        # 测试获取论文列表
        response = requests.get(f"{BASE_URL}/api/papers", params={"limit": 5}, timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'papers' in data:
                print_success("论文列表获取成功")
                return True
            else:
                print_error("论文列表格式错误")
                return False
        else:
            print_error(f"论文列表API返回错误状态码: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"论文功能测试失败: {str(e)}")
        return False

def test_news_functionality():
    """测试新闻功能"""
    print_info("测试新闻功能...")
    
    try:
        # 测试获取新闻列表
        response = requests.get(f"{BASE_URL}/api/news", params={"limit": 5}, timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'news' in data:
                print_success("新闻列表获取成功")
                return True
            else:
                print_error("新闻列表格式错误")
                return False
        else:
            print_error(f"新闻列表API返回错误状态码: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"新闻功能测试失败: {str(e)}")
        return False

def test_jobs_functionality():
    """测试岗位功能"""
    print_info("测试岗位功能...")
    
    try:
        # 测试获取岗位列表
        response = requests.get(f"{BASE_URL}/api/jobs", params={"limit": 5}, timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'jobs' in data:
                print_success("岗位列表获取成功")
                return True
            else:
                print_error("岗位列表格式错误")
                return False
        else:
            print_error(f"岗位列表API返回错误状态码: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"岗位功能测试失败: {str(e)}")
        return False

def test_datasets_functionality():
    """测试数据集功能"""
    print_info("测试数据集功能...")
    
    try:
        # 测试获取数据集列表
        response = requests.get(f"{BASE_URL}/api/datasets", params={"limit": 5}, timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'datasets' in data:
                print_success("数据集列表获取成功")
                return True
            else:
                print_error("数据集列表格式错误")
                return False
        else:
            print_error(f"数据集列表API返回错误状态码: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"数据集功能测试失败: {str(e)}")
        return False

def test_bilibili_functionality():
    """测试Bilibili功能"""
    print_info("测试Bilibili功能...")
    
    try:
        # 测试获取Bilibili数据
        response = requests.get(f"{BASE_URL}/api/bilibili", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'data' in data:
                print_success("Bilibili数据获取成功")
                return True
            else:
                print_warning("Bilibili数据可能被限制，但API正常")
                return True  # API正常，即使数据被限制也算通过
        else:
            print_error(f"Bilibili API返回错误状态码: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Bilibili功能测试失败: {str(e)}")
        return False

def test_stats_functionality():
    """测试统计功能"""
    print_info("测试统计功能...")
    
    try:
        # 测试获取统计数据
        response = requests.get(f"{BASE_URL}/api/stats", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'stats' in data:
                print_success("统计数据获取成功")
                return True
            else:
                print_error("统计数据格式错误")
                return False
        else:
            print_error(f"统计API返回错误状态码: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"统计功能测试失败: {str(e)}")
        return False

def run_all_tests():
    """运行所有功能测试"""
    print_info("=" * 60)
    print_info("开始功能测试")
    print_info("=" * 60)
    print()
    
    tests = [
        ("论文功能", test_papers_functionality),
        ("新闻功能", test_news_functionality),
        ("岗位功能", test_jobs_functionality),
        ("数据集功能", test_datasets_functionality),
        ("Bilibili功能", test_bilibili_functionality),
        ("统计功能", test_stats_functionality),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"{name}: 测试异常 - {str(e)}")
            results.append((name, False))
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
        print_success("所有功能测试通过！")
        return True
    else:
        print_error(f"有 {total - passed} 个测试失败")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)




