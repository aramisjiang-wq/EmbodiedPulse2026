# -*- coding: utf-8 -*-
"""
初始化认证系统数据库
创建表结构并初始化超级管理员
"""

import os
import sys
from werkzeug.security import generate_password_hash
from database import db, init_db
from auth_models import AuthUser, AdminUser, AccessLog, LoginHistory
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def init_auth_database():
    """初始化认证系统数据库"""
    try:
        logger.info("=" * 60)
        logger.info("开始初始化认证系统数据库...")
        logger.info("=" * 60)
        
        # 创建所有表
        logger.info("\n1. 创建数据库表...")
        db.create_all()
        logger.info("✅ 数据库表创建成功")
        logger.info(f"   - auth_users (认证用户表)")
        logger.info(f"   - admin_users (管理员表)")
        logger.info(f"   - access_logs (访问日志表)")
        logger.info(f"   - login_history (登录历史表)")
        
        # 检查是否已存在超级管理员
        logger.info("\n2. 检查超级管理员...")
        super_admin_username = os.getenv('SUPER_ADMIN_USERNAME', 'limx')
        super_admin_password = os.getenv('SUPER_ADMIN_PASSWORD', 'limx123456')
        
        existing_admin = AdminUser.query.filter_by(username=super_admin_username).first()
        
        if existing_admin:
            logger.info(f"✅ 超级管理员已存在")
            logger.info(f"   - 用户名: {existing_admin.username}")
            logger.info(f"   - 姓名: {existing_admin.name}")
            logger.info(f"   - 角色: {existing_admin.role}")
            logger.info(f"   - 状态: {existing_admin.status}")
        else:
            # 创建超级管理员
            logger.info(f"创建超级管理员...")
            logger.info(f"   - 用户名: {super_admin_username}")
            logger.info(f"   - 密码: {'*' * len(super_admin_password)}")
            
            password_hash = generate_password_hash(super_admin_password)
            
            super_admin = AdminUser(
                username=super_admin_username,
                password_hash=password_hash,
                name='超级管理员',
                role='super_admin',
                status='active'
            )
            
            db.session.add(super_admin)
            db.session.commit()
            
            logger.info(f"✅ 超级管理员创建成功")
            logger.info(f"   - ID: {super_admin.id}")
            logger.info(f"   - 用户名: {super_admin.username}")
            logger.info(f"   - 姓名: {super_admin.name}")
        
        # 统计信息
        logger.info("\n3. 数据库统计信息...")
        auth_user_count = AuthUser.query.count()
        admin_user_count = AdminUser.query.count()
        access_log_count = AccessLog.query.count()
        login_history_count = LoginHistory.query.count()
        
        logger.info(f"   - 认证用户数: {auth_user_count}")
        logger.info(f"   - 管理员数: {admin_user_count}")
        logger.info(f"   - 访问日志数: {access_log_count}")
        logger.info(f"   - 登录历史数: {login_history_count}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 认证系统数据库初始化完成！")
        logger.info("=" * 60)
        
        logger.info("\n📝 超级管理员登录信息:")
        logger.info(f"   用户名: {super_admin_username}")
        logger.info(f"   密码: {super_admin_password}")
        logger.info(f"   登录地址: http://localhost:5001/admin/login")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ 初始化数据库失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def drop_auth_tables():
    """删除认证系统表（危险操作，仅用于开发环境）"""
    logger.warning("=" * 60)
    logger.warning("⚠️  警告：即将删除认证系统所有表！")
    logger.warning("=" * 60)
    
    confirm = input("请输入 'YES' 确认删除: ")
    if confirm != 'YES':
        logger.info("已取消删除操作")
        return False
    
    try:
        logger.info("删除认证系统表...")
        AuthUser.__table__.drop(db.engine, checkfirst=True)
        AdminUser.__table__.drop(db.engine, checkfirst=True)
        AccessLog.__table__.drop(db.engine, checkfirst=True)
        LoginHistory.__table__.drop(db.engine, checkfirst=True)
        logger.info("✅ 认证系统表删除成功")
        return True
    except Exception as e:
        logger.error(f"❌ 删除表失败: {e}")
        return False


def reset_auth_database():
    """重置认证系统数据库（删除并重新创建）"""
    logger.info("重置认证系统数据库...")
    if drop_auth_tables():
        return init_auth_database()
    return False


if __name__ == '__main__':
    # 根据命令行参数执行不同操作
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'init':
            init_auth_database()
        elif command == 'drop':
            drop_auth_tables()
        elif command == 'reset':
            reset_auth_database()
        else:
            print("未知命令，可用命令:")
            print("  init  - 初始化数据库")
            print("  drop  - 删除所有表")
            print("  reset - 重置数据库")
    else:
        # 默认执行初始化
        init_auth_database()

