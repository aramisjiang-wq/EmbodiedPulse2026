# -*- coding: utf-8 -*-
"""
飞书登录系统 - 认证路由模块
包含所有认证相关的API端点
"""

from flask import Blueprint, request, jsonify, redirect, url_for
import logging
import secrets
import os
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from auth_decorators import login_required, admin_required, super_admin_required, get_current_user
from jwt_utils import generate_token
from feishu_auth import get_feishu_auth
from auth_models import AuthUser, AdminUser, AccessLog, LoginHistory
from database import db

logger = logging.getLogger(__name__)

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
user_bp = Blueprint('user', __name__, url_prefix='/api/user')
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# 用于存储state参数（防CSRF）
_state_storage = {}


# ==================== 认证API（公共） ====================

@auth_bp.route('/feishu/login', methods=['POST'])
def feishu_login():
    """
    生成飞书登录URL
    
    POST /api/auth/feishu/login
    {
        "redirect_uri": "http://localhost:5001/" (可选)
    }
    """
    try:
        data = request.get_json() or {}
        redirect_uri = data.get('redirect_uri') or os.getenv('FEISHU_REDIRECT_URI', 
                                                               'http://localhost:5001/api/auth/feishu/callback')
        
        # 生成随机state参数
        state = secrets.token_urlsafe(32)
        _state_storage[state] = {
            'timestamp': datetime.now(),
            'redirect_uri': data.get('final_redirect', '/')
        }
        
        # 获取飞书登录URL
        feishu_auth = get_feishu_auth()
        login_url = feishu_auth.get_login_url(redirect_uri, state)
        
        logger.info(f"生成飞书登录URL成功 - state: {state[:8]}...")
        
        return jsonify({
            'success': True,
            'login_url': login_url,
            'state': state
        })
        
    except Exception as e:
        logger.error(f"生成飞书登录URL失败: {e}")
        return jsonify({
            'success': False,
            'message': f'生成登录URL失败: {str(e)}'
        }), 500


@auth_bp.route('/feishu/callback', methods=['GET'])
def feishu_callback():
    """
    飞书OAuth2.0回调处理
    
    GET /api/auth/feishu/callback?code=xxx&state=xxx
    """
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        
        if not code or not state:
            logger.error("回调参数缺失")
            return redirect('/?error=missing_params')
        
        # 验证state参数
        if state not in _state_storage:
            logger.error(f"无效的state参数: {state[:8]}...")
            return redirect('/?error=invalid_state')
        
        state_data = _state_storage.pop(state)
        final_redirect = state_data.get('redirect_uri', '/')
        
        # 获取用户信息
        feishu_auth = get_feishu_auth()
        user_info = feishu_auth.complete_login_flow(code)
        
        # 提取用户信息
        feishu_id = user_info.get('user_id') or user_info.get('open_id')
        name = user_info.get('name', '未知用户')
        email = user_info.get('email')
        mobile = user_info.get('mobile')
        avatar_url = user_info.get('avatar_url')
        
        if not feishu_id:
            logger.error("无法获取飞书用户ID")
            return redirect('/?error=no_user_id')
        
        # 查询或创建用户
        user = AuthUser.query.filter_by(feishu_id=feishu_id).first()
        
        if user:
            # 更新用户信息
            user.name = name
            user.email = email
            user.mobile = mobile
            user.avatar_url = avatar_url
            user.last_login_at = datetime.now()
            user.last_login_ip = request.remote_addr
            user.login_count += 1
            logger.info(f"用户登录 - {name} ({feishu_id})")
        else:
            # 创建新用户（标记为"内部"）
            user = AuthUser(
                feishu_id=feishu_id,
                feishu_union_id=user_info.get('union_id'),
                feishu_open_id=user_info.get('open_id'),
                name=name,
                email=email,
                mobile=mobile,
                avatar_url=avatar_url,
                user_type='内部',  # 飞书登录用户标记为"内部"
                role='user',
                status='active',
                last_login_at=datetime.now(),
                last_login_ip=request.remote_addr,
                login_count=1
            )
            db.session.add(user)
            logger.info(f"新用户注册 - {name} ({feishu_id})")
        
        db.session.commit()
        
        # 记录登录历史
        login_history = LoginHistory(
            user_id=user.id,
            login_type='feishu',
            status='success',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            login_time=datetime.now()
        )
        db.session.add(login_history)
        db.session.commit()
        
        # 生成JWT token
        token = generate_token(user.id, user.role)
        
        # 重定向到前端页面，带上token
        redirect_url = f"{final_redirect}?token={token}"
        logger.info(f"登录成功，重定向到: {redirect_url}")
        
        return redirect(redirect_url)
        
    except Exception as e:
        logger.error(f"飞书回调处理失败: {e}")
        import traceback
        traceback.print_exc()
        return redirect('/?error=callback_failed')


