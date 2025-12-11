#!/usr/bin/env python3
"""
验证定时任务机制 - 检查部署后定时任务是否能自动启动
"""
import os
import sys

def verify_scheduler():
    """验证定时任务机制"""
    print("=" * 60)
    print("定时任务机制验证")
    print("=" * 60)
    
    results = []
    
    # 1. 检查APScheduler是否安装
    print("\n1. 检查APScheduler依赖...")
    try:
        import apscheduler
        print(f"✅ APScheduler 已安装 (版本: {apscheduler.__version__})")
        results.append(("APScheduler依赖", True))
    except ImportError:
        print("❌ APScheduler 未安装")
        print("   安装命令: pip install apscheduler")
        results.append(("APScheduler依赖", False))
    
    # 2. 检查环境变量
    print("\n2. 检查环境变量...")
    auto_fetch_enabled = os.getenv('AUTO_FETCH_ENABLED', 'false').lower() == 'true'
    if auto_fetch_enabled:
        print("✅ AUTO_FETCH_ENABLED=true")
    else:
        print("⚠️  AUTO_FETCH_ENABLED 未设置为 true（将使用默认值 false）")
    results.append(("环境变量", auto_fetch_enabled))
    
    # 3. 检查init_scheduler函数
    print("\n3. 检查init_scheduler函数...")
    try:
        from app import init_scheduler
        print("✅ init_scheduler 函数存在")
        results.append(("init_scheduler函数", True))
    except Exception as e:
        print(f"❌ init_scheduler 函数不存在或导入失败: {e}")
        results.append(("init_scheduler函数", False))
    
    # 4. 检查Gunicorn hook
    print("\n4. 检查Gunicorn hook...")
    try:
        import gunicorn_config
        if hasattr(gunicorn_config, 'when_ready'):
            print("✅ Gunicorn when_ready hook 已配置")
            results.append(("Gunicorn hook", True))
        else:
            print("❌ Gunicorn when_ready hook 未配置")
            results.append(("Gunicorn hook", False))
    except Exception as e:
        print(f"❌ 检查Gunicorn hook失败: {e}")
        results.append(("Gunicorn hook", False))
    
    # 5. 测试定时任务启动（如果环境变量启用）
    if auto_fetch_enabled:
        print("\n5. 测试定时任务启动...")
        try:
            from app import init_scheduler
            scheduler = init_scheduler()
            if scheduler:
                jobs = scheduler.get_jobs()
                print(f"✅ 定时任务启动成功，共 {len(jobs)} 个任务")
                for job in jobs:
                    print(f"   - {job.name}: 下次执行 = {job.next_run_time}")
                scheduler.shutdown()
                results.append(("定时任务启动", True))
            else:
                print("❌ 定时任务启动失败")
                results.append(("定时任务启动", False))
        except Exception as e:
            print(f"❌ 定时任务启动测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append(("定时任务启动", False))
    else:
        print("\n5. 跳过定时任务启动测试（AUTO_FETCH_ENABLED=false）")
        results.append(("定时任务启动", None))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        if result is None:
            status = "⏭️  跳过"
        elif result:
            status = "✅ 通过"
        else:
            status = "❌ 失败"
            all_passed = False
        print(f"{name}: {status}")
    
    print("=" * 60)
    if all_passed:
        print("✅ 所有检查通过！定时任务机制配置正确")
        print("\n部署建议：")
        print("  1. 确保设置 AUTO_FETCH_ENABLED=true")
        print("  2. 使用 Gunicorn 启动（生产环境）")
        print("  3. 查看启动日志确认定时任务已启动")
    else:
        print("❌ 部分检查失败，请修复后重新验证")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(verify_scheduler())
