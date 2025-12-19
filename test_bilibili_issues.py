#!/usr/bin/env python3
"""
B站数据问题诊断脚本
测试代码逻辑和数据库问题
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

from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from sqlalchemy import func, and_, or_

def print_section(title):
    print("\n" + "=" * 60)
    print(f"【{title}】")
    print("=" * 60)

def test_database_connection():
    """测试数据库连接"""
    print_section("1. 测试数据库连接")
    try:
        session = get_bilibili_session()
        print("✅ 数据库连接成功")
        
        # 测试基本查询
        up_count = session.query(BilibiliUp).count()
        video_count = session.query(BilibiliVideo).count()
        print(f"   UP主总数: {up_count}")
        print(f"   视频总数: {video_count}")
        
        session.close()
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_integrity():
    """测试数据完整性"""
    print_section("2. 测试数据完整性")
    session = get_bilibili_session()
    
    try:
        # 检查是否有孤立视频（视频的uid在UP主表中不存在）
        all_video_uids = session.query(BilibiliVideo.uid).distinct().all()
        all_video_uids = [uid[0] for uid in all_video_uids]
        
        all_up_uids = session.query(BilibiliUp.uid).all()
        all_up_uids = [uid[0] for uid in all_up_uids]
        
        orphan_videos = set(all_video_uids) - set(all_up_uids)
        
        if orphan_videos:
            print(f"⚠️  发现 {len(orphan_videos)} 个孤立视频（UP主不存在）")
            print(f"   孤立的UID: {list(orphan_videos)[:10]}")
            
            # 统计孤立视频数量
            for uid in list(orphan_videos)[:5]:
                count = session.query(BilibiliVideo).filter_by(uid=uid).count()
                print(f"     UID {uid}: {count} 个视频")
        else:
            print("✅ 没有发现孤立视频")
        
        # 检查NULL值
        null_pubdate_count = session.query(BilibiliVideo).filter(
            BilibiliVideo.pubdate == None
        ).count()
        
        null_pubdate_raw_count = session.query(BilibiliVideo).filter(
            BilibiliVideo.pubdate_raw == None
        ).count()
        
        if null_pubdate_count > 0:
            print(f"⚠️  发现 {null_pubdate_count} 个视频的 pubdate 为 NULL")
        if null_pubdate_raw_count > 0:
            print(f"⚠️  发现 {null_pubdate_raw_count} 个视频的 pubdate_raw 为 NULL")
        
        if null_pubdate_count == 0 and null_pubdate_raw_count == 0:
            print("✅ 所有视频都有有效的发布时间")
        
        return len(orphan_videos) == 0
        
    except Exception as e:
        print(f"❌ 数据完整性检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

def test_admin_videos_query():
    """测试管理后台视频列表查询（模拟API逻辑）"""
    print_section("3. 测试管理后台视频列表查询")
    session = get_bilibili_session()
    
    try:
        # 模拟原始查询（使用INNER JOIN）
        print("\n测试1: 使用INNER JOIN查询（原始代码）")
        try:
            query = session.query(BilibiliVideo, BilibiliUp).join(
                BilibiliUp, BilibiliVideo.uid == BilibiliUp.uid
            )
            
            # 排序（按发布时间倒序）
            query = query.order_by(BilibiliVideo.pubdate.desc())
            
            # 测试分页
            total = query.count()
            print(f"   ✅ INNER JOIN查询成功")
            print(f"   总记录数: {total}")
            
            # 尝试获取第一页
            results = query.limit(10).all()
            print(f"   成功获取前10条记录")
            
            # 检查是否有NULL pubdate导致排序问题
            null_pubdate_in_results = any(video.pubdate is None for video, up in results)
            if null_pubdate_in_results:
                print(f"   ⚠️  结果中包含 pubdate 为 NULL 的视频")
            
        except Exception as e:
            print(f"   ❌ INNER JOIN查询失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 测试LEFT JOIN查询（修复方案）
        print("\n测试2: 使用LEFT JOIN查询（修复方案）")
        try:
            from sqlalchemy import outerjoin
            query_left = session.query(BilibiliVideo, BilibiliUp).outerjoin(
                BilibiliUp, BilibiliVideo.uid == BilibiliUp.uid
            )
            
            # 处理NULL pubdate的排序
            query_left = query_left.order_by(
                BilibiliVideo.pubdate.desc().nullslast()
            )
            
            total_left = query_left.count()
            print(f"   ✅ LEFT JOIN查询成功")
            print(f"   总记录数: {total_left}")
            
            if total_left > total:
                print(f"   ⚠️  LEFT JOIN返回更多记录（包含孤立视频）")
            
        except Exception as e:
            print(f"   ❌ LEFT JOIN查询失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试处理NULL值的排序
        print("\n测试3: 测试NULL值排序处理")
        try:
            # 使用pubdate_raw排序（更安全）
            query_safe = session.query(BilibiliVideo, BilibiliUp).join(
                BilibiliUp, BilibiliVideo.uid == BilibiliUp.uid
            ).order_by(
                BilibiliVideo.pubdate_raw.desc().nullslast()
            )
            
            total_safe = query_safe.count()
            print(f"   ✅ 使用pubdate_raw排序成功")
            print(f"   总记录数: {total_safe}")
            
        except Exception as e:
            print(f"   ❌ 安全排序查询失败: {e}")
            import traceback
            traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

def test_api_bilibili_all():
    """测试 /api/bilibili/all API逻辑"""
    print_section("4. 测试 /api/bilibili/all API逻辑")
    session = get_bilibili_session()
    
    try:
        # 模拟API逻辑
        ups = session.query(BilibiliUp).filter_by(is_active=True).all()
        print(f"   活跃UP主数量: {len(ups)}")
        
        if not ups:
            print("   ⚠️  没有活跃的UP主")
            return False
        
        all_data = []
        for up in ups[:3]:  # 只测试前3个
            try:
                # 获取视频
                videos_query = session.query(BilibiliVideo).filter_by(
                    uid=up.uid,
                    is_deleted=False
                ).order_by(BilibiliVideo.pubdate_raw.desc()).limit(10)
                
                videos = videos_query.all()
                print(f"   UP主 {up.name} (UID: {up.uid}): {len(videos)} 个视频")
                
                # 测试to_dict方法
                if videos:
                    video_dict = videos[0].to_dict()
                    print(f"      第一个视频: {video_dict.get('title', '')[:30]}...")
                
            except Exception as e:
                print(f"   ❌ 处理UP主 {up.name} 失败: {e}")
                import traceback
                traceback.print_exc()
        
        print("   ✅ API逻辑测试通过")
        return True
        
    except Exception as e:
        print(f"❌ API逻辑测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

def test_data_freshness():
    """测试数据新鲜度"""
    print_section("5. 测试数据新鲜度")
    session = get_bilibili_session()
    
    try:
        ups = session.query(BilibiliUp).filter_by(is_active=True).all()
        
        if not ups:
            print("   ⚠️  没有活跃的UP主")
            return False
        
        now = datetime.now()
        stale_count = 0
        
        print("\n   UP主数据更新情况:")
        for up in ups[:10]:
            if up.last_fetch_at:
                age_hours = (now - up.last_fetch_at).total_seconds() / 3600
                status = "✅" if age_hours < 24 else "⚠️" if age_hours < 168 else "❌"
                print(f"   {status} {up.name}: {age_hours:.1f} 小时前更新")
                
                if age_hours > 24:
                    stale_count += 1
            else:
                print(f"   ❌ {up.name}: 从未更新")
                stale_count += 1
        
        if stale_count == 0:
            print("\n   ✅ 所有UP主数据都是最新的（24小时内）")
        else:
            print(f"\n   ⚠️  有 {stale_count} 个UP主数据需要更新")
        
        return stale_count == 0
        
    except Exception as e:
        print(f"❌ 数据新鲜度检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

def main():
    print("=" * 60)
    print("B站数据问题诊断脚本")
    print("=" * 60)
    
    results = []
    
    # 1. 测试数据库连接
    results.append(("数据库连接", test_database_connection()))
    
    # 2. 测试数据完整性
    results.append(("数据完整性", test_data_integrity()))
    
    # 3. 测试管理后台查询
    results.append(("管理后台查询", test_admin_videos_query()))
    
    # 4. 测试API逻辑
    results.append(("API逻辑", test_api_bilibili_all()))
    
    # 5. 测试数据新鲜度
    results.append(("数据新鲜度", test_data_freshness()))
    
    # 汇总结果
    print_section("测试结果汇总")
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")
    
    failed_tests = [name for name, result in results if not result]
    if failed_tests:
        print(f"\n⚠️  有 {len(failed_tests)} 个测试失败: {', '.join(failed_tests)}")
    else:
        print("\n✅ 所有测试通过")

if __name__ == '__main__':
    main()

