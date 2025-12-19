#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试B站API端点，检查错误
"""

import sys
import os
sys.path.insert(0, '/srv/EmbodiedPulse2026')

print("=" * 80)
print("B站API端点错误检查")
print("=" * 80)
print()

try:
    print("【1. 导入应用】")
    print("-" * 80)
    from app import app
    print("✅ 应用导入成功")
    print()
except Exception as e:
    print(f"❌ 应用导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("【2. 测试 /api/bilibili/all 端点】")
    print("-" * 80)
    with app.test_client() as client:
        print("发送请求: GET /api/bilibili/all?force=1")
        response = client.get('/api/bilibili/all?force=1')
        
        print(f"状态码: {response.status_code}")
        print(f"Content-Type: {response.content_type}")
        print()
        
        if response.status_code == 200:
            try:
                data = response.get_json()
                if data:
                    if data.get('success'):
                        print("✅ API返回成功")
                        cards = data.get('data', [])
                        print(f"   数据条数: {len(cards)}")
                        
                        if cards:
                            print(f"\n   第一条数据示例:")
                            first_card = cards[0]
                            print(f"   UP主: {first_card.get('user_info', {}).get('name', 'N/A')}")
                            print(f"   视频数: {len(first_card.get('videos', []))}")
                        else:
                            print("   ⚠️  数据为空")
                    else:
                        print(f"❌ API返回失败")
                        print(f"   错误信息: {data.get('error', '未知错误')}")
                        print(f"   完整响应: {data}")
                else:
                    print("❌ 响应不是JSON格式")
                    print(f"   响应内容: {response.data.decode('utf-8')[:500]}")
            except Exception as e:
                print(f"❌ 解析响应失败: {e}")
                print(f"   原始响应: {response.data.decode('utf-8')[:500]}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            try:
                error_text = response.data.decode('utf-8')
                print(f"   错误内容: {error_text[:1000]}")
            except:
                print(f"   响应数据: {response.data[:1000]}")
    print()
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    print()

try:
    print("【3. 检查数据库连接】")
    print("-" * 80)
    from bilibili_models import BILIBILI_DATABASE_URL, get_bilibili_session, BilibiliUp, BilibiliVideo
    
    print(f"数据库URL: {BILIBILI_DATABASE_URL}")
    
    session = get_bilibili_session()
    try:
        up_count = session.query(BilibiliUp).count()
        video_count = session.query(BilibiliVideo).count()
        print(f"✅ 数据库连接成功")
        print(f"   UP主数量: {up_count}")
        print(f"   视频数量: {video_count}")
        
        if video_count > 0:
            # 检查最新视频
            latest_video = session.query(BilibiliVideo).order_by(BilibiliVideo.pubdate.desc()).first()
            if latest_video:
                print(f"\n   最新视频:")
                print(f"   BV号: {latest_video.bvid}")
                print(f"   标题: {latest_video.title[:50]}...")
                print(f"   播放量: {latest_video.play:,}")
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
    print()
except Exception as e:
    print(f"❌ 数据库检查失败: {e}")
    import traceback
    traceback.print_exc()
    print()

print("=" * 80)
print("检查完成")
print("=" * 80)

