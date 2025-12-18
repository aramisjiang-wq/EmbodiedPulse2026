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
        
        # 自动检测当前协议（HTTP/HTTPS）并设置回调地址
        # 优先使用环境变量，如果没有则根据当前请求自动生成
        default_redirect = os.getenv('FEISHU_REDIRECT_URI')
        if not default_redirect:
            # 根据当前请求自动生成 HTTPS 回调地址
            scheme = 'https' if request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https' else 'http'
            host = request.headers.get('Host', 'localhost:5001')
            default_redirect = f"{scheme}://{host}/api/auth/feishu/callback"
        
        redirect_uri = data.get('redirect_uri') or default_redirect
        
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
            logger.error(f"回调参数缺失 - code: {code is not None}, state: {state is not None}")
            return redirect('/login?error=missing_params')
        
        # 验证state参数
        if state not in _state_storage:
            logger.error(f"无效的state参数: {state[:8]}... (存储的state数量: {len(_state_storage)})")
            # 清理过期的state（超过10分钟）
            now = datetime.now()
            expired_states = [s for s, data in _state_storage.items() 
                            if (now - data['timestamp']).total_seconds() > 600]
            for expired_state in expired_states:
                _state_storage.pop(expired_state, None)
            logger.warning(f"已清理 {len(expired_states)} 个过期的state")
            
            # 检查是否是过期导致的
            if expired_states:
                logger.info(f"可能是state过期导致，已清理 {len(expired_states)} 个过期state")
            
            return redirect('/login?error=invalid_state&reason=state_not_found')
        
        state_data = _state_storage.pop(state)
        final_redirect = state_data.get('redirect_uri', '/auth/callback')
        
        # 获取用户信息
        logger.info(f"开始处理飞书回调 - code: {code[:10]}..., state: {state[:8]}...")
        feishu_auth = get_feishu_auth()
        try:
            user_info = feishu_auth.complete_login_flow(code)
            logger.info(f"成功获取用户信息 - user_id: {user_info.get('user_id', 'unknown')}")
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}", exc_info=True)
            raise
        
        # 提取用户信息
        feishu_id = user_info.get('user_id') or user_info.get('open_id')
        name = user_info.get('name', '未知用户')
        email = user_info.get('email')
        mobile = user_info.get('mobile')
        avatar_url = user_info.get('avatar_url')
        
        if not feishu_id:
            logger.error(f"无法获取飞书用户ID - user_info keys: {list(user_info.keys())}")
            return redirect('/login?error=no_user_id')
        
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
        
        # 重定向到回调成功页面，带上token
        # 使用专门的 /auth/callback 页面来处理token保存和跳转
        redirect_url = f"/auth/callback?token={token}"
        logger.info(f"登录成功，重定向到: {redirect_url}")
        
        return redirect(redirect_url)
        
    except Exception as e:
        logger.error(f"飞书回调处理失败: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        # 根据错误类型返回更具体的错误信息
        error_msg = str(e).lower()
        logger.error(f"错误详情: {error_msg}")
        
        if 'app_access_token' in error_msg or 'app_id' in error_msg or 'app_secret' in error_msg:
            logger.error("飞书配置错误")
            return redirect('/login?error=feishu_config_error')
        elif 'code' in error_msg or 'invalid' in error_msg or 'expired' in error_msg:
            logger.error("飞书授权码无效或已过期")
            return redirect('/login?error=invalid_code')
        elif 'state' in error_msg:
            logger.error("State参数验证失败")
            return redirect('/login?error=invalid_state')
        else:
            logger.error(f"未知错误: {error_msg}")
            return redirect('/login?error=callback_failed')


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
        
        # ✅ 修复：检查user是否为None（虽然理论上不应该，但增加安全检查）
        if not user:
            logger.error("get_current_user()返回None，这不应该发生")
            return jsonify({
                'success': False,
                'message': '用户信息获取失败'
            }), 500
        
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
        
    except AttributeError as e:
        # ✅ 修复：捕获AttributeError（user为None时访问属性）
        logger.error(f"获取用户信息失败（AttributeError）: {e}")
        return jsonify({
            'success': False,
            'message': '用户信息获取失败：用户对象无效'
        }), 500
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}", exc_info=True)
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


