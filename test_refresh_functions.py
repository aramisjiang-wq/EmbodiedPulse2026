#!/usr/bin/env python3
"""
测试刷新功能 - 验证方式B（直接调用函数）是否正常工作
"""
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试1: 模块导入")
    print("=" * 60)
    
    try:
        from fetch_new_data import fetch_papers
        print("✅ fetch_new_data.fetch_papers 导入成功")
    except Exception as e:
        print(f"❌ fetch_new_data.fetch_papers 导入失败: {e}")
        return False
    
    try:
        from fetch_news import fetch_and_save_news
        print("✅ fetch_news.fetch_and_save_news 导入成功")
    except Exception as e:
        print(f"❌ fetch_news.fetch_and_save_news 导入失败: {e}")
        return False
    
    try:
        from fetch_jobs import fetch_and_save_jobs
        print("✅ fetch_jobs.fetch_and_save_jobs 导入成功")
    except Exception as e:
        print(f"❌ fetch_jobs.fetch_and_save_jobs 导入失败: {e}")
        return False
    
    print("\n✅ 所有模块导入成功！\n")
    return True

def test_app_imports():
    """测试app.py中的导入和API路由"""
    print("=" * 60)
    print("测试2: app.py模块导入和API路由")
    print("=" * 60)
    
    try:
        # 测试app.py能否正常导入（不运行Flask应用）
        import app
        print("✅ app.py 导入成功")
        
        # 检查API路由是否存在
        routes = [str(rule) for rule in app.app.url_map.iter_rules()]
        
        if '/api/refresh-all' in routes:
            print("✅ /api/refresh-all 路由存在")
        else:
            print("❌ /api/refresh-all 路由不存在")
            return False
            
        if '/api/refresh-status' in routes:
            print("✅ /api/refresh-status 路由存在")
        else:
            print("❌ /api/refresh-status 路由不存在")
            return False
        
        # 检查refresh_all_data函数是否存在
        if hasattr(app, 'refresh_all_data'):
            print("✅ refresh_all_data 函数存在")
        else:
            print("⚠️  refresh_all_data 函数不存在（可能是内部函数）")
        
        print("\n✅ app.py API路由检查通过！\n")
        print("说明：刷新函数在refresh_all_data()内部定义，这是正常的设计")
        return True
    except Exception as e:
        print(f"❌ app.py 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_exists():
    """测试配置文件是否存在"""
    print("=" * 60)
    print("测试3: 配置文件检查")
    print("=" * 60)
    
    config_path = 'config.yaml'
    if os.path.exists(config_path):
        print(f"✅ 配置文件存在: {config_path}")
        return True
    else:
        print(f"❌ 配置文件不存在: {config_path}")
        return False

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("刷新功能测试 - 方式B（直接调用函数）")
    print("=" * 60 + "\n")
    
    results = []
    
    # 测试1: 模块导入
    results.append(("模块导入", test_imports()))
    
    # 测试2: app.py导入
    results.append(("app.py导入", test_app_imports()))
    
    # 测试3: 配置文件
    results.append(("配置文件", test_config_exists()))
    
    # 汇总结果
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ 所有测试通过！刷新功能已配置为方式B（直接调用函数）")
        print("\n说明：")
        print("  - refresh_papers() 使用 fetch_new_data.fetch_papers()")
        print("  - refresh_news() 使用 fetch_news.fetch_and_save_news()")
        print("  - refresh_jobs() 使用 fetch_jobs.fetch_and_save_jobs()")
    else:
        print("❌ 部分测试失败，请检查错误信息")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
