#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API返回的数据
检查逐际动力的数据是否在返回中
"""

import sys
import os
import requests
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_api_response():
    """测试API返回"""
    print("=" * 80)
    print("测试 /api/bilibili/all API 返回")
    print("=" * 80)
    
    try:
        # 测试API
        url = "http://localhost:5001/api/bilibili/all?force=1"
        print(f"\n请求URL: {url}")
        response = requests.get(url, timeout=10)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API返回错误状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            return
        
        data = response.json()
        
        print(f"\n响应结构:")
        print(f"  success: {data.get('success')}")
        print(f"  total: {data.get('total')}")
        print(f"  data类型: {type(data.get('data'))}")
        print(f"  data长度: {len(data.get('data', []))}")
        
        # 查找逐际动力
        limx_data = None
        for card in data.get('data', []):
            user_info = card.get('user_info', {})
            if user_info.get('mid') == 1172054289 or user_info.get('name') == '逐际动力':
                limx_data = card
                break
        
        if limx_data:
            print(f"\n✅ 找到逐际动力数据:")
            print(f"  名称: {limx_data.get('user_info', {}).get('name')}")
            print(f"  UID: {limx_data.get('user_info', {}).get('mid')}")
            print(f"  视频数量: {len(limx_data.get('videos', []))}")
            print(f"  总播放: {limx_data.get('user_stat', {}).get('views')}")
            print(f"  总视频: {limx_data.get('user_stat', {}).get('videos')}")
            
            if len(limx_data.get('videos', [])) == 0:
                print(f"\n⚠️  视频列表为空！")
        else:
            print(f"\n❌ 未找到逐际动力数据！")
            print(f"\n所有UP主列表:")
            for i, card in enumerate(data.get('data', []), 1):
                user_info = card.get('user_info', {})
                print(f"  {i}. {user_info.get('name')} (UID: {user_info.get('mid')})")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_api_response()

