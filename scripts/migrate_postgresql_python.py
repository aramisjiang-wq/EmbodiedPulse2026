#!/usr/bin/env python3
"""
使用Python从本地PostgreSQL迁移到服务器PostgreSQL
不需要pg_dump，直接使用SQLAlchemy迁移
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 本地PostgreSQL配置
LOCAL_PG_URL = os.getenv('LOCAL_DATABASE_URL', 'postgresql://robotics_user:robotics_password@localhost:5432/robotics_arxiv')

# 服务器PostgreSQL配置（从环境变量或命令行参数获取）
SERVER_PG_URL = os.getenv('SERVER_DATABASE_URL')

if not SERVER_PG_URL:
    print("=" * 60)
    print("PostgreSQL到PostgreSQL迁移工具（Python版）")
    print("=" * 60)
    print()
    print("使用方法:")
    print("  python3 scripts/migrate_postgresql_python.py")
    print()
    print("环境变量:")
    print("  LOCAL_DATABASE_URL  - 本地PostgreSQL连接URL")
    print("  SERVER_DATABASE_URL - 服务器PostgreSQL连接URL")
    print()
    print("示例:")
    print("  export LOCAL_DATABASE_URL='postgresql://user:pass@localhost:5432/db'")
    print("  export SERVER_DATABASE_URL='postgresql://user:pass@server:5432/db'")
    print("  python3 scripts/migrate_postgresql_python.py")
    print()
    sys.exit(1)

def migrate_table(local_url, server_url, table_name, model_class):
    """迁移单个表的数据"""
    print(f"\n{'='*60}")
    print(f"迁移表: {table_name}")
    print(f"{'='*60}")
    
    try:
        # 连接本地PostgreSQL
        local_engine = create_engine(local_url, echo=False)
        local_session = sessionmaker(bind=local_engine)()
        
        # 连接服务器PostgreSQL
        server_engine = create_engine(
            server_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )
        server_session = sessionmaker(bind=server_engine)()
        
        # 检查服务器表是否存在
        with server_engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                );
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print(f"  ⚠️  服务器表 {table_name} 不存在，跳过迁移")
                print(f"  💡 提示: 请先在服务器上运行 python3 init_database.py")
                local_session.close()
                server_session.close()
                return False
        
        # 读取本地数据
        print(f"  📖 从本地PostgreSQL读取数据...")
        local_data = local_session.query(model_class).all()
        total_count = len(local_data)
        print(f"  ✅ 读取到 {total_count} 条记录")
        
        if total_count == 0:
            print(f"  ℹ️  没有数据需要迁移")
            local_session.close()
            server_session.close()
            return True
        
        # 检查服务器中是否已有数据
        existing_count = server_session.query(model_class).count()
        if existing_count > 0:
            print(f"  ⚠️  服务器中已有 {existing_count} 条记录")
            response = input(f"  ❓ 是否继续迁移？这将添加新数据（不会删除现有数据）[y/N]: ")
            if response.lower() != 'y':
                print(f"  ❌ 用户取消迁移")
                local_session.close()
                server_session.close()
                return False
        
        # 迁移数据
        print(f"  📝 开始迁移数据到服务器PostgreSQL...")
        migrated = 0
        skipped = 0
        errors = 0
        
        for record in local_data:
            try:
                # 检查是否已存在（根据主键）
                existing = server_session.query(model_class).filter_by(id=record.id).first()
                if existing:
                    skipped += 1
                    continue
                
                # 创建新记录
                new_record = model_class()
                for column in model_class.__table__.columns:
                    setattr(new_record, column.name, getattr(record, column.name))
                
                server_session.add(new_record)
                migrated += 1
                
                # 每100条提交一次
                if migrated % 100 == 0:
                    server_session.commit()
                    print(f"    ... 已迁移 {migrated}/{total_count} 条记录")
                    
            except Exception as e:
                errors += 1
                print(f"    ⚠️  迁移记录失败 (id={getattr(record, 'id', 'unknown')}): {e}")
                server_session.rollback()
                continue
        
        # 最终提交
        server_session.commit()
        
        print(f"\n  ✅ 迁移完成!")
        print(f"     - 成功: {migrated} 条")
        print(f"     - 跳过: {skipped} 条（已存在）")
        print(f"     - 失败: {errors} 条")
        
        local_session.close()
        server_session.close()
        return True
        
    except Exception as e:
        print(f"  ❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("="*60)
    print("PostgreSQL → PostgreSQL 数据迁移工具（Python版）")
    print("="*60)
    
    # 检查连接
    print(f"\n📡 检查本地PostgreSQL连接...")
    print(f"   URL: {LOCAL_PG_URL.replace(LOCAL_PG_URL.split('@')[0].split('//')[1] if '@' in LOCAL_PG_URL else '', '***@')}")
    
    try:
        local_engine = create_engine(LOCAL_PG_URL, echo=False)
        with local_engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"   ✅ 本地PostgreSQL连接成功")
            print(f"   📌 版本: {version.split(',')[0]}")
    except Exception as e:
        print(f"   ❌ 本地PostgreSQL连接失败: {e}")
        print(f"\n💡 提示:")
        print(f"   1. 确保本地PostgreSQL服务正在运行")
        print(f"   2. 检查LOCAL_DATABASE_URL环境变量是否正确")
        print(f"   3. 如果使用Docker，确保容器正在运行")
        sys.exit(1)
    
    print(f"\n📡 检查服务器PostgreSQL连接...")
    print(f"   URL: {SERVER_PG_URL.replace(SERVER_PG_URL.split('@')[0].split('//')[1] if '@' in SERVER_PG_URL else '', '***@')}")
    
    try:
        server_engine = create_engine(SERVER_PG_URL, echo=False)
        with server_engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"   ✅ 服务器PostgreSQL连接成功")
            print(f"   📌 版本: {version.split(',')[0]}")
    except Exception as e:
        print(f"   ❌ 服务器PostgreSQL连接失败: {e}")
        print(f"\n💡 提示:")
        print(f"   1. 确保服务器PostgreSQL服务正在运行")
        print(f"   2. 检查SERVER_DATABASE_URL环境变量是否正确")
        print(f"   3. 检查网络连接和防火墙设置")
        sys.exit(1)
    
    # 迁移各个数据库
    results = {}
    
    # 1. 迁移论文数据库
    try:
        from models import Paper
        results['papers'] = migrate_table(
            LOCAL_PG_URL,
            SERVER_PG_URL,
            'papers',
            Paper
        )
    except Exception as e:
        print(f"\n❌ 论文数据库迁移失败: {e}")
        results['papers'] = False
    
    # 2. 迁移招聘信息数据库
    try:
        from jobs_models import Job
        results['jobs'] = migrate_table(
            LOCAL_PG_URL,
            SERVER_PG_URL,
            'jobs',
            Job
        )
    except Exception as e:
        print(f"\n❌ 招聘信息数据库迁移失败: {e}")
        results['jobs'] = False
    
    # 3. 迁移新闻数据库
    try:
        from news_models import News
        results['news'] = migrate_table(
            LOCAL_PG_URL,
            SERVER_PG_URL,
            'news',
            News
        )
    except Exception as e:
        print(f"\n❌ 新闻数据库迁移失败: {e}")
        results['news'] = False
    
    # 4. 迁移数据集数据库
    try:
        from datasets_models import Dataset
        results['datasets'] = migrate_table(
            LOCAL_PG_URL,
            SERVER_PG_URL,
            'datasets',
            Dataset
        )
    except Exception as e:
        print(f"\n❌ 数据集数据库迁移失败: {e}")
        results['datasets'] = False
    
    # 5. 迁移Bilibili数据库
    try:
        from bilibili_models import BilibiliUp, BilibiliVideo
        
        print(f"\n迁移Bilibili UP主数据...")
        results['bilibili_ups'] = migrate_table(
            LOCAL_PG_URL,
            SERVER_PG_URL,
            'bilibili_ups',
            BilibiliUp
        )
        
        print(f"\n迁移Bilibili视频数据...")
        results['bilibili_videos'] = migrate_table(
            LOCAL_PG_URL,
            SERVER_PG_URL,
            'bilibili_videos',
            BilibiliVideo
        )
    except Exception as e:
        print(f"\n❌ Bilibili数据库迁移失败: {e}")
        results['bilibili_ups'] = False
        results['bilibili_videos'] = False
    
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

