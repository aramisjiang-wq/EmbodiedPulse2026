#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查并修复管理员账号
"""

import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask
from database import db
from auth_models import AdminUser
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_and_fix_admin():
    """检查并修复管理员账号"""
    try:
        # 加载环境变量
        env_path = os.path.join(project_root, '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
        
        # 创建 Flask app 并初始化数据库
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///instance/auth.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        
        with app.app_context():
            username = 'limx'
            password = 'limx123456'
            
            logger.info(f"检查管理员账号: {username}")
            
            # 查询管理员
            admin = AdminUser.query.filter_by(username=username).first()
            
            if admin:
                logger.info(f"✅ 管理员账号存在")
                logger.info(f"   - ID: {admin.id}")
                logger.info(f"   - 用户名: {admin.username}")
                logger.info(f"   - 姓名: {admin.name}")
                logger.info(f"   - 角色: {admin.role}")
                logger.info(f"   - 状态: {admin.status}")
                logger.info(f"   - 密码哈希: {admin.password_hash[:50]}...")
                
                # 测试密码
                if check_password_hash(admin.password_hash, password):
                    logger.info(f"✅ 密码验证成功")
                else:
                    logger.warning(f"❌ 密码验证失败，正在重置密码...")
                    admin.password_hash = generate_password_hash(password)
                    admin.status = 'active'
                    db.session.commit()
                    logger.info(f"✅ 密码已重置")
            else:
                logger.warning(f"❌ 管理员账号不存在，正在创建...")
                password_hash = generate_password_hash(password)
                
                admin = AdminUser(
                    username=username,
                    password_hash=password_hash,
                    name='超级管理员',
                    role='super_admin',
                    status='active'
                )
                
                db.session.add(admin)
                db.session.commit()
                
                logger.info(f"✅ 管理员账号创建成功")
                logger.info(f"   - ID: {admin.id}")
                logger.info(f"   - 用户名: {admin.username}")
                logger.info(f"   - 密码: {password}")
            
            logger.info("\n" + "=" * 60)
            logger.info("✅ 管理员账号检查完成！")
            logger.info("=" * 60)
            
            return True
        
    except Exception as e:
        logger.error(f"❌ 检查管理员账号失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    check_and_fix_admin()

