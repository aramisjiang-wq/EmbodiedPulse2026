#!/usr/bin/env python3
"""
数据库连接测试
测试所有数据库的连接和数据完整性
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

def test_database(name, get_session_func, model_class):
    """
    测试数据库连接
    
    Args:
        name: 数据库名称
        get_session_func: 获取session的函数
        model_class: 模型类
    """
    try:
        session = get_session_func()
        
        # 测试查询
        count = session.query(model_class).count()
        
        print_success(f"{name}: 连接成功，记录数: {count}")
        session.close()
        return True
        
    except Exception as e:
        print_error(f"{name}: 连接失败 - {str(e)}")
        return False

def run_all_tests():
    """运行所有数据库测试"""
    print_info("=" * 60)
    print_info("开始数据库连接测试")
    print_info("=" * 60)
    print()
    
    results = []
    
    # 测试主数据库（论文）
    try:
        from models import get_session, Paper
        result = test_database("主数据库（论文）", get_session, Paper)
        results.append(("主数据库（论文）", result))
    except Exception as e:
        print_error(f"主数据库测试失败: {str(e)}")
        results.append(("主数据库（论文）", False))
    
    print()
    
    # 测试岗位数据库
    try:
        from jobs_models import get_jobs_session, Job
        result = test_database("岗位数据库", get_jobs_session, Job)
        results.append(("岗位数据库", result))
    except Exception as e:
        print_error(f"岗位数据库测试失败: {str(e)}")
        results.append(("岗位数据库", False))
    
    print()
    
    # 测试数据集数据库
    try:
        from datasets_models import get_datasets_session, Dataset
        result = test_database("数据集数据库", get_datasets_session, Dataset)
        results.append(("数据集数据库", result))
    except Exception as e:
        print_error(f"数据集数据库测试失败: {str(e)}")
        results.append(("数据集数据库", False))
    
    print()
    
    # 测试新闻数据库
    try:
        from news_models import get_news_session, News
        result = test_database("新闻数据库", get_news_session, News)
        results.append(("新闻数据库", result))
    except Exception as e:
        print_error(f"新闻数据库测试失败: {str(e)}")
        results.append(("新闻数据库", False))
    
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
        print_success("所有数据库连接测试通过！")
        return True
    else:
        print_error(f"有 {total - passed} 个测试失败")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)




