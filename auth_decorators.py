# -*- coding: utf-8 -*-
"""
权限装饰器模块
用于API权限验证
"""

from functools import wraps
from flask import request, jsonify
import logging
from jwt_utils import verify_token
from auth_models import AuthUser, AdminUser
from database import db

logger = logging.getLogger(__name__)


def login_required(f):
    """
    需要登录装饰器（普通用户权限）
    验证JWT token并将用户信息附加到request.current_user
    用户只能访问自己的数据
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.warning("请求缺少Authorization header")
            return jsonify({
                'success': False,
                'message': '未登录，请先登录'
            }), 401
        
        # 提取token
        token = auth_header.replace('Bearer ', '')
        
        # 验证token
        payload = verify_token(token)
        if not payload:
            logger.warning("Token无效或已过期")
            return jsonify({
                'success': False,
                'message': 'Token无效或已过期，请重新登录'
            }), 401
        
        # 获取user_id
        user_id = payload.get('user_id')
        if not user_id:
            logger.warning("Token中缺少user_id")
            return jsonify({
                'success': False,
                'message': 'Token格式错误'
            }), 401
        
        # 查询用户
        user = db.session.query(AuthUser).filter_by(id=user_id).first()
        if not user:
            logger.warning(f"用户不存在 - user_id: {user_id}")
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        # 检查用户状态
        if user.status != 'active':
            logger.warning(f"用户已被禁用 - user_id: {user_id}, status: {user.status}")
            return jsonify({
                'success': False,
                'message': f'账号状态异常: {user.status}'
            }), 403
        
        # 将用户信息附加到request对象
        request.current_user = user
        request.token_payload = payload
        
        logger.info(f"用户认证成功 - user_id: {user_id}, name: {user.name}")
        
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """
    需要管理员权限装饰器
    验证JWT token并检查是否为管理员
    管理员可以访问所有用户的数据
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.warning("请求缺少Authorization header")
            return jsonify({
                'success': False,
                'message': '未登录，请先登录'
            }), 401
        
        # 提取token
        token = auth_header.replace('Bearer ', '')
        
        # 验证token
        payload = verify_token(token)
        if not payload:
            logger.warning("Token无效或已过期")
            return jsonify({
                'success': False,
                'message': 'Token无效或已过期，请重新登录'
            }), 401
        
        # 获取user_id和role
        user_id = payload.get('user_id')
        role = payload.get('role')
        
        if not user_id:
            logger.warning("Token中缺少user_id")
            return jsonify({
                'success': False,
                'message': 'Token格式错误'
            }), 401
        
        # 检查role
        if role not in ['admin', 'super_admin']:
            logger.warning(f"权限不足 - user_id: {user_id}, role: {role}")
            return jsonify({
                'success': False,
                'message': '权限不足，需要管理员权限'
            }), 403
        
        # 查询用户（可能是auth_users或admin_users）
        user = None
        
        # 先查询admin_users表
        admin_user = db.session.query(AdminUser).filter_by(id=user_id).first()
        if admin_user:
            if admin_user.status != 'active':
                logger.warning(f"管理员账号已被禁用 - user_id: {user_id}")
                return jsonify({
                    'success': False,
                    'message': '管理员账号已被禁用'
                }), 403
            user = admin_user
        else:
            # 查询auth_users表（飞书登录的管理员）
            auth_user = db.session.query(AuthUser).filter_by(id=user_id).first()
            if auth_user:
                if auth_user.status != 'active':
                    logger.warning(f"管理员账号已被禁用 - user_id: {user_id}")
                    return jsonify({
                        'success': False,
                        'message': '管理员账号已被禁用'
                    }), 403
                if auth_user.role not in ['admin', 'super_admin']:
                    logger.warning(f"权限不足 - user_id: {user_id}, role: {auth_user.role}")
                    return jsonify({
                        'success': False,
                        'message': '权限不足，需要管理员权限'
                    }), 403
                user = auth_user
        
        if not user:
            logger.warning(f"管理员不存在 - user_id: {user_id}")
            return jsonify({
                'success': False,
                'message': '管理员不存在'
            }), 404
        
        # 将管理员信息附加到request对象
        request.current_user = user
        request.token_payload = payload
        
        logger.info(f"管理员认证成功 - user_id: {user_id}, role: {role}")
        
        return f(*args, **kwargs)
    
    return decorated_function


def super_admin_required(f):
    """
    需要超级管理员权限装饰器
    仅超级管理员可以访问
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.warning("请求缺少Authorization header")
            return jsonify({
                'success': False,
                'message': '未登录，请先登录'
            }), 401
        
        # 提取token
        token = auth_header.replace('Bearer ', '')
        
        # 验证token
        payload = verify_token(token)
        if not payload:
            logger.warning("Token无效或已过期")
            return jsonify({
                'success': False,
                'message': 'Token无效或已过期，请重新登录'
            }), 401
        
        # 获取user_id和role
        user_id = payload.get('user_id')
        role = payload.get('role')
        
        if not user_id:
            logger.warning("Token中缺少user_id")
            return jsonify({
                'success': False,
                'message': 'Token格式错误'
            }), 401
        
        # 检查role
        if role != 'super_admin':
            logger.warning(f"权限不足 - user_id: {user_id}, role: {role}")
            return jsonify({
                'success': False,
                'message': '权限不足，需要超级管理员权限'
            }), 403
        
        # 查询用户
        user = None
        admin_user = db.session.query(AdminUser).filter_by(id=user_id).first()
        if admin_user:
            user = admin_user
        else:
            auth_user = db.session.query(AuthUser).filter_by(id=user_id).first()
            if auth_user:
                user = auth_user
        
        if not user:
            logger.warning(f"超级管理员不存在 - user_id: {user_id}")
            return jsonify({
                'success': False,
                'message': '超级管理员不存在'
            }), 404
        
        # 将超级管理员信息附加到request对象
        request.current_user = user
        request.token_payload = payload
        
        logger.info(f"超级管理员认证成功 - user_id: {user_id}")
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user():
    """
    获取当前请求的用户对象
    必须在使用了@login_required、@admin_required或@super_admin_required装饰器的函数中调用
    
    Returns:
        AuthUser或AdminUser对象，如果未认证则返回None
    """
    return getattr(request, 'current_user', None)


def get_current_user_id():
    """
    获取当前请求的用户ID
    
    Returns:
        user_id，如果未认证则返回None
    """
    user = get_current_user()
    return user.id if user else None


def get_current_role():
    """
    获取当前请求的用户角色
    
    Returns:
        role字符串，如果未认证则返回None
    """
    payload = getattr(request, 'token_payload', None)
    return payload.get('role') if payload else None

