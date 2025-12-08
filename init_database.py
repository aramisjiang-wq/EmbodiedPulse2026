"""
初始化数据库脚本
"""
from models import init_db, get_session, Paper
from migrate_json_to_db import migrate_json_to_database

if __name__ == '__main__':
    print("=" * 50)
    print("初始化数据库")
    print("=" * 50)
    
    # 1. 创建数据库表
    print("\n1. 创建数据库表...")
    init_db()
    
    # 2. 迁移JSON数据到数据库
    print("\n2. 迁移JSON数据到数据库...")
    try:
        migrate_json_to_database()
    except Exception as e:
        print(f"迁移失败: {e}")
        print("可以稍后手动运行: python migrate_json_to_db.py")
    
    # 3. 显示统计信息
    print("\n3. 数据库统计信息:")
    session = get_session()
    total = session.query(Paper).count()
    print(f"   总论文数: {total}")
    
    from sqlalchemy import func
    stats = session.query(
        Paper.category,
        func.count(Paper.id).label('count')
    ).group_by(Paper.category).all()
    
    for category, count in stats:
        print(f"   {category}: {count}")
    
    session.close()
    print("\n数据库初始化完成！")

