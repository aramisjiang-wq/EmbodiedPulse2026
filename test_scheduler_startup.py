#!/usr/bin/env python3
"""
测试定时任务启动机制
验证在不同启动方式下定时任务是否能正确启动
"""
import os
import sys

def test_direct_run():
    """测试直接运行app.py"""
    print("=" * 60)
    print("测试1: 直接运行 app.py")
    print("=" * 60)
    
    # 设置环境变量
    os.environ['AUTO_FETCH_ENABLED'] = 'true'
    os.environ['AUTO_FETCH_SCHEDULE'] = '0 * * * *'
    os.environ['AUTO_FETCH_NEWS_SCHEDULE'] = '0 * * * *'
    os.environ['AUTO_FETCH_JOBS_SCHEDULE'] = '0 * * * *'
    
    try:
        # 模拟直接运行
        from app import start_scheduler
        scheduler = start_scheduler()
        if scheduler:
            print("✅ 直接运行模式：定时任务可以启动")
            scheduler.shutdown()
            return True
        else:
            print("❌ 直接运行模式：定时任务启动失败")
            return False
    except Exception as e:
        print(f"❌ 直接运行模式测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gunicorn_mode():
    """测试Gunicorn模式（通过init_scheduler）"""
    print("\n" + "=" * 60)
    print("测试2: Gunicorn模式（通过init_scheduler）")
    print("=" * 60)
    
    # 设置环境变量
    os.environ['AUTO_FETCH_ENABLED'] = 'true'
    os.environ['AUTO_FETCH_SCHEDULE'] = '0 * * * *'
    os.environ['AUTO_FETCH_NEWS_SCHEDULE'] = '0 * * * *'
    os.environ['AUTO_FETCH_JOBS_SCHEDULE'] = '0 * * * *'
    
    try:
        # 模拟Gunicorn启动
        from app import init_scheduler
        scheduler = init_scheduler()
        if scheduler:
            print("✅ Gunicorn模式：定时任务可以启动")
            scheduler.shutdown()
            return True
        else:
            print("❌ Gunicorn模式：定时任务启动失败")
            return False
    except Exception as e:
        print(f"❌ Gunicorn模式测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gunicorn_hook():
    """测试Gunicorn hook"""
    print("\n" + "=" * 60)
    print("测试3: Gunicorn hook配置")
    print("=" * 60)
    
    try:
        import gunicorn_config
        if hasattr(gunicorn_config, 'when_ready'):
            print("✅ Gunicorn when_ready hook 已配置")
            return True
        else:
            print("❌ Gunicorn when_ready hook 未配置")
            return False
    except Exception as e:
        print(f"❌ Gunicorn hook测试失败: {e}")
        return False

def test_environment_variables():
    """测试环境变量配置"""
    print("\n" + "=" * 60)
    print("测试4: 环境变量配置")
    print("=" * 60)
    
    required_vars = [
        'AUTO_FETCH_ENABLED',
        'AUTO_FETCH_SCHEDULE',
        'AUTO_FETCH_NEWS_SCHEDULE',
        'AUTO_FETCH_JOBS_SCHEDULE'
    ]
    
    all_ok = True
    for var in required_vars:
        value = os.getenv(var, '')
        if value:
            print(f"✅ {var} = {value}")
        else:
            print(f"⚠️  {var} 未设置（将使用默认值）")
    
    return all_ok

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("定时任务启动机制测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 测试1: 直接运行
    results.append(("直接运行模式", test_direct_run()))
    
    # 测试2: Gunicorn模式
    results.append(("Gunicorn模式", test_gunicorn_mode()))
    
    # 测试3: Gunicorn hook
    results.append(("Gunicorn hook", test_gunicorn_hook()))
    
    # 测试4: 环境变量
    results.append(("环境变量配置", test_environment_variables()))
    
    # 汇总结果
    print("\n" + "=" * 60)
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
        print("✅ 所有测试通过！定时任务机制配置正确")
        print("\n说明：")
        print("  - 直接运行 app.py：定时任务会在 if __name__ == '__main__' 中启动")
        print("  - Gunicorn模式：定时任务会在 when_ready hook 中启动")
        print("  - 环境变量：AUTO_FETCH_ENABLED=true 启用自动抓取")
    else:
        print("❌ 部分测试失败，请检查错误信息")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
