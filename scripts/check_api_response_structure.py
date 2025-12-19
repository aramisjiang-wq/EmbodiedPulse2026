#!/usr/bin/env python3
"""
检查API实际返回的数据结构
"""
import sys
import os
import json
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_api_response():
    """检查API实际返回的数据结构"""
    print("=" * 60)
    print("检查API实际返回的数据结构")
    print("=" * 60)
    
    # 调用API
    try:
        import urllib.request
        url = 'http://localhost:5001/api/bilibili/all?force=1'
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if data.get('success') and data.get('data') and len(data['data']) > 0:
                first_card = data['data'][0]
                
                print(f"\n第一个UP主: {first_card.get('user_info', {}).get('name', 'Unknown')}")
                print(f"\n完整数据结构:")
                print(json.dumps(first_card, indent=2, ensure_ascii=False))
                
                print("\n" + "="*60)
                print("关键字段检查:")
                print("="*60)
                
                user_info = first_card.get('user_info', {})
                user_stat = first_card.get('user_stat', {})
                
                print(f"\nuser_info:")
                for key, value in user_info.items():
                    print(f"  {key}: {value!r}")
                
                print(f"\nuser_stat:")
                for key, value in user_stat.items():
                    print(f"  {key}: {value!r}")
                
                print(f"\n前端期望的字段:")
                print(f"  userStat.views = {user_stat.get('views', 'NOT_FOUND')!r}")
                print(f"  userStat.videos = {user_stat.get('videos', 'NOT_FOUND')!r}")
                
            else:
                print("❌ API返回数据为空或格式错误")
                print(f"success: {data.get('success')}")
                print(f"data length: {len(data.get('data', []))}")
                
    except Exception as e:
        print(f"❌ 调用API失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_api_response()

