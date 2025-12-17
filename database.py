# -*- coding: utf-8 -*-
"""
数据库初始化和管理
整合主数据库（论文等）和认证数据库
"""

from flask_sqlalchemy import SQLAlchemy
import os

# Flask-SQLAlchemy实例
db = SQLAlchemy()

# 为了兼容性，提供Base（虽然Flask-SQLAlchemy使用db.Model）
Base = db.Model


def init_db(app):
    """
    初始化Flask-SQLAlchemy数据库
    """
    # 配置数据库URI（使用现有的论文数据库）
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./papers.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化Flask-SQLAlchemy
    db.init_app(app)
    
    return db


def create_tables(app):
    """创建所有数据库表"""
    with app.app_context():
        db.create_all()
        print("✅ 所有数据库表创建成功")

