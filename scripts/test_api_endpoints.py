#!/usr/bin/env python3
"""
快速测试API端点
"""
import requests
import json
import sys

def test_api(url, name):
    """测试API端点"""
    print(f"\n{'='*60}")
    print(f"测试 {name}: {url}")
    print('='*60)
    
    try:
        response = requests.get(url, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"响应成功: {data.get('success', 'N/A')}")
                
                if 'data' in data:
                    if isinstance(data['data'], list):
                        print(f"数据数量: {len(data['data'])}")
                        if len(data['data']) > 0:
                            print(f"第一条数据: {json.dumps(data['data'][0], indent=2, ensure_ascii=False)[:200]}...")
                    elif isinstance(data['data'], dict):
                        print(f"数据键: {list(data['data'].keys())[:10]}")
                        print(f"数据类别数: {len(data['data'])}")
                
                if 'total' in data:
                    print(f"总数: {data['total']}")
                
                if 'error' in data:
                    print(f"错误: {data['error']}")
                
                return True
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                print(f"响应内容: {response.text[:500]}")
                return False
        else:
            print(f"HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时（超过10秒）")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保服务器正在运行")
        return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def main():
    """主函数"""
    base_url = "http://localhost:5001"
    
    print("开始测试API端点...")
    print(f"服务器地址: {base_url}")
    
    # 测试论文API
    papers_ok = test_api(f"{base_url}/api/papers", "论文API")
    
    # 测试B站API
    bilibili_ok = test_api(f"{base_url}/api/bilibili/all", "B站API")
    
    print(f"\n{'='*60}")
    print("测试总结:")
    print('='*60)
    print(f"论文API: {'✅ 正常' if papers_ok else '❌ 异常'}")
    print(f"B站API: {'✅ 正常' if bilibili_ok else '❌ 异常'}")
    
    if not papers_ok or not bilibili_ok:
        print("\n如果API测试失败，请检查:")
        print("  1. 服务器是否正在运行 (python3 app.py)")
        print("  2. 端口是否正确 (默认5001)")
        print("  3. 数据库是否正常")
        sys.exit(1)


if __name__ == '__main__':
    main()