@auth_bp.route('/user-info', methods=['GET'])
@login_required
def get_user_info():
    """
    获取当前用户基本信息
    
    GET /api/auth/user-info
    Header: Authorization: Bearer <token>
    """
    try:
        user = get_current_user()
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'avatar_url': user.avatar_url,
                'department': user.department,
                'role': user.role,
                'user_type': user.user_type,
                'status': user.status
            }
        })
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取用户信息失败: {str(e)}'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    退出登录
    
    POST /api/auth/logout
    Header: Authorization: Bearer <token>
    """
    try:
        user = get_current_user()
        logger.info(f"用户退出登录 - user_id: {user.id}, name: {user.name}")
        
        # 这里可以将token加入黑名单（如果实现了token黑名单机制）
        # TODO: 实现token黑名单
        
        return jsonify({
            'success': True,
            'message': '退出成功'
        })
        
    except Exception as e:
        logger.error(f"退出登录失败: {e}")
        return jsonify({
            'success': False,
            'message': f'退出登录失败: {str(e)}'
        }), 500


@auth_bp.route('/log-access', methods=['POST'])
@login_required
def log_access():
    """
    记录页面访问日志
    
    POST /api/auth/log-access
    {
        "page_url": "http://localhost:5001/",
        "page_title": "首页"
    }
    """
    try:
        user = get_current_user()
        data = request.get_json()
        
        access_log = AccessLog(
            user_id=user.id,
            username=user.name,
            page_url=data.get('page_url'),
            page_title=data.get('page_title'),
            http_method='GET',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            referer=request.headers.get('Referer'),
            access_time=datetime.now()
        )
        
        db.session.add(access_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '访问日志记录成功'
        })
        
    except Exception as e:
        logger.error(f"记录访问日志失败: {e}")
        return jsonify({
            'success': False,
            'message': f'记录访问日志失败: {str(e)}'
        }), 500


# ==================== 用户端API（个人中心） ====================

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """获取个人详细信息"""
    try:
        user = get_current_user()
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
    except Exception as e:
        logger.error(f"获取个人信息失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取个人信息失败: {str(e)}'
        }), 500


@user_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """更新个人信息（仅限部分字段）"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        # 只允许修改特定字段
        allowed_fields = ['email', 'mobile', 'avatar_url']
        
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        user.updated_at = datetime.now()
        db.session.commit()
        
        logger.info(f"用户更新个人信息 - user_id: {user.id}")
        
        return jsonify({
            'success': True,
            'message': '个人信息更新成功',
            'user': user.to_dict()
        })
        
    except Exception as e:
        logger.error(f"更新个人信息失败: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新个人信息失败: {str(e)}'
        }), 500


@user_bp.route('/login-history', methods=['GET'])
@login_required
def get_login_history():
    """获取个人登录历史"""
    try:
        user = get_current_user()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 查询当前用户的登录历史
        query = LoginHistory.query.filter_by(user_id=user.id)
        pagination = query.order_by(LoginHistory.login_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'history': [h.to_dict() for h in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages
        })
        
    except Exception as e:
        logger.error(f"获取登录历史失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取登录历史失败: {str(e)}'
        }), 500


