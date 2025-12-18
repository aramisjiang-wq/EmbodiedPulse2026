#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清除Bilibili API缓存
用于强制刷新数据
"""

import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 这个脚本需要在Flask应用上下文中运行
# 或者直接修改内存中的缓存（如果Flask应用正在运行）

print("=" * 60)
print("清除Bilibili API缓存")
print("=" * 60)
print("\n⚠️  注意：此脚本需要重启Flask服务才能清除内存缓存")
print("   或者访问 API 时使用 ?force=1 参数强制刷新")
print("\n建议操作：")
print("1. 重启Flask服务：sudo systemctl restart embodiedpulse")
print("2. 或者在浏览器访问：https://blibli.gradmotion.com/bilibili?force=1")
print("=" * 60)

