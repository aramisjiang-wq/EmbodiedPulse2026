#!/usr/bin/env python3
"""
刷新功能诊断脚本
用于排查"刷新全局数据"功能的问题
"""
import os
import sys
import traceback

def check_config_file():
    """检查配置文件"""
    print("=" * 60)
    print("1. 检查配置文件")
    print("=" * 60)
    
    config_path = 'config.yaml'
    if os.path.exists(config_path):
        print(f"✅ 配置文件存在: {config_path}")
        try:
            from daily_arxiv import load_config
            config = load_config(config_path)
            print(f"✅ 配置文件加载成功")
            print(f"   - max_results: {config.get('max_results', 'N/A')}")
            print(f"   - keywords数量: {len(config.get('keywords', {}))}")
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
            return False
    else:
        print(f"❌ 配置文件不存在: {config_path}")
        return False
    
    return True

def check_dependencies():
    """检查依赖"""
    print("\n" + "=" * 60)
    print("2. 检查Python依赖")
    print("=" * 60)
    
    required_modules = [
        'flask',
        'sqlalchemy',
        'arxiv',
        'requests',
        'feedparser',
        'beautifulsoup4',
        'apscheduler'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - 未安装")
            missing.append(module)
    
    if missing:
        print(f"\n缺少依赖: {', '.join(missing)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True

def check_database():
    """检查数据库"""
    print("\n" + "=" * 60)
    print("3. 检查数据库")
    print("=" * 60)
    
    # 检查论文数据库
    papers_db = 'papers.db'
    if os.path.exists(papers_db):
        print(f"✅ 论文数据库存在: {papers_db}")
        try:
            from models import get_session, Paper
            session = get_session()
            count = session.query(Paper).count()
            print(f"✅ 论文数据库连接正常，当前有 {count} 篇论文")
            session.close()
        except Exception as e:
            print(f"❌ 论文数据库连接失败: {e}")
            return False
    else:
        print(f"⚠️  论文数据库不存在: {papers_db}（首次运行会创建）")
    
    # 检查新闻数据库
    try:
        from news_models import get_news_session, News, init_news_db
        init_news_db()
        session = get_news_session()
        count = session.query(News).count()
        print(f"✅ 新闻数据库连接正常，当前有 {count} 条新闻")
        session.close()
    except Exception as e:
        print(f"⚠️  新闻数据库检查失败: {e}")
    
    return True

def check_modules():
    """检查功能模块"""
    print("\n" + "=" * 60)
    print("4. 检查功能模块")
    print("=" * 60)
    
    # 检查论文抓取模块
    try:
        from daily_arxiv import demo, load_config
        print("✅ 论文抓取模块 (daily_arxiv)")
    except ImportError as e:
        print(f"❌ 论文抓取模块导入失败: {e}")
        return False
    
    # 检查新闻抓取模块
    try:
        from fetch_news import fetch_and_save_news
        print("✅ 新闻抓取模块 (fetch_news)")
    except ImportError as e:
        print(f"❌ 新闻抓取模块导入失败: {e}")
        return False
    
    # 检查招聘抓取模块
    try:
        from fetch_jobs import fetch_and_save_jobs
        print("✅ 招聘抓取模块 (fetch_jobs)")
    except ImportError as e:
        print(f"⚠️  招聘抓取模块导入失败: {e}（可选）")
    
    return True

def test_paper_fetch():
    """测试论文抓取（小规模）"""
    print("\n" + "=" * 60)
    print("5. 测试论文抓取（小规模测试）")
    print("=" * 60)
    
    try:
        from daily_arxiv import load_config, demo
        
        config = load_config('config.yaml')
        config['max_results'] = 5  # 只抓取5篇，快速测试
        config['update_paper_links'] = False
        config['enable_dedup'] = True
        config['enable_incremental'] = True
        config['days_back'] = 7
        config['fetch_semantic_scholar'] = False  # 禁用Semantic Scholar，加快测试
        
        print("开始测试抓取（只抓取5篇论文）...")
        demo(**config)
        print("✅ 论文抓取测试成功")
        return True
    except Exception as e:
        print(f"❌ 论文抓取测试失败: {e}")
        traceback.print_exc()
        return False

def test_news_fetch():
    """测试新闻抓取"""
    print("\n" + "=" * 60)
    print("6. 测试新闻抓取")
    print("=" * 60)
    
    try:
        from fetch_news import fetch_and_save_news
        
        print("开始测试新闻抓取...")
        fetch_and_save_news()
        print("✅ 新闻抓取测试成功")
        return True
    except Exception as e:
        print(f"❌ 新闻抓取测试失败: {e}")
        traceback.print_exc()
        return False

def check_network():
    """检查网络连接"""
    print("\n" + "=" * 60)
    print("7. 检查网络连接")
    print("=" * 60)
    
    import urllib.request
    
    test_urls = [
        ('ArXiv', 'https://arxiv.org/list/cs.RO/recent'),
        ('Google', 'https://www.google.com'),
    ]
    
    all_ok = True
    for name, url in test_urls:
        try:
            urllib.request.urlopen(url, timeout=5)
            print(f"✅ {name} 连接正常")
        except Exception as e:
            print(f"❌ {name} 连接失败: {e}")
            all_ok = False
    
    return all_ok

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("刷新功能诊断工具")
    print("=" * 60)
    print()
    
    results = []
    
    # 1. 检查配置文件
    results.append(("配置文件", check_config_file()))
    
    # 2. 检查依赖
    results.append(("Python依赖", check_dependencies()))
    
    # 3. 检查数据库
    results.append(("数据库", check_database()))
    
    # 4. 检查模块
    results.append(("功能模块", check_modules()))
    
    # 5. 检查网络
    results.append(("网络连接", check_network()))
    
    # 6. 测试抓取（可选，需要用户确认）
    print("\n" + "=" * 60)
    print("测试抓取功能（可选）")
    print("=" * 60)
    print("是否执行实际抓取测试？这可能需要几分钟时间。")
    print("输入 y 继续，其他键跳过...")
    
    if sys.stdin.isatty():
        try:
            response = input().strip().lower()
            if response == 'y':
                results.append(("论文抓取测试", test_paper_fetch()))
                results.append(("新闻抓取测试", test_news_fetch()))
        except KeyboardInterrupt:
            print("\n跳过测试...")
    
    # 总结
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有检查通过！刷新功能应该可以正常工作。")
        print("\n如果仍然无法刷新，请：")
        print("1. 查看浏览器控制台（F12）")
        print("2. 查看服务器日志")
        print("3. 检查 /api/refresh-status 接口返回的状态")
    else:
        print("❌ 发现问题，请根据上述检查结果修复。")
        print("\n常见解决方案：")
        print("1. 缺少依赖：pip install -r requirements.txt")
        print("2. 配置文件问题：检查 config.yaml 是否存在且格式正确")
        print("3. 数据库问题：检查数据库文件权限")
        print("4. 网络问题：检查网络连接和防火墙设置")
    print("=" * 60)

if __name__ == '__main__':
    main()
