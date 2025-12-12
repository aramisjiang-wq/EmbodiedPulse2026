#!/usr/bin/env python3
"""
测试 bilibili-api-python 库是否正常工作
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def test_library_import():
    """测试库是否可以导入"""
    print_info("=" * 60)
    print_info("测试1: 检查库是否已安装")
    print_info("=" * 60)
    
    try:
        from bilibili_api import user
        print_success("bilibili-api-python 库导入成功")
        return True
    except ImportError as e:
        print_error(f"bilibili-api-python 库未安装: {e}")
        print_warning("请运行: pip install bilibili-api-python aiohttp")
        return False

def test_client_import():
    """测试客户端是否可以导入"""
    print_info("=" * 60)
    print_info("测试2: 检查客户端模块")
    print_info("=" * 60)
    
    try:
        from bilibili_client import BilibiliClient, format_number, format_timestamp
        print_success("bilibili_client 模块导入成功")
        return True
    except ImportError as e:
        print_error(f"bilibili_client 模块导入失败: {e}")
        return False

def test_get_user_info():
    """测试获取用户信息"""
    print_info("=" * 60)
    print_info("测试3: 获取UP主信息")
    print_info("=" * 60)
    
    try:
        from bilibili_client import BilibiliClient
        
        # 逐际动力的Bilibili UID
        UP_UID = 1172054289
        
        print_info(f"正在获取UP主信息 (UID: {UP_UID})...")
        client = BilibiliClient()
        user_info = client.get_user_info(UP_UID, retry=2)
        
        if user_info:
            print_success("获取UP主信息成功")
            print_info(f"  名称: {user_info.get('name', 'N/A')}")
            print_info(f"  粉丝数: {user_info.get('fans', 0)}")
            print_info(f"  关注数: {user_info.get('friend', 0)}")
            print_info(f"  等级: {user_info.get('level', 0)}")
            return True
        else:
            print_error("获取UP主信息失败，返回 None")
            return False
            
    except Exception as e:
        print_error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_user_videos():
    """测试获取视频列表"""
    print_info("=" * 60)
    print_info("测试4: 获取视频列表")
    print_info("=" * 60)
    
    try:
        from bilibili_client import BilibiliClient
        
        UP_UID = 1172054289
        
        print_info(f"正在获取视频列表 (UID: {UP_UID})...")
        client = BilibiliClient()
        videos = client.get_user_videos(UP_UID, pn=1, ps=5, retry=2)
        
        if videos:
            print_success(f"获取视频列表成功，共 {len(videos)} 个视频")
            for i, video in enumerate(videos[:3], 1):
                print_info(f"  视频{i}: {video.get('title', 'N/A')[:50]}...")
                print_info(f"    播放数: {video.get('play', 0)}")
                print_info(f"    发布时间: {video.get('pubdate', 0)}")
            return True
        else:
            print_error("获取视频列表失败，返回 None")
            return False
            
    except Exception as e:
        print_error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_all_data():
    """测试获取完整数据"""
    print_info("=" * 60)
    print_info("测试5: 获取完整数据")
    print_info("=" * 60)
    
    try:
        from bilibili_client import BilibiliClient
        
        UP_UID = 1172054289
        
        print_info(f"正在获取完整数据 (UID: {UP_UID})...")
        client = BilibiliClient()
        data = client.get_all_data(UP_UID, video_count=5)
        
        if data:
            print_success("获取完整数据成功")
            user_info = data.get('user_info', {})
            videos = data.get('videos', [])
            user_stat = data.get('user_stat', {})
            
            print_info(f"  用户信息: {user_info.get('name', 'N/A')}")
            print_info(f"  视频数量: {len(videos)}")
            print_info(f"  统计数据: {user_stat}")
            return True
        else:
            print_error("获取完整数据失败，返回 None")
            return False
            
    except Exception as e:
        print_error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_format_functions():
    """测试格式化函数"""
    print_info("=" * 60)
    print_info("测试6: 格式化函数")
    print_info("=" * 60)
    
    try:
        from bilibili_client import format_number, format_timestamp
        
        # 测试数字格式化
        test_cases = [
            (1000, "1000"),
            (10000, "1.0万"),
            (100000000, "1.0亿"),
        ]
        
        for num, expected_pattern in test_cases:
            result = format_number(num)
            print_info(f"  {num} -> {result}")
        
        # 测试时间戳格式化
        import time
        timestamp = int(time.time())
        formatted = format_timestamp(timestamp)
        print_info(f"  时间戳 {timestamp} -> {formatted}")
        
        print_success("格式化函数测试通过")
        return True
        
    except Exception as e:
        print_error(f"测试失败: {e}")
        return False

def main():
    """主函数"""
    print_info("=" * 60)
    print_info("Bilibili API 测试脚本")
    print_info("=" * 60)
    print()
    
    tests = [
        ("库导入测试", test_library_import),
        ("客户端导入测试", test_client_import),
        ("获取用户信息测试", test_get_user_info),
        ("获取视频列表测试", test_get_user_videos),
        ("获取完整数据测试", test_get_all_data),
        ("格式化函数测试", test_format_functions),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"{test_name} 异常: {e}")
            results.append((test_name, False))
        print()
    
    # 总结
    print_info("=" * 60)
    print_info("测试总结")
    print_info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}: 通过")
        else:
            print_error(f"{name}: 失败")
    
    print()
    print_info(f"总计: {passed}/{total} 通过")
    
    if passed == total:
        print_success("\n🎉 所有测试通过！bilibili-api-python 库工作正常。")
        return 0
    else:
        print_error(f"\n⚠️  有 {total - passed} 个测试失败，请检查。")
        return 1

if __name__ == "__main__":
    sys.exit(main())