@user_bp.route('/access-logs', methods=['GET'])
@login_required
def get_access_logs():
    """获取个人访问日志"""
    try:
        user = get_current_user()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        start_date = request.args.get('start_date')
        
        # 查询当前用户的访问日志
        query = AccessLog.query.filter_by(user_id=user.id)
        
        # 日期筛选
        if start_date:
            query = query.filter(AccessLog.access_time >= start_date)
        
        pagination = query.order_by(AccessLog.access_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'logs': [log.to_dict() for log in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages
        })
        
    except Exception as e:
        logger.error(f"获取访问日志失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取访问日志失败: {str(e)}'
        }), 500


@user_bp.route('/stats', methods=['GET'])
@login_required
def get_user_stats():
    """获取个人统计数据"""
    try:
        user = get_current_user()
        
        # 计算统计数据
        total_logins = user.login_count
        last_login = user.last_login_at
        total_access = AccessLog.query.filter_by(user_id=user.id).count()
        
        today = datetime.now().date()
        today_access = AccessLog.query.filter(
            AccessLog.user_id == user.id,
            func.date(AccessLog.access_time) == today
        ).count()
        
        # 最常访问的页面
        from sqlalchemy import func
        most_visited = db.session.query(
            AccessLog.page_url,
            func.count(AccessLog.id).label('count')
        ).filter_by(user_id=user.id).group_by(
            AccessLog.page_url
        ).order_by(func.count(AccessLog.id).desc()).first()
        
        # 账号年龄
        account_age = (datetime.now() - user.created_at).days
        
        return jsonify({
            'success': True,
            'stats': {
                'total_logins': total_logins,
                'last_login': last_login.isoformat() if last_login else None,
                'total_access': total_access,
                'today_access': today_access,
                'most_visited_page': most_visited[0] if most_visited else None,
                'account_age_days': account_age
            }
        })
        
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取统计数据失败: {str(e)}'
        }), 500


# ==================== 管理端API ====================

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """管理员登录（用户名密码）"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            }), 400
        
        # 查询管理员
        admin = AdminUser.query.filter_by(username=username).first()
        
        if not admin:
            logger.warning(f"管理员不存在 - username: {username}")
            # 记录失败的登录历史
            login_history = LoginHistory(
                user_id=None,
                login_type='password',
                status='failed',
                failure_reason='用户不存在',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                login_time=datetime.now()
            )
            db.session.add(login_history)
            db.session.commit()
            
            return jsonify({
                'success': False,
                'message': '用户名或密码错误'
            }), 401
        
        # 验证密码
        if not check_password_hash(admin.password_hash, password):
            logger.warning(f"密码错误 - username: {username}")
            # 记录失败的登录历史
            login_history = LoginHistory(
                user_id=admin.id,
                login_type='password',
                status='failed',
                failure_reason='密码错误',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                login_time=datetime.now()
            )
            db.session.add(login_history)
            db.session.commit()
            
            return jsonify({
                'success': False,
                'message': '用户名或密码错误'
            }), 401
        
        # 检查状态
        if admin.status != 'active':
            logger.warning(f"管理员账号已被禁用 - username: {username}")
            return jsonify({
                'success': False,
                'message': '账号已被禁用'
            }), 403
        
        # 更新最后登录时间
        admin.last_login_at = datetime.now()
        db.session.commit()
        
        # 记录成功的登录历史
        login_history = LoginHistory(
            user_id=admin.id,
            login_type='password',
            status='success',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            login_time=datetime.now()
        )
        db.session.add(login_history)
        db.session.commit()
        
        # 生成JWT token
        token = generate_token(admin.id, admin.role)
        
        logger.info(f"管理员登录成功 - username: {username}")
        
        return jsonify({
            'success': True,
            'token': token,
            'admin': admin.to_dict()
        })
        
    except Exception as e:
        logger.error(f"管理员登录失败: {e}")
        return jsonify({
            'success': False,
            'message': f'登录失败: {str(e)}'
        }), 500


# 注意：由于篇幅限制，这里仅实现了核心API
# 其他管理端API（用户管理、日志查看等）将在后续补充

