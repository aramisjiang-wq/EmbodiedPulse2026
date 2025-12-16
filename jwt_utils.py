# -*- coding: utf-8 -*-
"""
JWT工具模块
用于生成和验证JWT token
"""

import jwt
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class JWTManager:
    """JWT管理器"""
    
    def __init__(self, secret_key: str = None, expires_hours: int = 24):
        """
        初始化JWT管理器
        
        Args:
            secret_key: JWT密钥
            expires_hours: token过期时间（小时）
        """
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this')
        self.expires_hours = expires_hours
        self.algorithm = 'HS256'
        
        if self.secret_key == 'your-secret-key-change-this':
            logger.warning("⚠️ JWT密钥使用默认值，生产环境请务必修改！")
    
    def generate_token(self, user_id: int, role: str = 'user', extra_data: Dict = None) -> str:
        """
        生成JWT token
        
        Args:
            user_id: 用户ID
            role: 用户角色
            extra_data: 额外数据（可选）
            
        Returns:
            JWT token字符串
        """
        try:
            # 基础payload
            payload = {
                'user_id': user_id,
                'role': role,
                'exp': datetime.utcnow() + timedelta(hours=self.expires_hours),
                'iat': datetime.utcnow(),
                'type': 'access'
            }
            
            # 添加额外数据
            if extra_data:
                payload.update(extra_data)
            
            # 生成token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.info(f"生成JWT token - user_id: {user_id}, role: {role}")
            return token
            
        except Exception as e:
            logger.error(f"生成JWT token失败: {e}")
            raise
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        验证JWT token
        
        Args:
            token: JWT token字符串
            
        Returns:
            验证成功返回payload字典，失败返回None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            logger.info(f"JWT token验证成功 - user_id: {payload.get('user_id')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token已过期")
            return None
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT token无效: {e}")
            return None
            
        except Exception as e:
            logger.error(f"验证JWT token时发生错误: {e}")
            return None
    
    def decode_token(self, token: str) -> Optional[Dict]:
        """
        解码JWT token（不验证有效性）
        
        Args:
            token: JWT token字符串
            
        Returns:
            payload字典，失败返回None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_signature": False})
            return payload
        except Exception as e:
            logger.error(f"解码JWT token失败: {e}")
            return None
    
    def refresh_token(self, old_token: str) -> Optional[str]:
        """
        刷新JWT token
        
        Args:
            old_token: 旧的JWT token
            
        Returns:
            新的JWT token，失败返回None
        """
        try:
            # 解码旧token（不验证有效性，因为可能已过期）
            payload = self.decode_token(old_token)
            
            if not payload:
                logger.warning("无法解码旧token")
                return None
            
            # 生成新token
            user_id = payload.get('user_id')
            role = payload.get('role', 'user')
            
            # 复制其他数据（除了exp、iat、type）
            extra_data = {k: v for k, v in payload.items() if k not in ['user_id', 'role', 'exp', 'iat', 'type']}
            
            new_token = self.generate_token(user_id, role, extra_data)
            logger.info(f"刷新JWT token成功 - user_id: {user_id}")
            return new_token
            
        except Exception as e:
            logger.error(f"刷新JWT token失败: {e}")
            return None
    
    def get_user_id_from_token(self, token: str) -> Optional[int]:
        """
        从token中提取user_id
        
        Args:
            token: JWT token字符串
            
        Returns:
            user_id，失败返回None
        """
        payload = self.verify_token(token)
        if payload:
            return payload.get('user_id')
        return None
    
    def get_role_from_token(self, token: str) -> Optional[str]:
        """
        从token中提取role
        
        Args:
            token: JWT token字符串
            
        Returns:
            role，失败返回None
        """
        payload = self.verify_token(token)
        if payload:
            return payload.get('role')
        return None
    
    def is_admin(self, token: str) -> bool:
        """
        判断token是否为管理员
        
        Args:
            token: JWT token字符串
            
        Returns:
            是否为管理员
        """
        role = self.get_role_from_token(token)
        return role in ['admin', 'super_admin']
    
    def is_super_admin(self, token: str) -> bool:
        """
        判断token是否为超级管理员
        
        Args:
            token: JWT token字符串
            
        Returns:
            是否为超级管理员
        """
        role = self.get_role_from_token(token)
        return role == 'super_admin'


# 全局实例
_jwt_manager_instance: Optional[JWTManager] = None


def get_jwt_manager() -> JWTManager:
    """
    获取JWT管理器单例
    
    Returns:
        JWTManager实例
    """
    global _jwt_manager_instance
    
    if _jwt_manager_instance is None:
        _jwt_manager_instance = JWTManager()
    
    return _jwt_manager_instance


# 便捷函数
def generate_token(user_id: int, role: str = 'user', extra_data: Dict = None) -> str:
    """生成JWT token"""
    return get_jwt_manager().generate_token(user_id, role, extra_data)


def verify_token(token: str) -> Optional[Dict]:
    """验证JWT token"""
    return get_jwt_manager().verify_token(token)


def get_user_id_from_token(token: str) -> Optional[int]:
    """从token中提取user_id"""
    return get_jwt_manager().get_user_id_from_token(token)


def is_admin(token: str) -> bool:
    """判断是否为管理员"""
    return get_jwt_manager().is_admin(token)


def is_super_admin(token: str) -> bool:
    """判断是否为超级管理员"""
    return get_jwt_manager().is_super_admin(token)

