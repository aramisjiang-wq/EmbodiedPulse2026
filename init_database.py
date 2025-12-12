"""
初始化数据库脚本
支持PostgreSQL和SQLite
"""
from models import init_db, get_session, Paper
from jobs_models import init_jobs_db
from news_models import init_news_db
from datasets_models import init_datasets_db
from migrate_json_to_db import migrate_json_to_database

if __name__ == '__main__':
    print("=" * 60)
    print("初始化所有数据库")
    print("=" * 60)
    
    # 1. 创建所有数据库表
    print("\n1. 创建数据库表...")
    print("   - 论文数据库...")
    init_db()
    print("   - 招聘信息数据库...")
    init_jobs_db()
    print("   - 新闻数据库...")
    init_news_db()
    print("   - 数据集数据库...")
    init_datasets_db()
    
    # 2. 迁移JSON数据到数据库（仅论文数据库）
    print("\n2. 迁移JSON数据到数据库...")
    try:
        migrate_json_to_database()
    except Exception as e:
        print(f"迁移失败: {e}")
        print("可以稍后手动运行: python migrate_json_to_db.py")
    
    # 3. 显示统计信息
    print("\n3. 数据库统计信息:")
    
    # 论文数据库
    try:
        session = get_session()
        total = session.query(Paper).count()
        print(f"   论文数据库 - 总论文数: {total}")
        
        from sqlalchemy import func
        stats = session.query(
            Paper.category,
            func.count(Paper.id).label('count')
        ).group_by(Paper.category).all()
        
        for category, count in stats:
            print(f"     {category}: {count}")
        session.close()
    except Exception as e:
        print(f"   论文数据库统计失败: {e}")
    
    # 其他数据库统计
    try:
        from jobs_models import get_jobs_session, Job
        jobs_session = get_jobs_session()
        jobs_count = jobs_session.query(Job).count()
        print(f"   招聘信息数据库 - 总记录数: {jobs_count}")
        jobs_session.close()
    except Exception as e:
        print(f"   招聘信息数据库统计失败: {e}")
    
    try:
        from news_models import get_news_session, News
        news_session = get_news_session()
        news_count = news_session.query(News).count()
        print(f"   新闻数据库 - 总记录数: {news_count}")
        news_session.close()
    except Exception as e:
        print(f"   新闻数据库统计失败: {e}")
    
    try:
        from datasets_models import get_datasets_session, Dataset
        datasets_session = get_datasets_session()
        datasets_count = datasets_session.query(Dataset).count()
        print(f"   数据集数据库 - 总记录数: {datasets_count}")
        datasets_session.close()
    except Exception as e:
        print(f"   数据集数据库统计失败: {e}")
    
    print("\n✅ 所有数据库初始化完成！")