@admin_bp.route('/profile', methods=['GET'])
@admin_required
def get_admin_profile():
    """
    获取管理员个人信息
    
    GET /api/admin/profile
    Header: Authorization: Bearer <token>
    """
    try:
        user = get_current_user()
        
        # 管理员信息
        user_data = {
            'id': user.id,
            'name': user.name,
            'role': user.role,
            'status': user.status
        }
        
        # 如果是admin_users表的管理员，返回username
        if hasattr(user, 'username'):
            user_data['username'] = user.username
            user_data['email'] = user.email
        # 如果是auth_users表的管理员（飞书登录的管理员）
        else:
            user_data['email'] = user.email
            user_data['feishu_id'] = user.feishu_id
        
        logger.info(f"获取管理员信息成功 - user_id: {user.id}")
        
        return jsonify({
            'success': True,
            'user': user_data
        })
        
    except Exception as e:
        logger.error(f"获取管理员信息失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取管理员信息失败: {str(e)}'
        }), 500


# ==================== 管理端API - 用户管理 ====================

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """
    获取用户列表（分页）
    
    GET /api/admin/users?page=1&per_page=20&search=&status=&role=
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '').strip()
        role_filter = request.args.get('role', '').strip()
        
        # 构建查询
        query = AuthUser.query
        
        # 搜索过滤
        if search:
            query = query.filter(
                (AuthUser.name.contains(search)) |
                (AuthUser.email.contains(search)) |
                (AuthUser.mobile.contains(search)) |
                (AuthUser.feishu_id.contains(search))
            )
        
        # 状态过滤
        if status_filter and status_filter in ['active', 'inactive', 'banned']:
            query = query.filter(AuthUser.status == status_filter)
        
        # 角色过滤
        if role_filter and role_filter in ['user', 'admin', 'super_admin']:
            query = query.filter(AuthUser.role == role_filter)
        
        # 排序
        query = query.order_by(AuthUser.created_at.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page,
            'per_page': pagination.per_page
        })
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取用户列表失败: {str(e)}'
        }), 500


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user_detail(user_id):
    """
    获取用户详情
    
    GET /api/admin/users/{user_id}
    """
    try:
        user = AuthUser.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        # 获取用户的登录历史（最近10条）
        login_history = LoginHistory.query.filter_by(user_id=user_id).order_by(
            LoginHistory.login_time.desc()
        ).limit(10).all()
        
        # 获取用户的访问统计
        total_access_count = AccessLog.query.filter_by(user_id=user_id).count()
        today_access_count = AccessLog.query.filter_by(user_id=user_id).filter(
            AccessLog.access_time >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'login_history': [h.to_dict() for h in login_history],
            'stats': {
                'total_access_count': total_access_count,
                'today_access_count': today_access_count,
                'login_count': len([h for h in login_history if h.status == 'success'])
            }
        })
        
    except Exception as e:
        logger.error(f"获取用户详情失败 (user_id={user_id}): {e}")
        return jsonify({
            'success': False,
            'message': f'获取用户详情失败: {str(e)}'
        }), 500


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """
    更新用户信息
    
    PUT /api/admin/users/{user_id}
    {
        "name": "新名字",
        "email": "new@example.com",
        "mobile": "13800138000",
        "department": "技术部",
        "role": "admin",
        "status": "active"
    }
    """
    try:
        user = AuthUser.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 获取当前管理员
        current_admin = get_current_user()
        
        # 可更新字段
        updatable_fields = ['name', 'email', 'mobile', 'department', 'status']
        
        # 只有超级管理员可以更新角色
        if current_admin.get('role') == 'super_admin':
            updatable_fields.append('role')
        
        # 更新字段
        updated_fields = []
        for field in updatable_fields:
            if field in data:
                setattr(user, field, data[field])
                updated_fields.append(field)
        
        if updated_fields:
            user.updated_at = datetime.now()
            db.session.commit()
            logger.info(f"用户信息已更新 - user_id: {user_id}, fields: {updated_fields}")
        
        return jsonify({
            'success': True,
            'message': '用户信息更新成功',
            'user': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新用户信息失败 (user_id={user_id}): {e}")
        return jsonify({
            'success': False,
            'message': f'更新用户信息失败: {str(e)}'
        }), 500


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@super_admin_required
def delete_user(user_id):
    """
    删除用户（仅超级管理员）
    
    DELETE /api/admin/users/{user_id}
    """
    try:
        user = AuthUser.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        # 不能删除超级管理员
        if user.role == 'super_admin':
            return jsonify({
                'success': False,
                'message': '不能删除超级管理员'
            }), 403
        
        db.session.delete(user)
        db.session.commit()
        
        logger.info(f"用户已删除 - user_id: {user_id}, name: {user.name}")
        
        return jsonify({
            'success': True,
            'message': '用户删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除用户失败 (user_id={user_id}): {e}")
        return jsonify({
            'success': False,
            'message': f'删除用户失败: {str(e)}'
        }), 500


@admin_bp.route('/users/batch', methods=['POST'])
@admin_required
def batch_update_users():
    """
    批量更新用户
    
    POST /api/admin/users/batch
    {
        "user_ids": [1, 2, 3],
        "action": "update_status" | "update_role" | "delete",
        "value": "active" | "admin" (根据action不同)
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        user_ids = data.get('user_ids', [])
        action = data.get('action')
        value = data.get('value')
        
        if not user_ids or not action:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        # 获取用户
        users = AuthUser.query.filter(AuthUser.id.in_(user_ids)).all()
        if not users:
            return jsonify({
                'success': False,
                'message': '未找到指定用户'
            }), 404
        
        current_admin = get_current_user()
        updated_count = 0
        
        if action == 'update_status':
            if value not in ['active', 'inactive', 'banned']:
                return jsonify({
                    'success': False,
                    'message': '无效的状态值'
                }), 400
            
            for user in users:
                if user.role != 'super_admin':  # 不能修改超级管理员状态
                    user.status = value
                    user.updated_at = datetime.now()
                    updated_count += 1
        
        elif action == 'update_role':
            # 只有超级管理员可以批量更新角色
            if current_admin.get('role') != 'super_admin':
                return jsonify({
                    'success': False,
                    'message': '权限不足'
                }), 403
            
            if value not in ['user', 'admin', 'super_admin']:
                return jsonify({
                    'success': False,
                    'message': '无效的角色值'
                }), 400
            
            for user in users:
                if user.role != 'super_admin':  # 不能修改超级管理员角色
                    user.role = value
                    user.updated_at = datetime.now()
                    updated_count += 1
        
        elif action == 'delete':
            # 只有超级管理员可以批量删除
            if current_admin.get('role') != 'super_admin':
                return jsonify({
                    'success': False,
                    'message': '权限不足'
                }), 403
            
            for user in users:
                if user.role != 'super_admin':  # 不能删除超级管理员
                    db.session.delete(user)
                    updated_count += 1
        else:
            return jsonify({
                'success': False,
                'message': '无效的操作类型'
            }), 400
        
        db.session.commit()
        logger.info(f"批量操作完成 - action: {action}, count: {updated_count}")
        
        return jsonify({
            'success': True,
            'message': f'批量操作成功，共处理 {updated_count} 个用户'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"批量操作失败: {e}")
        return jsonify({
            'success': False,
            'message': f'批量操作失败: {str(e)}'
        }), 500


# ==================== 管理端API - 日志管理 ====================

@admin_bp.route('/logs/login', methods=['GET'])
@admin_required
def get_login_logs():
    """
    获取登录日志
    
    GET /api/admin/logs/login?page=1&per_page=50&user_id=&status=&start_date=&end_date=
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        user_id = request.args.get('user_id', type=int)
        status_filter = request.args.get('status', '').strip()
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        
        # 构建查询
        query = LoginHistory.query
        
        # 用户过滤
        if user_id:
            query = query.filter(LoginHistory.user_id == user_id)
        
        # 状态过滤
        if status_filter and status_filter in ['success', 'failed']:
            query = query.filter(LoginHistory.status == status_filter)
        
        # 日期过滤
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(LoginHistory.login_time >= start_dt)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(LoginHistory.login_time <= end_dt)
            except ValueError:
                pass
        
        # 排序
        query = query.order_by(LoginHistory.login_time.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 构建结果（包含用户信息）
        results = []
        for log in pagination.items:
            log_dict = log.to_dict()
            if log.user_id:
                user = AuthUser.query.get(log.user_id)
                if user:
                    log_dict['user'] = {
                        'id': user.id,
                        'name': user.name,
                        'email': user.email
                    }
            results.append(log_dict)
        
        return jsonify({
            'success': True,
            'logs': results,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page,
            'per_page': pagination.per_page
        })
        
    except Exception as e:
        logger.error(f"获取登录日志失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取登录日志失败: {str(e)}'
        }), 500


@admin_bp.route('/logs/access', methods=['GET'])
@admin_required
def get_access_logs():
    """
    获取访问日志
    
    GET /api/admin/logs/access?page=1&per_page=50&user_id=&start_date=&end_date=
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        user_id = request.args.get('user_id', type=int)
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        
        # 构建查询
        query = AccessLog.query
        
        # 用户过滤
        if user_id:
            query = query.filter(AccessLog.user_id == user_id)
        
        # 日期过滤
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(AccessLog.access_time >= start_dt)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(AccessLog.access_time <= end_dt)
            except ValueError:
                pass
        
        # 排序
        query = query.order_by(AccessLog.access_time.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 构建结果（包含用户信息）
        results = []
        for log in pagination.items:
            log_dict = log.to_dict()
            if log.user_id:
                user = AuthUser.query.get(log.user_id)
                if user:
                    log_dict['user'] = {
                        'id': user.id,
                        'name': user.name,
                        'email': user.email
                    }
            results.append(log_dict)
        
        return jsonify({
            'success': True,
            'logs': results,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page,
            'per_page': pagination.per_page
        })
        
    except Exception as e:
        logger.error(f"获取访问日志失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取访问日志失败: {str(e)}'
        }), 500


# ==================== 管理端API - 统计数据 ====================

@admin_bp.route('/stats/overview', methods=['GET'])
@admin_required
def get_overview_stats():
    """
    获取全局统计概览
    
    GET /api/admin/stats/overview
    """
    try:
        from sqlalchemy import func, distinct
        from datetime import timedelta
        
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # 用户统计
        total_users = AuthUser.query.count()
        active_users = AuthUser.query.filter_by(status='active').count()
        new_users_today = AuthUser.query.filter(AuthUser.created_at >= today).count()
        new_users_week = AuthUser.query.filter(AuthUser.created_at >= week_ago).count()
        
        # 登录统计
        total_logins = LoginHistory.query.filter_by(status='success').count()
        logins_today = LoginHistory.query.filter(
            LoginHistory.status == 'success',
            LoginHistory.login_time >= today
        ).count()
        logins_week = LoginHistory.query.filter(
            LoginHistory.status == 'success',
            LoginHistory.login_time >= week_ago
        ).count()
        
        # 活跃用户统计
        active_users_today = db.session.query(distinct(LoginHistory.user_id)).filter(
            LoginHistory.login_time >= today
        ).count()
        active_users_week = db.session.query(distinct(LoginHistory.user_id)).filter(
            LoginHistory.login_time >= week_ago
        ).count()
        
        # 访问统计
        total_access = AccessLog.query.count()
        access_today = AccessLog.query.filter(AccessLog.access_time >= today).count()
        access_week = AccessLog.query.filter(AccessLog.access_time >= week_ago).count()
        
        # 用户类型分布
        user_type_stats = db.session.query(
            AuthUser.user_type,
            func.count(AuthUser.id)
        ).group_by(AuthUser.user_type).all()
        
        # 用户角色分布
        role_stats = db.session.query(
            AuthUser.role,
            func.count(AuthUser.id)
        ).group_by(AuthUser.role).all()
        
        return jsonify({
            'success': True,
            'stats': {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'new_today': new_users_today,
                    'new_week': new_users_week
                },
                'logins': {
                    'total': total_logins,
                    'today': logins_today,
                    'week': logins_week
                },
                'active_users': {
                    'today': active_users_today,
                    'week': active_users_week
                },
                'access': {
                    'total': total_access,
                    'today': access_today,
                    'week': access_week
                },
                'distribution': {
                    'user_type': {ut[0]: ut[1] for ut in user_type_stats},
                    'role': {r[0]: r[1] for r in role_stats}
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取统计概览失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取统计概览失败: {str(e)}'
        }), 500


@admin_bp.route('/stats/trends', methods=['GET'])
@admin_required
def get_trends_stats():
    """
    获取趋势统计数据
    
    GET /api/admin/stats/trends?days=30
    """
    try:
        from datetime import timedelta
        from sqlalchemy import func, cast, Date
        
        days = request.args.get('days', 30, type=int)
        if days > 365:
            days = 365  # 最多1年
        
        end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        start_date = end_date - timedelta(days=days-1)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 每日新增用户
        new_users_daily = db.session.query(
            cast(AuthUser.created_at, Date).label('date'),
            func.count(AuthUser.id).label('count')
        ).filter(
            AuthUser.created_at >= start_date,
            AuthUser.created_at <= end_date
        ).group_by(cast(AuthUser.created_at, Date)).all()
        
        # 每日登录次数
        logins_daily = db.session.query(
            cast(LoginHistory.login_time, Date).label('date'),
            func.count(LoginHistory.id).label('count')
        ).filter(
            LoginHistory.status == 'success',
            LoginHistory.login_time >= start_date,
            LoginHistory.login_time <= end_date
        ).group_by(cast(LoginHistory.login_time, Date)).all()
        
        # 每日活跃用户数
        active_users_daily = db.session.query(
            cast(LoginHistory.login_time, Date).label('date'),
            func.count(distinct(LoginHistory.user_id)).label('count')
        ).filter(
            LoginHistory.login_time >= start_date,
            LoginHistory.login_time <= end_date
        ).group_by(cast(LoginHistory.login_time, Date)).all()
        
        # 每日访问次数
        access_daily = db.session.query(
            cast(AccessLog.access_time, Date).label('date'),
            func.count(AccessLog.id).label('count')
        ).filter(
            AccessLog.access_time >= start_date,
            AccessLog.access_time <= end_date
        ).group_by(cast(AccessLog.access_time, Date)).all()
        
        # 格式化返回数据
        def format_daily_data(data):
            result = {}
            for item in data:
                date_str = item.date.strftime('%Y-%m-%d')
                result[date_str] = item.count
            return result
        
        return jsonify({
            'success': True,
            'trends': {
                'new_users': format_daily_data(new_users_daily),
                'logins': format_daily_data(logins_daily),
                'active_users': format_daily_data(active_users_daily),
                'access': format_daily_data(access_daily)
            },
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'days': days
            }
        })
        
    except Exception as e:
        logger.error(f"获取趋势统计失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取趋势统计失败: {str(e)}'
        }), 500


# ==================== 管理端API - 论文管理 ====================

@admin_bp.route('/papers', methods=['GET'])
@admin_required
def get_papers():
    """
    获取论文列表（分页、搜索、筛选）
    
    GET /api/admin/papers?page=1&per_page=20&search=&category=&date_from=&date_to=&min_citations=
    """
    try:
        from models import get_session, Paper
        from sqlalchemy import or_, func
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        category_filter = request.args.get('category', '').strip()
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()
        min_citations = request.args.get('min_citations', type=int)
        
        session = get_session()
        
        try:
            # 构建查询
            query = session.query(Paper)
            
            # 搜索过滤
            if search:
                query = query.filter(
                    or_(
                        Paper.title.contains(search),
                        Paper.authors.contains(search),
                        Paper.abstract.contains(search)
                    )
                )
            
            # 类别过滤
            if category_filter:
                query = query.filter(Paper.category == category_filter)
            
            # 日期范围过滤
            if date_from:
                try:
                    from datetime import datetime as dt
                    date_from_obj = dt.strptime(date_from, '%Y-%m-%d').date()
                    query = query.filter(Paper.publish_date >= date_from_obj)
                except:
                    pass
            
            if date_to:
                try:
                    from datetime import datetime as dt
                    date_to_obj = dt.strptime(date_to, '%Y-%m-%d').date()
                    query = query.filter(Paper.publish_date <= date_to_obj)
                except:
                    pass
            
            # 引用数过滤
            if min_citations is not None:
                query = query.filter(Paper.citation_count >= min_citations)
            
            # 排序（按发布日期倒序）
            query = query.order_by(Paper.publish_date.desc(), Paper.created_at.desc())
            
            # 分页
            total = query.count()
            papers = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return jsonify({
                'success': True,
                'papers': [paper.to_dict() for paper in papers],
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': (total + per_page - 1) // per_page
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"获取论文列表失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'获取论文列表失败: {str(e)}'
        }), 500


@admin_bp.route('/papers/<paper_id>', methods=['GET'])
@admin_required
def get_paper_detail(paper_id):
    """
    获取论文详情
    
    GET /api/admin/papers/{paper_id}
    """
    try:
        from models import get_session, Paper
        
        session = get_session()
        try:
            paper = session.query(Paper).filter_by(id=paper_id).first()
            if not paper:
                return jsonify({
                    'success': False,
                    'message': '论文不存在'
                }), 404
            
            return jsonify({
                'success': True,
                'paper': paper.to_dict()
            })
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"获取论文详情失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取论文详情失败: {str(e)}'
        }), 500


