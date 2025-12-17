# -*- coding: utf-8 -*-
"""
飞书登录系统 - 数据库模型
包含：用户表、管理员表、访问日志表、登录历史表
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime
from database import db


class AuthUser(db.Model):
    """认证用户表 - 飞书登录用户"""
    __tablename__ = 'auth_users'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 飞书相关
    feishu_id = Column(String(100), unique=True, nullable=False, index=True, comment='飞书用户ID')
    feishu_union_id = Column(String(100), comment='飞书Union ID')
    feishu_open_id = Column(String(100), comment='飞书Open ID')
    
    # 基本信息
    name = Column(String(100), nullable=False, comment='用户姓名')
    email = Column(String(200), index=True, comment='邮箱')
    mobile = Column(String(20), comment='手机号')
    avatar_url = Column(Text, comment='头像URL')
    department = Column(String(200), comment='部门')
    
    # 身份和权限
    user_type = Column(String(20), default='内部', comment='用户身份: 内部/外部')
    role = Column(String(20), default='user', index=True, comment='角色: user/admin/super_admin')
    status = Column(String(20), default='active', index=True, comment='状态: active/inactive/banned')
    
    # 登录信息
    last_login_at = Column(DateTime, comment='最后登录时间')
    last_login_ip = Column(String(50), comment='最后登录IP')
    login_count = Column(Integer, default=0, comment='登录次数')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'feishu_id': self.feishu_id,
            'feishu_union_id': self.feishu_union_id,
            'feishu_open_id': self.feishu_open_id,
            'name': self.name,
            'email': self.email,
            'mobile': self.mobile,
            'avatar_url': self.avatar_url,
            'department': self.department,
            'user_type': self.user_type,
            'role': self.role,
            'status': self.status,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'last_login_ip': self.last_login_ip,
            'login_count': self.login_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<AuthUser {self.id}: {self.name} ({self.role})>'


class AdminUser(db.Model):
    """管理员表 - 用户名密码登录的管理员"""
    __tablename__ = 'admin_users'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 登录凭证
    username = Column(String(50), unique=True, nullable=False, index=True, comment='用户名')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    
    # 基本信息
    name = Column(String(100), comment='真实姓名')
    email = Column(String(200), comment='邮箱')
    
    # 权限
    role = Column(String(20), default='admin', index=True, comment='角色: admin/super_admin')
    status = Column(String(20), default='active', comment='状态: active/inactive')
    
    # 关联飞书（可选，管理员也可以使用飞书登录）
    auth_user_id = Column(Integer, ForeignKey('auth_users.id'), comment='关联的飞书用户ID')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    last_login_at = Column(DateTime, comment='最后登录时间')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'status': self.status,
            'auth_user_id': self.auth_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }
    
    def __repr__(self):
        return f'<AdminUser {self.id}: {self.username} ({self.role})>'


class AccessLog(db.Model):
    """访问日志表 - 记录用户访问行为"""
    __tablename__ = 'access_logs'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 用户信息
    user_id = Column(Integer, ForeignKey('auth_users.id'), index=True, comment='用户ID')
    username = Column(String(100), comment='用户名（冗余，便于查询）')
    
    # 访问信息
    page_url = Column(Text, nullable=False, comment='访问页面URL')
    page_title = Column(String(200), comment='页面标题')
    http_method = Column(String(10), comment='HTTP方法')
    
    # 请求详情
    ip_address = Column(String(50), index=True, comment='IP地址')
    user_agent = Column(Text, comment='User Agent')
    referer = Column(Text, comment='来源页面')
    
    # 地理位置（可选）
    country = Column(String(50), comment='国家')
    city = Column(String(100), comment='城市')
    
    # 时间信息
    access_time = Column(DateTime, default=datetime.utcnow, index=True, comment='访问时间')
    duration = Column(Integer, comment='停留时长（毫秒）')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'page_url': self.page_url,
            'page_title': self.page_title,
            'http_method': self.http_method,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'referer': self.referer,
            'country': self.country,
            'city': self.city,
            'access_time': self.access_time.isoformat() if self.access_time else None,
            'duration': self.duration
        }
    
    def __repr__(self):
        return f'<AccessLog {self.id}: {self.username} -> {self.page_url}>'


class LoginHistory(db.Model):
    """登录历史表 - 记录用户登录行为"""
    __tablename__ = 'login_history'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 用户信息
    user_id = Column(Integer, ForeignKey('auth_users.id'), index=True, comment='用户ID')
    login_type = Column(String(20), nullable=False, comment='登录类型: feishu/password')
    
    # 登录结果
    status = Column(String(20), nullable=False, index=True, comment='状态: success/failed')
    failure_reason = Column(Text, comment='失败原因')
    
    # 登录信息
    ip_address = Column(String(50), comment='IP地址')
    user_agent = Column(Text, comment='User Agent')
    location = Column(String(200), comment='登录地点')
    
    # 时间戳
    login_time = Column(DateTime, default=datetime.utcnow, index=True, comment='登录时间')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'login_type': self.login_type,
            'status': self.status,
            'failure_reason': self.failure_reason,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'location': self.location,
            'login_time': self.login_time.isoformat() if self.login_time else None
        }
    
    def __repr__(self):
        return f'<LoginHistory {self.id}: User {self.user_id} - {self.status}>'

