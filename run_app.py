#!/usr/bin/env python3
"""
Flask应用启动脚本
确保从正确的目录运行应用
"""
import os
import sys

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 切换到脚本所在目录
os.chdir(SCRIPT_DIR)

# 将当前目录添加到Python路径
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# 打印调试信息
print("=" * 60)
print("Flask应用启动")
print("=" * 60)
print(f"工作目录: {os.getcwd()}")
print(f"脚本目录: {SCRIPT_DIR}")
print(f"模板目录: {os.path.join(SCRIPT_DIR, 'templates')}")
print(f"模板存在: {os.path.exists(os.path.join(SCRIPT_DIR, 'templates', 'index.html'))}")
print("=" * 60)
print()

# 导入并运行应用
from app import app

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    print(f"服务器运行在: http://localhost:{port}")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=False)

