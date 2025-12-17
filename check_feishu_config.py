#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书OAuth配置检查工具
用于验证飞书配置是否正确
"""

import os
import sys
from dotenv import load_dotenv

# 加载.env文件
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    print("❌ 错误: 找不到.env文件")
    sys.exit(1)

print("=" * 70)
print("飞书OAuth配置检查工具")
print("=" * 70)
print()

# 检查必需的环境变量
required_vars = {
    'FEISHU_APP_ID': '飞书App ID',
    'FEISHU_APP_SECRET': '飞书App Secret',
    'FEISHU_REDIRECT_URI': '回调地址',
    'JWT_SECRET_KEY': 'JWT密钥'
}

all_ok = True

print("📋 配置检查:")
print("-" * 70)

for var_name, var_desc in required_vars.items():
    value = os.getenv(var_name)
    
    if not value:
        print(f"❌ {var_desc} ({var_name}): 未配置")
        all_ok = False
    else:
        # 对于Secret，只显示前几位
        if 'SECRET' in var_name:
            display_value = value[:10] + '...' if len(value) > 10 else value
        else:
            display_value = value
        
        print(f"✅ {var_desc} ({var_name}): {display_value}")

print()
print("=" * 70)
print("📍 当前配置的回调地址:")
print("=" * 70)

redirect_uri = os.getenv('FEISHU_REDIRECT_URI', '')
if redirect_uri:
    print()
    print(f"  {redirect_uri}")
    print()
    
    # 分析回调地址
    print("🔍 回调地址分析:")
    print("-" * 70)
    
    # 检查协议
    if redirect_uri.startswith('https://'):
        print("✅ 协议: HTTPS (生产环境)")
    elif redirect_uri.startswith('http://'):
        print("✅ 协议: HTTP (本地开发)")
    else:
        print("❌ 协议: 未知或错误")
        all_ok = False
    
    # 检查域名
    if 'localhost' in redirect_uri:
        print("✅ 域名: localhost (本地开发)")
    elif '127.0.0.1' in redirect_uri:
        print("✅ 域名: 127.0.0.1 (本地开发)")
    elif redirect_uri.startswith('http://'):
        print("⚠️  域名: 其他HTTP地址（可能不被飞书接受）")
    else:
        print("✅ 域名: 公网域名")
    
    # 检查端口
    if ':5001' in redirect_uri:
        print("✅ 端口: 5001")
    elif ':80' in redirect_uri or ':443' in redirect_uri:
        print("✅ 端口: 标准端口")
    else:
        print("⚠️  端口: 未指定或非标准端口")
    
    # 检查路径
    if '/api/auth/feishu/callback' in redirect_uri:
        print("✅ 路径: /api/auth/feishu/callback")
    else:
        print("❌ 路径: 错误或缺失")
        all_ok = False

print()
print("=" * 70)
print("📝 飞书开放平台配置要求:")
print("=" * 70)
print()
print("请在飞书开放平台（https://open.feishu.cn）添加以下回调URL:")
print()
print("【方案1】 使用localhost (推荐)")
print(f"  http://localhost:5001/api/auth/feishu/callback")
print()
print("【方案2】 使用127.0.0.1")
print(f"  http://127.0.0.1:5001/api/auth/feishu/callback")
print()
print("💡 建议: 两个URL都添加到飞书开放平台，确保兼容性")
print()

print("=" * 70)
print("🔧 配置步骤:")
print("=" * 70)
print()
print("1. 访问飞书开放平台: https://open.feishu.cn")
print("2. 登录管理员账号")
print("3. 进入'应用管理' → 找到App ID: cli_a6727c4ffc71d00b")
print("4. 进入应用详情 → '安全设置' 或 '重定向URL'")
print("5. 添加上述回调URL")
print("6. 保存配置，等待1-5分钟生效")
print()

print("=" * 70)
print("🧪 测试地址:")
print("=" * 70)
print()
print("登录页面:")
print("  http://localhost:5001/login")
print("  http://127.0.0.1:5001/login")
print()

if all_ok:
    print("=" * 70)
    print("✅ 配置检查通过！")
    print("=" * 70)
    print()
    print("下一步: 在飞书开放平台添加回调URL后，访问登录页面测试")
    print()
else:
    print("=" * 70)
    print("❌ 配置检查失败，请修复上述问题")
    print("=" * 70)
    print()

print("📖 详细配置指南: 查看 飞书OAuth配置指南.md")
print()

