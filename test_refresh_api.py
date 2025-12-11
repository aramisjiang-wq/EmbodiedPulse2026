#!/usr/bin/env python3
"""
测试刷新API - 验证刷新功能是否正常工作
"""
import requests
import time
import json

BASE_URL = "http://localhost:5001"

def test_refresh_api():
    """测试刷新API"""
    print("=" * 60)
    print("测试刷新API功能")
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
        print("   启动命令: python3 app.py 或 ./start_web.sh")
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
        else:
            print(f"❌ 刷新任务启动失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 触发刷新失败: {e}")
        return False
    
    # 3. 轮询刷新状态
    print("\n3. 监控刷新状态（最多等待60秒）...")
    max_wait = 60
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{BASE_URL}/api/refresh-status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                running = status.get('running', False)
                
                papers_status = status.get('papers', {}).get('status', 'unknown')
                jobs_status = status.get('jobs', {}).get('status', 'unknown')
                news_status = status.get('news', {}).get('status', 'unknown')
                
                print(f"   状态: 运行中={running}, 论文={papers_status}, 招聘={jobs_status}, 新闻={news_status}")
                
                if not running:
                    print("\n✅ 刷新任务完成！")
                    print(f"   最终状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
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
    print("刷新API功能测试")
    print("=" * 60)
    
    success = test_refresh_api()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试完成！刷新功能正常工作")
    else:
        print("❌ 测试未完全通过，请检查错误信息")
    print("=" * 60 + "\n")
    
    return 0 if success else 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