@admin_bp.route('/papers/<paper_id>', methods=['PUT'])
@admin_required
def update_paper(paper_id):
    """
    更新论文信息
    
    PUT /api/admin/papers/{paper_id}
    {
        "category": "Perception/3D Perception",
        "code_url": "https://github.com/...",
        "title": "修正后的标题"
    }
    """
    try:
        from models import get_session, Paper
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        session = get_session()
        try:
            paper = session.query(Paper).filter_by(id=paper_id).first()
            if not paper:
                return jsonify({
                    'success': False,
                    'message': '论文不存在'
                }), 404
            
            # 可更新字段
            if 'category' in data:
                paper.category = data['category']
            if 'code_url' in data:
                paper.code_url = data['code_url']
            if 'title' in data:
                paper.title = data['title']
            
            paper.updated_at = datetime.now()
            session.commit()
            
            logger.info(f"论文已更新 - paper_id: {paper_id}")
            
            return jsonify({
                'success': True,
                'message': '论文更新成功',
                'paper': paper.to_dict()
            })
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"更新论文失败: {e}")
        return jsonify({
            'success': False,
            'message': f'更新论文失败: {str(e)}'
        }), 500


@admin_bp.route('/papers/<paper_id>', methods=['DELETE'])
@admin_required
def delete_paper(paper_id):
    """
    删除论文
    
    DELETE /api/admin/papers/{paper_id}
    """
    try:
        from models import get_session, Paper
        
        session = get_session()
        try:
            paper = session.query(Paper).filter_by(id=paper_id).first()
            if not paper:
                return jsonify({
                    'success': False,
                    'message': '论文不存在'
                }), 404
            
            session.delete(paper)
            session.commit()
            
            logger.info(f"论文已删除 - paper_id: {paper_id}")
            
            return jsonify({
                'success': True,
                'message': '论文删除成功'
            })
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"删除论文失败: {e}")
        return jsonify({
            'success': False,
            'message': f'删除论文失败: {str(e)}'
        }), 500


