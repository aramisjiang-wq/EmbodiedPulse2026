#!/usr/bin/env python3
"""
诊断论文数据获取、更新和显示问题
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_env_config():
    """检查环境变量配置"""
    print("=" * 60)
    print("1. 检查环境变量配置")
    print("=" * 60)
    
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ .env 文件存在: {env_path}")
    else:
        print(f"❌ .env 文件不存在: {env_path}")
        return False
    
    auto_fetch_enabled = os.getenv('AUTO_FETCH_ENABLED', 'false').lower() == 'true'
    auto_fetch_schedule = os.getenv('AUTO_FETCH_SCHEDULE', '0 * * * *')
    
    print(f"   AUTO_FETCH_ENABLED: {auto_fetch_enabled}")
    print(f"   AUTO_FETCH_SCHEDULE: {auto_fetch_schedule}")
    
    if not auto_fetch_enabled:
        print("   ⚠️  定时任务未启用！")
        return False
    
    print("   ✅ 定时任务已启用")
    return True

def check_scheduler_status():
    """检查定时任务调度器状态"""
    print("\n" + "=" * 60)
    print("2. 检查定时任务调度器")
    print("=" * 60)
    
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        print("   ✅ APScheduler 已安装")
    except ImportError:
        print("   ❌ APScheduler 未安装")
        return False
    
    # 检查是否有运行的调度器进程（通过日志或PID文件）
    log_file = project_root / 'app.log'
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent_lines = lines[-50:] if len(lines) > 50 else lines
            scheduler_found = any('定时任务' in line or 'scheduler' in line.lower() for line in recent_lines)
            if scheduler_found:
                print("   ✅ 调度器相关日志存在")
            else:
                print("   ⚠️  未找到调度器相关日志")
    else:
        print("   ⚠️  日志文件不存在")
    
    return True

def check_fetch_function():
    """检查抓取函数是否可用"""
    print("\n" + "=" * 60)
    print("3. 检查数据抓取函数")
    print("=" * 60)
    
    try:
        from fetch_new_data import fetch_papers
        print("   ✅ fetch_papers 函数可导入")
    except ImportError as e:
        print(f"   ❌ 无法导入 fetch_papers: {e}")
        return False
    
    try:
        from daily_arxiv import load_config, demo
        print("   ✅ daily_arxiv 模块可导入")
    except ImportError as e:
        print(f"   ❌ 无法导入 daily_arxiv: {e}")
        return False
    
    # 检查配置文件
    config_path = project_root / 'config.yaml'
    if config_path.exists():
        print(f"   ✅ 配置文件存在: {config_path}")
    else:
        print(f"   ❌ 配置文件不存在: {config_path}")
        return False
    
    return True

def check_database():
    """检查数据库状态"""
    print("\n" + "=" * 60)
    print("4. 检查数据库状态")
    print("=" * 60)
    
    try:
        from models import get_session, Paper
        from sqlalchemy import func
        
        session = get_session()
        
        # 检查论文总数
        total_count = session.query(func.count(Paper.id)).scalar()
        print(f"   📊 数据库论文总数: {total_count}")
        
        # 检查最近7天的论文
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_count = session.query(func.count(Paper.id)).filter(
            Paper.created_at >= seven_days_ago
        ).scalar()
        print(f"   📊 最近7天新增论文: {recent_count}")
        
        # 检查2025年12月16日的论文
        target_date = datetime(2025, 12, 16).date()
        target_papers = session.query(Paper).filter(
            func.date(Paper.publish_date) == target_date
        ).all()
        print(f"   📊 2025年12月16日的论文数量: {len(target_papers)}")
        
        if len(target_papers) > 0:
            print(f"   ✅ 找到 {len(target_papers)} 篇12月16日的论文")
            for i, paper in enumerate(target_papers[:3], 1):
                print(f"      {i}. {paper.title[:60]}...")
        else:
            print("   ⚠️  未找到12月16日的论文")
        
        # 检查最新的论文
        latest_paper = session.query(Paper).order_by(Paper.created_at.desc()).first()
        if latest_paper:
            print(f"   📊 最新论文创建时间: {latest_paper.created_at}")
            print(f"   📊 最新论文发布日期: {latest_paper.publish_date}")
            print(f"   📊 最新论文标题: {latest_paper.title[:60]}...")
        
        session.close()
        return True
    except Exception as e:
        print(f"   ❌ 数据库检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_date_filter():
    """检查日期过滤逻辑"""
    print("\n" + "=" * 60)
    print("5. 检查日期过滤逻辑")
    print("=" * 60)
    
    # 检查 fetch_new_data.py 中的 days_back 配置
    fetch_new_data_path = project_root / 'fetch_new_data.py'
    if fetch_new_data_path.exists():
        with open(fetch_new_data_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'days_back' in content:
                # 提取 days_back 的值
                import re
                match = re.search(r"days_back\s*=\s*(\d+)", content)
                if match:
                    days_back = int(match.group(1))
                    print(f"   📊 days_back 配置: {days_back} 天")
                    
                    # 计算应该抓取的日期范围
                    today = datetime.now().date()
                    start_date = today - timedelta(days=days_back)
                    target_date = datetime(2025, 12, 16).date()
                    
                    print(f"   📊 今天日期: {today}")
                    print(f"   📊 抓取范围: {start_date} 到 {today}")
                    print(f"   📊 目标日期 (2025-12-16): {target_date}")
                    
                    if start_date <= target_date <= today:
                        print(f"   ✅ 12月16日在抓取范围内")
                    else:
                        print(f"   ⚠️  12月16日不在抓取范围内！")
                        print(f"      需要调整 days_back 或等待时间")
                else:
                    print("   ⚠️  无法从代码中提取 days_back 值")
            else:
                print("   ⚠️  代码中未找到 days_back 配置")
    else:
        print(f"   ❌ fetch_new_data.py 不存在")

def check_api_routes():
    """检查API路由"""
    print("\n" + "=" * 60)
    print("6. 检查API路由")
    print("=" * 60)
    
    app_py_path = project_root / 'app.py'
    if app_py_path.exists():
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            routes = [
                ('/api/papers', '获取论文列表'),
                ('/api/fetch', '手动触发抓取'),
                ('/api/refresh-all', '刷新所有数据'),
                ('/api/refresh-papers', '刷新论文数据'),
            ]
            
            for route, desc in routes:
                if route in content:
                    print(f"   ✅ {route} - {desc}")
                else:
                    print(f"   ⚠️  {route} - 未找到")
    else:
        print(f"   ❌ app.py 不存在")

def check_frontend():
    """检查前端代码"""
    print("\n" + "=" * 60)
    print("7. 检查前端代码")
    print("=" * 60)
    
    # 检查刷新按钮
    index_html_path = project_root / 'templates' / 'index.html'
    if index_html_path.exists():
        with open(index_html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            if 'refreshPapersBtn' in content:
                print("   ✅ 刷新论文按钮存在")
            else:
                print("   ⚠️  刷新论文按钮不存在")
            
            if '/api/fetch' in content or '/api/refresh' in content:
                print("   ✅ 刷新API调用存在")
            else:
                print("   ⚠️  刷新API调用不存在")
    else:
        print(f"   ⚠️  index.html 不存在")
    
    # 检查前端JS
    app_js_path = project_root / 'static' / 'js' / 'app.js'
    if app_js_path.exists():
        with open(app_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            if 'refreshPapersBtn' in content:
                print("   ✅ 刷新按钮事件监听器存在")
            else:
                print("   ⚠️  刷新按钮事件监听器不存在")
            
            if 'loadPapers' in content:
                print("   ✅ loadPapers 函数存在")
            else:
                print("   ⚠️  loadPapers 函数不存在")

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("论文数据获取、更新和显示问题诊断")
    print("=" * 60)
    print(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    results.append(("环境变量配置", check_env_config()))
    results.append(("定时任务调度器", check_scheduler_status()))
    results.append(("数据抓取函数", check_fetch_function()))
    results.append(("数据库状态", check_database()))
    check_date_filter()
    check_api_routes()
    check_frontend()
    
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")
    
    print("\n建议:")
    print("1. 如果定时任务未启用，检查 .env 文件中的 AUTO_FETCH_ENABLED")
    print("2. 如果数据库中没有12月16日的论文，手动执行一次抓取:")
    print("   python3 fetch_new_data.py --papers")
    print("3. 检查服务器日志 app.log 查看定时任务执行情况")
    print("4. 测试手动刷新按钮是否正常工作")

if __name__ == '__main__':
    main()

