#!/usr/bin/env python3
"""
直接测试API函数，看实际返回什么
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from bilibili_models import get_bilibili_session, BilibiliUp
from bilibili_client import format_number

# 创建测试应用
app = Flask(__name__)

# 导入app模块
import app as app_module

def test_api_directly():
    """直接测试API函数"""
    print("=" * 60)
    print("直接测试 /api/bilibili/all API函数")
    print("=" * 60)
    
    # 创建测试请求上下文
    with app.test_request_context('/api/bilibili/all?force=1'):
        try:
            # 调用实际的API函数
            response = app_module.get_all_bilibili()
            data = response.get_json()
            
            if data and 'data' in data and len(data['data']) > 0:
                print(f"\n✅ API返回了 {len(data['data'])} 个UP主\n")
                
                # 检查前3个UP主
                for i, card in enumerate(data['data'][:3], 1):
                    up_name = card.get('user_info', {}).get('name', 'Unknown')
                    user_stat = card.get('user_stat', {})
                    
                    print(f"{i}. {up_name}:")
                    print(f"   user_stat: {user_stat}")
                    
                    if user_stat.get('videos') == '0' and user_stat.get('views') == '0':
                        print(f"   ⚠️  返回了0，检查数据库...")
                        
                        # 检查数据库
                        session = get_bilibili_session()
                        up = session.query(BilibiliUp).filter_by(name=up_name).first()
                        if up:
                            print(f"   数据库: videos_count={up.videos_count}, views_count={up.views_count}, views_formatted={up.views_formatted!r}")
                            
                            # 模拟API逻辑
                            videos = format_number(up.videos_count) if up.videos_count else '0'
                            views = up.views_formatted or (format_number(up.views_count) if up.views_count else '0')
                            print(f"   应该返回: videos={videos}, views={views}")
                        session.close()
                    print()
            else:
                print("❌ API返回数据为空")
                
        except Exception as e:
            print(f"❌ 调用API失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_api_directly()

