# -*- coding: utf-8 -*-
"""
飞书OAuth2.0认证客户端
实现飞书登录流程
"""

import requests
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class FeishuAuth:
    """飞书OAuth2.0认证客户端"""
    
    def __init__(self, app_id: str = None, app_secret: str = None):
        """
        初始化飞书认证客户端
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
        """
        self.app_id = app_id or os.getenv('FEISHU_APP_ID')
        self.app_secret = app_secret or os.getenv('FEISHU_APP_SECRET')
        self.base_url = "https://open.feishu.cn/open-apis"
        
        if not self.app_id or not self.app_secret:
            raise ValueError("飞书App ID和App Secret未配置")
        
        logger.info(f"飞书认证客户端初始化成功 - App ID: {self.app_id[:8]}...")
    
    def get_app_access_token(self) -> str:
        """
        获取app_access_token（企业自建应用）
        
        Returns:
            app_access_token
            
        Raises:
            Exception: 获取失败时抛出异常
        """
        url = f"{self.base_url}/auth/v3/app_access_token/internal"
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 0:
                token = result.get("app_access_token")
                logger.info("成功获取app_access_token")
                return token
            else:
                error_msg = f"获取app_access_token失败: {result.get('msg', '未知错误')}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"请求飞书API失败: {e}")
            raise Exception(f"请求飞书API失败: {e}")
    
    def get_login_url(self, redirect_uri: str, state: str) -> str:
        """
        生成飞书OAuth2.0登录URL
        
        Args:
            redirect_uri: 回调地址
            state: 随机state参数（用于防CSRF）
            
        Returns:
            飞书登录URL
        """
        login_url = (
            f"https://open.feishu.cn/open-apis/authen/v1/authorize?"
            f"app_id={self.app_id}&"
            f"redirect_uri={redirect_uri}&"
            f"state={state}"
        )
        logger.info(f"生成飞书登录URL - redirect_uri: {redirect_uri}")
        return login_url
    
    def get_user_access_token(self, code: str) -> Dict:
        """
        使用code换取user_access_token
        
        Args:
            code: 飞书回调返回的code
            
        Returns:
            包含access_token、refresh_token等信息的字典
            
        Raises:
            Exception: 换取失败时抛出异常
        """
        url = f"{self.base_url}/authen/v1/access_token"
        
        try:
            # 获取app_access_token
            app_access_token = self.get_app_access_token()
            
            headers = {
                "Authorization": f"Bearer {app_access_token}",
                "Content-Type": "application/json"
            }
            data = {
                "grant_type": "authorization_code",
                "code": code
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 0:
                token_data = result.get("data", {})
                logger.info("成功获取user_access_token")
                return token_data
            else:
                error_msg = f"获取user_access_token失败: {result.get('msg', '未知错误')}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"请求飞书API失败: {e}")
            raise Exception(f"请求飞书API失败: {e}")
    
    def get_user_info(self, user_access_token: str) -> Dict:
        """
        获取用户信息
        
        Args:
            user_access_token: 用户访问令牌
            
        Returns:
            用户信息字典
            
        Raises:
            Exception: 获取失败时抛出异常
        """
        url = f"{self.base_url}/authen/v1/user_info"
        headers = {
            "Authorization": f"Bearer {user_access_token}"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 0:
                user_info = result.get("data", {})
                logger.info(f"成功获取用户信息 - user_id: {user_info.get('user_id', 'unknown')}")
                return user_info
            else:
                error_msg = f"获取用户信息失败: {result.get('msg', '未知错误')}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"请求飞书API失败: {e}")
            raise Exception(f"请求飞书API失败: {e}")
    
    def complete_login_flow(self, code: str) -> Dict:
        """
        完成登录流程（获取用户信息）
        
        Args:
            code: 飞书回调返回的code
            
        Returns:
            用户信息字典
        """
        try:
            # 1. 使用code换取user_access_token
            token_data = self.get_user_access_token(code)
            user_access_token = token_data.get("access_token")
            
            if not user_access_token:
                raise Exception("user_access_token为空")
            
            # 2. 使用user_access_token获取用户信息
            user_info = self.get_user_info(user_access_token)
            
            # 3. 整合数据
            user_info['access_token'] = user_access_token
            user_info['refresh_token'] = token_data.get("refresh_token")
            user_info['expires_in'] = token_data.get("expires_in")
            
            logger.info(f"完成登录流程 - 用户: {user_info.get('name', 'unknown')}")
            return user_info
            
        except Exception as e:
            logger.error(f"登录流程失败: {e}")
            raise
    
    def refresh_user_access_token(self, refresh_token: str) -> Dict:
        """
        刷新用户访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            新的token信息
        """
        url = f"{self.base_url}/authen/v1/refresh_access_token"
        
        try:
            app_access_token = self.get_app_access_token()
            
            headers = {
                "Authorization": f"Bearer {app_access_token}",
                "Content-Type": "application/json"
            }
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 0:
                token_data = result.get("data", {})
                logger.info("成功刷新user_access_token")
                return token_data
            else:
                error_msg = f"刷新user_access_token失败: {result.get('msg', '未知错误')}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"请求飞书API失败: {e}")
            raise Exception(f"请求飞书API失败: {e}")


# 全局实例
_feishu_auth_instance: Optional[FeishuAuth] = None


def get_feishu_auth() -> FeishuAuth:
    """
    获取飞书认证客户端单例
    
    Returns:
        FeishuAuth实例
    """
    global _feishu_auth_instance
    
    if _feishu_auth_instance is None:
        _feishu_auth_instance = FeishuAuth()
    
    return _feishu_auth_instance