@admin_bp.route('/papers/stats', methods=['GET'])
@admin_required
def get_papers_stats():
    """
    获取论文统计信息
    
    GET /api/admin/papers/stats
    """
    try:
        from models import get_session, Paper
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        session = get_session()
        try:
            # 总论文数
            total = session.query(func.count(Paper.id)).scalar()
            
            # 今日新增
            today = datetime.now().date()
            today_count = session.query(func.count(Paper.id)).filter(
                func.date(Paper.created_at) == today
            ).scalar()
            
            # 平均引用数
            avg_citations = session.query(func.avg(Paper.citation_count)).scalar() or 0
            
            # 类别数
            from sqlalchemy import distinct
            category_count = session.query(func.count(distinct(Paper.category))).scalar()
            
            return jsonify({
                'success': True,
                'stats': {
                    'total': total,
                    'today': today_count,
                    'avg_citations': round(float(avg_citations), 2),
                    'categories': category_count
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"获取论文统计失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取论文统计失败: {str(e)}'
        }), 500


# ==================== 管理端API - 视频管理 ====================

@admin_bp.route('/bilibili/ups', methods=['GET'])
@admin_required
def get_bilibili_ups():
    """
    获取UP主列表（分页、搜索、筛选）
    
    GET /api/admin/bilibili/ups?page=1&per_page=20&search=&is_active=
    """
    try:
        from bilibili_models import get_bilibili_session, BilibiliUp
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        is_active = request.args.get('is_active', '').strip()
        
        session = get_bilibili_session()
        
        try:
            # 构建查询
            query = session.query(BilibiliUp)
            
            # 搜索过滤
            if search:
                query = query.filter(BilibiliUp.name.contains(search))
            
            # 状态过滤
            if is_active == 'true':
                query = query.filter(BilibiliUp.is_active == True)
            elif is_active == 'false':
                query = query.filter(BilibiliUp.is_active == False)
            
            # 排序（按粉丝数倒序）
            query = query.order_by(BilibiliUp.fans.desc())
            
            # 分页
            total = query.count()
            ups = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return jsonify({
                'success': True,
                'ups': [up.to_dict() for up in ups],
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': (total + per_page - 1) // per_page
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"获取UP主列表失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'获取UP主列表失败: {str(e)}'
        }), 500


@admin_bp.route('/bilibili/videos', methods=['GET'])
@admin_required
def get_bilibili_videos():
    """
    获取视频列表（分页、搜索、筛选）
    
    GET /api/admin/bilibili/videos?page=1&per_page=20&search=&uid=&date_from=&date_to=&min_play=
    """
    try:
        from bilibili_models import get_bilibili_session, BilibiliVideo, BilibiliUp
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        uid = request.args.get('uid', type=int)
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()
        min_play = request.args.get('min_play', type=int)
        
        session = get_bilibili_session()
        
        try:
            # 构建查询（关联UP主表）
            query = session.query(BilibiliVideo, BilibiliUp).join(
                BilibiliUp, BilibiliVideo.uid == BilibiliUp.uid
            )
            
            # 搜索过滤
            if search:
                query = query.filter(
                    BilibiliVideo.title.contains(search)
                )
            
            # UP主过滤
            if uid:
                query = query.filter(BilibiliVideo.uid == uid)
            
            # 日期范围过滤
            if date_from:
                try:
                    from datetime import datetime as dt
                    date_from_obj = dt.strptime(date_from, '%Y-%m-%d')
                    query = query.filter(BilibiliVideo.pubdate >= date_from_obj)
                except:
                    pass
            
            if date_to:
                try:
                    from datetime import datetime as dt
                    date_to_obj = dt.strptime(date_to, '%Y-%m-%d')
                    query = query.filter(BilibiliVideo.pubdate <= date_to_obj)
                except:
                    pass
            
            # 播放量过滤
            if min_play is not None:
                query = query.filter(BilibiliVideo.play >= min_play)
            
            # 排序（按发布时间倒序）
            query = query.order_by(BilibiliVideo.pubdate.desc())
            
            # 分页
            total = query.count()
            results = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # 组装数据
            videos = []
            for video, up in results:
                video_dict = video.to_dict()
                video_dict['up_name'] = up.name
                videos.append(video_dict)
            
            return jsonify({
                'success': True,
                'videos': videos,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': (total + per_page - 1) // per_page
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"获取视频列表失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'获取视频列表失败: {str(e)}'
        }), 500


@admin_bp.route('/bilibili/ups/<int:uid>', methods=['GET'])
@admin_required
def get_bilibili_up_detail(uid):
    """
    获取UP主详情
    
    GET /api/admin/bilibili/ups/{uid}
    """
    try:
        from bilibili_models import get_bilibili_session, BilibiliUp
        
        session = get_bilibili_session()
        try:
            up = session.query(BilibiliUp).filter_by(uid=uid).first()
            if not up:
                return jsonify({
                    'success': False,
                    'message': 'UP主不存在'
                }), 404
            
            return jsonify({
                'success': True,
                'up': up.to_dict()
            })
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"获取UP主详情失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取UP主详情失败: {str(e)}'
        }), 500


