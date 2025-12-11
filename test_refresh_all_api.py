#!/usr/bin/env python3
"""
测试刷新所有数据API - 验证论文、招聘、新闻三个任务是否都启动
"""
import requests
import time
import json

BASE_URL = "http://localhost:5001"

def test_refresh_all():
    """测试刷新所有数据API"""
    print("=" * 60)
    print("测试刷新所有数据API")
    print("=" * 60)
    
    # 1. 检查服务器是否运行
    print("\n1. 检查服务器状态...")
    try:
        response = requests.get(f"{BASE_URL}/api/stats", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
        else:
            print(f"⚠️  服务器响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 服务器未运行，请先启动服务器")
        return False
    except Exception as e:
        print(f"❌ 检查服务器状态失败: {e}")
        return False
    
    # 2. 触发刷新
    print("\n2. 触发刷新任务...")
    try:
        response = requests.post(f"{BASE_URL}/api/refresh-all", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ 刷新任务已启动")
            print(f"   响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 检查初始状态
            status = data.get('status', {})
            print(f"\n   初始状态:")
            print(f"   - 论文: {status.get('papers', {}).get('status', 'unknown')}")
            print(f"   - 招聘: {status.get('jobs', {}).get('status', 'unknown')}")
            print(f"   - 新闻: {status.get('news', {}).get('status', 'unknown')}")
            print(f"   - 运行中: {status.get('running', False)}")
        else:
            print(f"❌ 刷新任务启动失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 触发刷新失败: {e}")
        return False
    
    # 3. 轮询刷新状态（最多等待60秒）
    print("\n3. 监控刷新状态（最多等待60秒）...")
    max_wait = 60
    start_time = time.time()
    last_status = {}
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{BASE_URL}/api/refresh-status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                
                # 检查状态是否有变化
                if status != last_status:
                    papers_status = status.get('papers', {}).get('status', 'unknown')
                    jobs_status = status.get('jobs', {}).get('status', 'unknown')
                    news_status = status.get('news', {}).get('status', 'unknown')
                    running = status.get('running', False)
                    
                    print(f"   状态: 运行中={running}, 论文={papers_status}, 招聘={jobs_status}, 新闻={news_status}")
                    last_status = status
                
                if not running:
                    print("\n✅ 刷新任务完成！")
                    print(f"   最终状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
                    
                    # 检查每个任务的状态
                    papers_status = status.get('papers', {}).get('status', 'unknown')
                    jobs_status = status.get('jobs', {}).get('status', 'unknown')
                    news_status = status.get('news', {}).get('status', 'unknown')
                    
                    print(f"\n   任务完成情况:")
                    print(f"   - 论文: {papers_status} ({status.get('papers', {}).get('message', '')})")
                    print(f"   - 招聘: {jobs_status} ({status.get('jobs', {}).get('message', '')})")
                    print(f"   - 新闻: {news_status} ({status.get('news', {}).get('message', '')})")
                    
                    # 检查是否有错误
                    errors = []
                    if papers_status == 'error':
                        errors.append(f"论文: {status.get('papers', {}).get('message', '未知错误')}")
                    if jobs_status == 'error':
                        errors.append(f"招聘: {status.get('jobs', {}).get('message', '未知错误')}")
                    if news_status == 'error':
                        errors.append(f"新闻: {status.get('news', {}).get('message', '未知错误')}")
                    
                    if errors:
                        print(f"\n   ⚠️  发现错误:")
                        for error in errors:
                            print(f"   - {error}")
                        return False
                    else:
                        print(f"\n   ✅ 所有任务都成功完成！")
                        return True
            else:
                print(f"⚠️  获取状态失败: {response.status_code}")
            
            time.sleep(2)
        except Exception as e:
            print(f"⚠️  获取状态异常: {e}")
            time.sleep(2)
    
    print(f"\n⚠️  等待超时（{max_wait}秒），刷新可能仍在进行中")
    return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("刷新所有数据API测试")
    print("=" * 60)
    
    success = test_refresh_all()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试完成！所有任务（论文、招聘、新闻）都正常启动和执行")
    else:
        print("❌ 测试未完全通过，请检查错误信息")
    print("=" * 60 + "\n")
    
    return 0 if success else 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
