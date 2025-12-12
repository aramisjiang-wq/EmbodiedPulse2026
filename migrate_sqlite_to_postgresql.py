"""
从SQLite迁移数据到PostgreSQL
支持迁移所有数据库：papers, jobs, news, datasets
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# SQLite数据库路径
SQLITE_PAPERS_DB = 'sqlite:///./papers.db'
SQLITE_JOBS_DB = 'sqlite:///./jobs.db'
SQLITE_NEWS_DB = 'sqlite:///./news.db'
SQLITE_DATASETS_DB = 'sqlite:///./datasets.db'

# PostgreSQL连接URL（从环境变量获取）
POSTGRES_URL = os.getenv('DATABASE_URL', 'postgresql://robotics_user:robotics_password@localhost:5432/robotics_arxiv')

def migrate_table(sqlite_url, postgres_url, table_name, model_class):
    """迁移单个表的数据"""
    print(f"\n{'='*60}")
    print(f"迁移表: {table_name}")
    print(f"{'='*60}")
    
    try:
        # 连接SQLite
        sqlite_engine = create_engine(sqlite_url, echo=False)
        sqlite_session = sessionmaker(bind=sqlite_engine)()
        
        # 连接PostgreSQL
        postgres_engine = create_engine(
            postgres_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )
        postgres_session = sessionmaker(bind=postgres_engine)()
        
        # 检查PostgreSQL表是否存在
        with postgres_engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                );
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print(f"  ⚠️  PostgreSQL表 {table_name} 不存在，跳过迁移")
                print(f"  💡 提示: 请先运行 python3 init_database.py 创建表结构")
                sqlite_session.close()
                postgres_session.close()
                return False
        
        # 读取SQLite数据
        print(f"  📖 从SQLite读取数据...")
        sqlite_data = sqlite_session.query(model_class).all()
        total_count = len(sqlite_data)
        print(f"  ✅ 读取到 {total_count} 条记录")
        
        if total_count == 0:
            print(f"  ℹ️  没有数据需要迁移")
            sqlite_session.close()
            postgres_session.close()
            return True
        
        # 检查PostgreSQL中是否已有数据
        existing_count = postgres_session.query(model_class).count()
        if existing_count > 0:
            print(f"  ⚠️  PostgreSQL中已有 {existing_count} 条记录")
            response = input(f"  ❓ 是否继续迁移？这将添加新数据（不会删除现有数据）[y/N]: ")
            if response.lower() != 'y':
                print(f"  ❌ 用户取消迁移")
                sqlite_session.close()
                postgres_session.close()
                return False
        
        # 迁移数据
        print(f"  📝 开始迁移数据到PostgreSQL...")
        migrated = 0
        skipped = 0
        errors = 0
        
        for record in sqlite_data:
            try:
                # 检查是否已存在（根据主键）
                existing = postgres_session.query(model_class).filter_by(id=record.id).first()
                if existing:
                    skipped += 1
                    continue
                
                # 创建新记录
                new_record = model_class()
                for column in model_class.__table__.columns:
                    setattr(new_record, column.name, getattr(record, column.name))
                
                postgres_session.add(new_record)
                migrated += 1
                
                # 每100条提交一次
                if migrated % 100 == 0:
                    postgres_session.commit()
                    print(f"    ... 已迁移 {migrated}/{total_count} 条记录")
                    
            except Exception as e:
                errors += 1
                print(f"    ⚠️  迁移记录失败 (id={getattr(record, 'id', 'unknown')}): {e}")
                postgres_session.rollback()
                continue
        
        # 最终提交
        postgres_session.commit()
        
        print(f"\n  ✅ 迁移完成!")
        print(f"     - 成功: {migrated} 条")
        print(f"     - 跳过: {skipped} 条（已存在）")
        print(f"     - 失败: {errors} 条")
        
        sqlite_session.close()
        postgres_session.close()
        return True
        
    except Exception as e:
        print(f"  ❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("="*60)
    print("SQLite → PostgreSQL 数据迁移工具")
    print("="*60)
    
    # 检查PostgreSQL连接
    print(f"\n📡 检查PostgreSQL连接...")
    print(f"   URL: {POSTGRES_URL.replace(POSTGRES_URL.split('@')[0].split('//')[1] if '@' in POSTGRES_URL else '', '***@')}")
    
    try:
        postgres_engine = create_engine(POSTGRES_URL, echo=False)
        with postgres_engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"   ✅ PostgreSQL连接成功")
            print(f"   📌 版本: {version.split(',')[0]}")
    except Exception as e:
        print(f"   ❌ PostgreSQL连接失败: {e}")
        print(f"\n💡 提示:")
        print(f"   1. 确保PostgreSQL服务正在运行")
        print(f"   2. 检查DATABASE_URL环境变量是否正确")
        print(f"   3. 检查数据库用户权限")
        sys.exit(1)
    
    # 迁移各个数据库
    results = {}
    
    # 1. 迁移论文数据库
    try:
        from models import Paper
        results['papers'] = migrate_table(
            SQLITE_PAPERS_DB,
            POSTGRES_URL,
            'papers',
            Paper
        )
    except Exception as e:
        print(f"\n❌ 论文数据库迁移失败: {e}")
        results['papers'] = False
    
    # 2. 迁移招聘信息数据库
    try:
        from jobs_models import Job
        # 如果使用独立数据库URL，可以从环境变量获取
        jobs_postgres_url = os.getenv('JOBS_DATABASE_URL', POSTGRES_URL)
        results['jobs'] = migrate_table(
            SQLITE_JOBS_DB,
            jobs_postgres_url,
            'jobs',
            Job
        )
    except Exception as e:
        print(f"\n❌ 招聘信息数据库迁移失败: {e}")
        results['jobs'] = False
    
    # 3. 迁移新闻数据库
    try:
        from news_models import News
        news_postgres_url = os.getenv('NEWS_DATABASE_URL', POSTGRES_URL)
        results['news'] = migrate_table(
            SQLITE_NEWS_DB,
            news_postgres_url,
            'news',
            News
        )
    except Exception as e:
        print(f"\n❌ 新闻数据库迁移失败: {e}")
        results['news'] = False
    
    # 4. 迁移数据集数据库
    try:
        from datasets_models import Dataset
        datasets_postgres_url = os.getenv('DATASETS_DATABASE_URL', POSTGRES_URL)
        results['datasets'] = migrate_table(
            SQLITE_DATASETS_DB,
            datasets_postgres_url,
            'datasets',
            Dataset
        )
    except Exception as e:
        print(f"\n❌ 数据集数据库迁移失败: {e}")
        results['datasets'] = False
    
    # 总结
    print(f"\n{'='*60}")
    print("迁移总结")
    print(f"{'='*60}")
    for db_name, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  {db_name}: {status}")
    
    all_success = all(results.values())
    if all_success:
        print(f"\n🎉 所有数据库迁移完成！")
    else:
        print(f"\n⚠️  部分数据库迁移失败，请检查错误信息")

if __name__ == '__main__':
    main()
