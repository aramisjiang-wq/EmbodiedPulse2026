#!/usr/bin/env python3
"""
检查Bilibili数据库中"逐际动力"的实际值
"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, '.env'))

from sqlalchemy import create_engine, text
from bilibili_models import get_bilibili_session, BilibiliUp

def main():
    print("=" * 60)
    print("检查Bilibili数据库中'逐际动力'的实际值")
    print("=" * 60)
    
    # 方法1：直接SQL查询
    print("\n方法1：直接SQL查询")
    print("-" * 60)
    
    bilibili_db_url = os.getenv('BILIBILI_DATABASE_URL', 'sqlite:///./bilibili.db')
    print(f"数据库URL: {bilibili_db_url}")
    
    engine = create_engine(bilibili_db_url)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT uid, name, videos_count, views_count, views_formatted, is_active
            FROM bilibili_ups 
            WHERE name = '逐际动力'
            ORDER BY uid
        """))
        
        rows = result.fetchall()
        if rows:
            print(f"\n找到 {len(rows)} 条记录:")
            for i, row in enumerate(rows, 1):
                print(f"\n记录 {i}:")
                print(f"  uid: {row[0]}")
                print(f"  name: {row[1]}")
                print(f"  videos_count: {row[2]} (type: {type(row[2]).__name__})")
                print(f"  views_count: {row[3]} (type: {type(row[3]).__name__})")
                print(f"  views_formatted: {row[4]!r}")
                print(f"  is_active: {row[5]}")
        else:
            print("❌ 未找到记录")
    
    # 方法2：ORM查询
    print("\n" + "=" * 60)
    print("方法2：ORM查询")
    print("-" * 60)
    
    session = get_bilibili_session()
    
    # 查询所有名为"逐际动力"的记录
    ups = session.query(BilibiliUp).filter_by(name='逐际动力').all()
    
    if ups:
        print(f"\n找到 {len(ups)} 条记录:")
        for i, up in enumerate(ups, 1):
            print(f"\n记录 {i}:")
            print(f"  uid: {up.uid}")
            print(f"  name: {up.name}")
            print(f"  videos_count: {up.videos_count} (type: {type(up.videos_count).__name__})")
            print(f"  views_count: {up.views_count} (type: {type(up.views_count).__name__})")
            print(f"  views_formatted: {up.views_formatted!r}")
            print(f"  is_active: {up.is_active}")
    else:
        print("❌ 未找到记录")
    
    # 查询活跃的记录
    print("\n" + "=" * 60)
    print("查询is_active=True的记录")
    print("-" * 60)
    
    active_up = session.query(BilibiliUp).filter_by(name='逐际动力', is_active=True).first()
    
    if active_up:
        print(f"\n活跃记录:")
        print(f"  uid: {active_up.uid}")
        print(f"  name: {active_up.name}")
        print(f"  videos_count: {active_up.videos_count}")
        print(f"  views_count: {active_up.views_count}")
        print(f"  views_formatted: {active_up.views_formatted!r}")
    else:
        print("❌ 未找到活跃记录")
    
    session.close()
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)

if __name__ == '__main__':
    main()

