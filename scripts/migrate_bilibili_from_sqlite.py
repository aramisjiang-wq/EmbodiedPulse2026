#!/usr/bin/env python3
"""
从SQLite数据库迁移Bilibili数据到PostgreSQL
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("从SQLite迁移Bilibili数据到PostgreSQL")
print("=" * 60)
print()

# 检查SQLite数据库是否存在
sqlite_db_path = os.path.join(project_root, 'bilibili.db')
if not os.path.exists(sqlite_db_path):
    print(f"❌ SQLite数据库不存在: {sqlite_db_path}")
    print("   请确保bilibili.db文件在项目根目录")
    sys.exit(1)

print(f"✅ 找到SQLite数据库: {sqlite_db_path}")
print()

# 连接SQLite数据库
import sqlite3
sqlite_conn = sqlite3.connect(sqlite_db_path)
sqlite_cursor = sqlite_conn.cursor()

# 连接PostgreSQL数据库
from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo

bilibili_session = get_bilibili_session()

# 1. 迁移UP主数据
print("=" * 60)
print("1. 迁移UP主数据")
print("=" * 60)
print()

sqlite_cursor.execute("SELECT * FROM bilibili_ups")
ups_data = sqlite_cursor.fetchall()

# 获取列名
sqlite_cursor.execute("PRAGMA table_info(bilibili_ups)")
columns = [row[1] for row in sqlite_cursor.fetchall()]

print(f"📊 SQLite中有 {len(ups_data)} 个UP主")
print()

migrated_ups = 0
for row in ups_data:
    up_dict = dict(zip(columns, row))
    
    # 检查是否已存在
    existing = bilibili_session.query(BilibiliUp).filter_by(uid=up_dict['uid']).first()
    
    if existing:
        # 更新现有记录
        for key, value in up_dict.items():
            if hasattr(existing, key) and key != 'id':
                setattr(existing, key, value)
        existing.updated_at = datetime.now()
        print(f"  更新: {up_dict.get('name', 'Unknown')} (UID: {up_dict['uid']})")
    else:
        # 创建新记录
        new_up = BilibiliUp(**{k: v for k, v in up_dict.items() if k != 'id'})
        bilibili_session.add(new_up)
        print(f"  新增: {up_dict.get('name', 'Unknown')} (UID: {up_dict['uid']})")
    
    migrated_ups += 1

bilibili_session.commit()
print()
print(f"✅ 已迁移 {migrated_ups} 个UP主")
print()

# 2. 迁移视频数据
print("=" * 60)
print("2. 迁移视频数据")
print("=" * 60)
print()

sqlite_cursor.execute("SELECT * FROM bilibili_videos")
videos_data = sqlite_cursor.fetchall()

# 获取列名
sqlite_cursor.execute("PRAGMA table_info(bilibili_videos)")
video_columns = [row[1] for row in sqlite_cursor.fetchall()]

print(f"📊 SQLite中有 {len(videos_data)} 个视频")
print()

migrated_videos = 0
for row in videos_data:
    video_dict = dict(zip(video_columns, row))
    
    # 检查是否已存在（根据bvid和uid）
    existing = bilibili_session.query(BilibiliVideo).filter_by(
        bvid=video_dict.get('bvid'),
        uid=video_dict.get('uid')
    ).first()
    
    if existing:
        # 更新现有记录
        for key, value in video_dict.items():
            if hasattr(existing, key) and key != 'id':
                setattr(existing, key, value)
        existing.updated_at = datetime.now()
    else:
        # 创建新记录
        new_video = BilibiliVideo(**{k: v for k, v in video_dict.items() if k != 'id'})
        bilibili_session.add(new_video)
    
    migrated_videos += 1
    
    if migrated_videos % 50 == 0:
        bilibili_session.commit()
        print(f"  已迁移 {migrated_videos}/{len(videos_data)} 个视频...")

bilibili_session.commit()
print()
print(f"✅ 已迁移 {migrated_videos} 个视频")
print()

# 关闭连接
sqlite_conn.close()
bilibili_session.close()

print("=" * 60)
print("✅ 迁移完成！")
print("=" * 60)
print()
print("📝 下一步：")
print("  1. 运行 venv/bin/python3 scripts/check_bilibili_data_integrity.py 验证数据")
print("  2. 运行抓取脚本更新最新数据")

