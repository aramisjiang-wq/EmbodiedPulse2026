#!/usr/bin/env python3
"""
测试管理后台API的完整流程
模拟实际API调用
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except:
    pass

# 导入Flask应用
from app import app
from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo

def test_admin_videos_api():
    """测试管理后台视频列表API"""
    print("=" * 60)
    print("测试管理后台视频列表API")
    print("=" * 60)
    
    with app.test_client() as client:
        # 测试不同的查询参数
        test_cases = [
            ("基本查询", "/api/admin/bilibili/videos?page=1&per_page=20"),
            ("带搜索", "/api/admin/bilibili/videos?page=1&per_page=20&search=机器人"),
            ("按UP主筛选", "/api/admin/bilibili/videos?page=1&per_page=20&uid=1172054289"),
        ]
        
        for name, url in test_cases:
            print(f"\n测试: {name}")
            print(f"URL: {url}")
            
            try:
                # 注意：这里需要认证token，但我们先测试未认证的情况
                response = client.get(url)
                print(f"状态码: {response.status_code}")
                
                if response.status_code == 401:
                    print("   ⚠️  需要认证（这是正常的）")
                elif response.status_code == 200:
                    data = response.get_json()
                    if data and data.get('success'):
                        videos = data.get('videos', [])
                        pagination = data.get('pagination', {})
                        print(f"   ✅ 成功获取 {len(videos)} 个视频")
                        print(f"   总记录数: {pagination.get('total', 0)}")
                        if videos:
                            print(f"   第一个视频: {videos[0].get('title', '')[:40]}...")
                    else:
                        print(f"   ❌ API返回失败: {data.get('message', '未知错误')}")
                else:
                    print(f"   ❌ HTTP错误: {response.status_code}")
                    try:
                        error_text = response.data.decode('utf-8')
                        print(f"   错误信息: {error_text[:200]}")
                    except:
                        pass
                        
            except Exception as e:
                print(f"   ❌ 请求失败: {e}")
                import traceback
                traceback.print_exc()

def test_admin_videos_query_direct():
    """直接测试查询逻辑（不通过API）"""
    print("\n" + "=" * 60)
    print("直接测试查询逻辑（模拟API内部逻辑）")
    print("=" * 60)
    
    session = get_bilibili_session()
    
    try:
        # 模拟API逻辑
        page = 1
        per_page = 20
        search = ''
        uid = None
        date_from = ''
        date_to = ''
        min_play = None
        
        # 构建查询（关联UP主表）
        query = session.query(BilibiliVideo, BilibiliUp).join(
            BilibiliUp, BilibiliVideo.uid == BilibiliUp.uid
        )
        
        # 搜索过滤
        if search:
            query = query.filter(
                BilibiliVideo.title.contains(search)
            )
        
        # UP主过滤
        if uid:
            query = query.filter(BilibiliVideo.uid == uid)
        
        # 日期范围过滤
        if date_from:
            try:
                from datetime import datetime as dt
                date_from_obj = dt.strptime(date_from, '%Y-%m-%d')
                query = query.filter(BilibiliVideo.pubdate >= date_from_obj)
            except:
                pass
        
        if date_to:
            try:
                from datetime import datetime as dt
                date_to_obj = dt.strptime(date_to, '%Y-%m-%d')
                query = query.filter(BilibiliVideo.pubdate <= date_to_obj)
            except:
                pass
        
        # 播放量过滤
        if min_play is not None:
            query = query.filter(BilibiliVideo.play >= min_play)
        
        # 排序（按发布时间倒序）- 修复：处理NULL值
        try:
            # 先尝试使用pubdate排序
            query = query.order_by(BilibiliVideo.pubdate.desc())
        except Exception as e:
            print(f"   ⚠️  pubdate排序失败，尝试使用pubdate_raw: {e}")
            # 如果pubdate排序失败，使用pubdate_raw
            query = query.order_by(BilibiliVideo.pubdate_raw.desc())
        
        # 分页
        total = query.count()
        print(f"   总记录数: {total}")
        
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        print(f"   成功获取 {len(results)} 条记录")
        
        # 组装数据
        videos = []
        for video, up in results:
            try:
                video_dict = video.to_dict()
                video_dict['up_name'] = up.name
                videos.append(video_dict)
            except Exception as e:
                print(f"   ⚠️  处理视频 {video.bvid} 失败: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"   ✅ 成功组装 {len(videos)} 个视频数据")
        
        if videos:
            print(f"\n   示例数据（第一个视频）:")
            first = videos[0]
            print(f"      BV号: {first.get('bvid')}")
            print(f"      标题: {first.get('title', '')[:50]}...")
            print(f"      UP主: {first.get('up_name')}")
            print(f"      播放量: {first.get('play')}")
            print(f"      发布时间: {first.get('pubdate')}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

def test_potential_issues():
    """测试潜在问题"""
    print("\n" + "=" * 60)
    print("测试潜在问题")
    print("=" * 60)
    
    session = get_bilibili_session()
    
    try:
        # 问题1: 检查是否有视频的pubdate为NULL但pubdate_raw不为NULL
        print("\n1. 检查pubdate和pubdate_raw的一致性")
        videos_with_null_pubdate = session.query(BilibiliVideo).filter(
            BilibiliVideo.pubdate == None,
            BilibiliVideo.pubdate_raw != None
        ).count()
        
        if videos_with_null_pubdate > 0:
            print(f"   ⚠️  发现 {videos_with_null_pubdate} 个视频pubdate为NULL但pubdate_raw不为NULL")
            print(f"   这可能导致排序问题")
        else:
            print(f"   ✅ pubdate和pubdate_raw一致")
        
        # 问题2: 检查是否有视频的pubdate_raw为NULL
        videos_with_null_pubdate_raw = session.query(BilibiliVideo).filter(
            BilibiliVideo.pubdate_raw == None
        ).count()
        
        if videos_with_null_pubdate_raw > 0:
            print(f"   ⚠️  发现 {videos_with_null_pubdate_raw} 个视频pubdate_raw为NULL")
        else:
            print(f"   ✅ 所有视频都有pubdate_raw")
        
        # 问题3: 测试排序是否会因为NULL值失败
        print("\n2. 测试排序逻辑")
        try:
            # 测试pubdate排序
            query1 = session.query(BilibiliVideo, BilibiliUp).join(
                BilibiliUp, BilibiliVideo.uid == BilibiliUp.uid
            ).order_by(BilibiliVideo.pubdate.desc())
            
            count1 = query1.count()
            print(f"   ✅ pubdate排序成功，记录数: {count1}")
        except Exception as e:
            print(f"   ❌ pubdate排序失败: {e}")
        
        try:
            # 测试pubdate_raw排序
            query2 = session.query(BilibiliVideo, BilibiliUp).join(
                BilibiliUp, BilibiliVideo.uid == BilibiliUp.uid
            ).order_by(BilibiliVideo.pubdate_raw.desc())
            
            count2 = query2.count()
            print(f"   ✅ pubdate_raw排序成功，记录数: {count2}")
        except Exception as e:
            print(f"   ❌ pubdate_raw排序失败: {e}")
        
        # 问题4: 检查to_dict方法是否会失败
        print("\n3. 测试to_dict方法")
        try:
            video = session.query(BilibiliVideo).first()
            if video:
                video_dict = video.to_dict()
                print(f"   ✅ to_dict方法正常")
                print(f"   示例字段: bvid={video_dict.get('bvid')}, title={video_dict.get('title', '')[:30]}...")
            else:
                print(f"   ⚠️  没有视频数据")
        except Exception as e:
            print(f"   ❌ to_dict方法失败: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    # 测试1: API端点（需要认证，会返回401）
    test_admin_videos_api()
    
    # 测试2: 直接测试查询逻辑
    test_admin_videos_query_direct()
    
    # 测试3: 潜在问题
    test_potential_issues()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

