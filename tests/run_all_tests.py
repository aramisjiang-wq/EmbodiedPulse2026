#!/usr/bin/env python3
"""
运行所有部署前验收测试
"""
import sys
import os
import subprocess
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def run_test(test_file, test_name):
    """运行单个测试文件"""
    print_header(f"运行 {test_name}")
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True,
            text=True
        )
        
        # 打印输出
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print_error(f"运行测试失败: {str(e)}")
        return False

def main():
    """主函数"""
    print_header("部署前验收测试")
    print_info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info("确保服务器已启动: python3 app.py 或 gunicorn -c gunicorn_config.py app:app")
    print()
    
    # 测试文件列表
    tests = [
        ("tests/test_api_endpoints.py", "API端点测试"),
        ("tests/test_database_connections.py", "数据库连接测试"),
        ("tests/test_functionality.py", "功能测试"),
    ]
    
    results = []
    
    for test_file, test_name in tests:
        success = run_test(test_file, test_name)
        results.append((test_name, success))
        print()
    
    # 总结
    print_header("测试总结")
    
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
        print_success("\n🎉 所有测试通过！系统已准备好部署。")
        return 0
    else:
        print_error(f"\n⚠️  有 {total - passed} 个测试失败，请修复后再部署。")
        return 1

if __name__ == "__main__":
    sys.exit(main())




