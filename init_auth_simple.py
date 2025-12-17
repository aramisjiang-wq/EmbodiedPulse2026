#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的认证系统数据库初始化脚本
使用Flask应用上下文
"""

import os
import sys

# 设置环境变量（如果需要）
os.environ.setdefault('FLASK_APP', 'app.py')

# 导入Flask应用
from app import app
from database import db
from auth_models import AuthUser, AdminUser, AccessLog, LoginHistory
from werkzeug.security import generate_password_hash
import hashlib


def init_auth_database():
    """初始化认证系统数据库"""
    with app.app_context():
        print("=" * 60)
        print("开始初始化认证系统数据库...")
        print("=" * 60)
        
        try:
            # 1. 创建所有表
            print("\n1. 创建数据库表...")
            db.create_all()
            print("✅ 数据库表创建成功")
            print("   - auth_users (认证用户表)")
            print("   - admin_users (管理员表)")
            print("   - access_logs (访问日志表)")
            print("   - login_history (登录历史表)")
            
            # 2. 检查并创建超级管理员
            print("\n2. 检查超级管理员...")
            super_admin_username = os.getenv('SUPER_ADMIN_USERNAME', 'limx')
            super_admin_password = os.getenv('SUPER_ADMIN_PASSWORD', 'limx123456')
            
            existing_admin = AdminUser.query.filter_by(username=super_admin_username).first()
            
            if existing_admin:
                print(f"✅ 超级管理员已存在")
                print(f"   - 用户名: {existing_admin.username}")
                print(f"   - 姓名: {existing_admin.name}")
                print(f"   - 角色: {existing_admin.role}")
                print(f"   - 状态: {existing_admin.status}")
            else:
                # 创建超级管理员
                print(f"创建超级管理员...")
                print(f"   - 用户名: {super_admin_username}")
                print(f"   - 密码: {'*' * len(super_admin_password)}")
                
                # 使用pbkdf2:sha256方法（兼容Python 3.9）
                password_hash = generate_password_hash(super_admin_password, method='pbkdf2:sha256')
                
                super_admin = AdminUser(
                    username=super_admin_username,
                    password_hash=password_hash,
                    name='超级管理员',
                    role='super_admin',
                    status='active'
                )
                
                db.session.add(super_admin)
                db.session.commit()
                
                print(f"✅ 超级管理员创建成功")
                print(f"   - ID: {super_admin.id}")
                print(f"   - 用户名: {super_admin.username}")
                print(f"   - 姓名: {super_admin.name}")
            
            # 3. 统计信息
            print("\n3. 数据库统计信息...")
            auth_user_count = AuthUser.query.count()
            admin_user_count = AdminUser.query.count()
            access_log_count = AccessLog.query.count()
            login_history_count = LoginHistory.query.count()
            
            print(f"   - 认证用户数: {auth_user_count}")
            print(f"   - 管理员数: {admin_user_count}")
            print(f"   - 访问日志数: {access_log_count}")
            print(f"   - 登录历史数: {login_history_count}")
            
            print("\n" + "=" * 60)
            print("✅ 认证系统数据库初始化完成！")
            print("=" * 60)
            
            print("\n📝 超级管理员登录信息:")
            print(f"   用户名: {super_admin_username}")
            print(f"   密码: {super_admin_password}")
            print(f"   登录地址: http://localhost:5001/admin/login")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 初始化数据库失败: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        init_auth_database()
    else:
        print("用法: python3 init_auth_simple.py init")