@admin_bp.route('/bilibili/videos/<bvid>', methods=['GET'])
@admin_required
def get_bilibili_video_detail(bvid):
    """
    获取视频详情
    
    GET /api/admin/bilibili/videos/{bvid}
    """
    try:
        from bilibili_models import get_bilibili_session, BilibiliVideo, BilibiliUp
        
        session = get_bilibili_session()
        try:
            video = session.query(BilibiliVideo).filter_by(bvid=bvid).first()
            if not video:
                return jsonify({
                    'success': False,
                    'message': '视频不存在'
                }), 404
            
            # 获取UP主信息
            up = session.query(BilibiliUp).filter_by(uid=video.uid).first()
            
            video_dict = video.to_dict()
            if up:
                video_dict['up_name'] = up.name
            
            return jsonify({
                'success': True,
                'video': video_dict
            })
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"获取视频详情失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取视频详情失败: {str(e)}'
        }), 500


@admin_bp.route('/bilibili/stats', methods=['GET'])
@admin_required
def get_bilibili_stats():
    """
    获取视频统计信息
    
    GET /api/admin/bilibili/stats
    """
    try:
        from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        session = get_bilibili_session()
        try:
            # 总UP主数
            total_ups = session.query(func.count(BilibiliUp.uid)).scalar()
            
            # 总视频数
            total_videos = session.query(func.count(BilibiliVideo.bvid)).scalar()
            
            # 总播放量
            total_plays = session.query(func.sum(BilibiliVideo.play)).scalar() or 0
            
            # 今日新增视频数
            today = datetime.now().date()
            today_videos = session.query(func.count(BilibiliVideo.bvid)).filter(
                func.date(BilibiliVideo.created_at) == today
            ).scalar()
            
            return jsonify({
                'success': True,
                'stats': {
                    'total_ups': total_ups,
                    'total_videos': total_videos,
                    'total_plays': int(total_plays),
                    'today_videos': today_videos
                }
            })
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"获取视频统计失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取视频统计失败: {str(e)}'
        }), 500


# ==================== Phase 3 管理端API开发完成 ====================

