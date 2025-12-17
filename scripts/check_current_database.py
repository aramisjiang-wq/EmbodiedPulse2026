#!/usr/bin/env python3
"""
检查当前使用的数据库类型和配置
"""
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

print("=" * 60)
print("当前数据库配置检查")
print("=" * 60)
print()

# 1. 检查具身论文数据库
papers_db_url = os.getenv('DATABASE_URL', 'sqlite:///./papers.db')
print("📚 具身论文数据库:")
print(f"   DATABASE_URL: {papers_db_url}")

if papers_db_url.startswith('postgresql://') or papers_db_url.startswith('postgres://'):
    print("   ✅ 使用: PostgreSQL")
    # 解析PostgreSQL连接信息
    try:
        # 隐藏密码
        if '@' in papers_db_url:
            parts = papers_db_url.split('@')
            user_pass = parts[0].split('//')[1] if '//' in parts[0] else ''
            if ':' in user_pass:
                user = user_pass.split(':')[0]
                print(f"   用户: {user}")
            print(f"   主机: {parts[1].split('/')[0]}")
            db_name = parts[1].split('/')[-1].split('?')[0]
            print(f"   数据库: {db_name}")
    except:
        pass
else:
    print("   ✅ 使用: SQLite")
    db_file = papers_db_url.replace('sqlite:///', '').replace('sqlite:///', '')
    if os.path.exists(db_file):
        size = os.path.getsize(db_file) / (1024 * 1024)  # MB
        print(f"   文件: {db_file}")
        print(f"   大小: {size:.2f} MB")
    else:
        print(f"   ⚠️  文件不存在: {db_file}")

print()

# 2. 检查具身视频数据库
bilibili_db_url = os.getenv('BILIBILI_DATABASE_URL', 'sqlite:///./bilibili.db')
print("📹 具身视频数据库:")
print(f"   BILIBILI_DATABASE_URL: {bilibili_db_url}")

if bilibili_db_url.startswith('postgresql://') or bilibili_db_url.startswith('postgres://'):
    print("   ✅ 使用: PostgreSQL")
    # 解析PostgreSQL连接信息
    try:
        # 隐藏密码
        if '@' in bilibili_db_url:
            parts = bilibili_db_url.split('@')
            user_pass = parts[0].split('//')[1] if '//' in parts[0] else ''
            if ':' in user_pass:
                user = user_pass.split(':')[0]
                print(f"   用户: {user}")
            print(f"   主机: {parts[1].split('/')[0]}")
            db_name = parts[1].split('/')[-1].split('?')[0]
            print(f"   数据库: {db_name}")
    except:
        pass
else:
    print("   ✅ 使用: SQLite")
    db_file = bilibili_db_url.replace('sqlite:///', '').replace('sqlite:///', '')
    if os.path.exists(db_file):
        size = os.path.getsize(db_file) / (1024 * 1024)  # MB
        print(f"   文件: {db_file}")
        print(f"   大小: {size:.2f} MB")
    else:
        print(f"   ⚠️  文件不存在: {db_file}")

print()

# 3. 检查数据量
print("📊 数据统计:")
try:
    from models import get_session, Paper
    session = get_session()
    papers_count = session.query(Paper).count()
    session.close()
    print(f"   论文数量: {papers_count} 篇")
except Exception as e:
    print(f"   ⚠️  无法查询论文数据: {e}")

try:
    from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
    bilibili_session = get_bilibili_session()
    ups_count = bilibili_session.query(BilibiliUp).count()
    videos_count = bilibili_session.query(BilibiliVideo).count()
    bilibili_session.close()
    print(f"   UP主数量: {ups_count} 个")
    print(f"   视频数量: {videos_count} 个")
except Exception as e:
    print(f"   ⚠️  无法查询B站数据: {e}")

print()
print("=" * 60)

