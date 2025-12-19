# -*- coding: utf-8 -*-
"""
定时任务工具模块 - 提供重试机制和告警功能
安全设计：通过环境变量控制，不影响现有代码
"""

from functools import wraps
import time
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# 通过环境变量控制是否启用重试机制（默认关闭，确保安全）
RETRY_ENABLED = os.getenv('SCHEDULER_RETRY_ENABLED', 'false').lower() == 'true'

# 重试配置（可通过环境变量覆盖）
DEFAULT_MAX_RETRIES = int(os.getenv('SCHEDULER_MAX_RETRIES', '3'))
DEFAULT_RETRY_DELAY = int(os.getenv('SCHEDULER_RETRY_DELAY', '60'))
DEFAULT_BACKOFF_FACTOR = int(os.getenv('SCHEDULER_BACKOFF_FACTOR', '2'))


def retry_on_failure(max_retries=None, retry_delay=None, backoff_factor=None, alert_on_final_failure=True):
    """
    定时任务失败重试装饰器（安全版本）
    
    特点：
    1. 默认不启用，需要通过环境变量 SCHEDULER_RETRY_ENABLED=true 启用
    2. 不影响原有代码逻辑，只是增强
    3. 可以随时通过环境变量关闭
    
    Args:
        max_retries: 最大重试次数（默认从环境变量读取，或使用3）
        retry_delay: 初始重试延迟（秒，默认从环境变量读取，或使用60）
        backoff_factor: 退避因子（默认从环境变量读取，或使用2）
        alert_on_final_failure: 最终失败后是否发送告警（默认True）
    
    使用示例:
        @retry_on_failure(max_retries=3, retry_delay=60)
        def my_scheduled_task():
            # 任务代码
            pass
    """
    # 使用默认值或环境变量值
    max_retries = max_retries or DEFAULT_MAX_RETRIES
    retry_delay = retry_delay or DEFAULT_RETRY_DELAY
    backoff_factor = backoff_factor or DEFAULT_BACKOFF_FACTOR
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 如果重试机制未启用，直接执行原函数（保持原有行为）
            if not RETRY_ENABLED:
                return func(*args, **kwargs)
            
            # 重试机制已启用，执行带重试的逻辑
            last_exception = None
            task_name = func.__name__
            
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(f"✅ 定时任务 {task_name} 重试成功 (第 {attempt + 1} 次尝试)")
                    return result
                except Exception as e:
                    last_exception = e
                    error_msg = str(e)
                    
                    if attempt < max_retries:
                        delay = retry_delay * (backoff_factor ** attempt)
                        logger.warning(
                            f"⚠️  定时任务 {task_name} 失败 (尝试 {attempt + 1}/{max_retries + 1}): {error_msg}"
                        )
                        logger.info(f"⏳ 等待 {delay} 秒后重试...")
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"❌ 定时任务 {task_name} 失败，已重试 {max_retries} 次: {error_msg}"
                        )
                        import traceback
                        logger.error(traceback.format_exc())
                        
                        # 发送告警
                        if alert_on_final_failure:
                            send_task_failure_alert(task_name, error_msg, max_retries)
                        raise
            
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def send_task_failure_alert(task_name, error_msg, retry_count):
    """
    发送定时任务失败告警（安全版本）
    
    特点：
    1. 默认只记录日志，不发送外部告警
    2. 可以通过环境变量启用飞书/邮件告警
    3. 避免告警风暴
    
    Args:
        task_name: 任务名称
        error_msg: 错误信息
        retry_count: 重试次数
    """
    try:
        alert_message = (
            f"🚨 定时任务失败告警\n"
            f"任务名称: {task_name}\n"
            f"失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"重试次数: {retry_count}\n"
            f"错误信息: {error_msg[:500]}\n"  # 限制长度，避免日志过长
            f"请检查系统状态并及时处理。"
        )
        
        # 始终记录到日志
        logger.error(f"告警信息: {alert_message}")
        
        # 可选：发送飞书告警（需要配置环境变量）
        feishu_webhook = os.getenv('FEISHU_ALERT_WEBHOOK')
        if feishu_webhook:
            try:
                send_feishu_alert(alert_message)
            except Exception as e:
                logger.error(f"发送飞书告警失败: {e}")
        
        # 可选：发送邮件告警（需要配置环境变量）
        email_enabled = os.getenv('EMAIL_ALERT_ENABLED', 'false').lower() == 'true'
        if email_enabled:
            try:
                send_email_alert(task_name, error_msg, retry_count)
            except Exception as e:
                logger.error(f"发送邮件告警失败: {e}")
        
    except Exception as e:
        logger.error(f"发送告警失败: {e}")


def send_feishu_alert(message):
    """
    发送飞书告警（可选功能）
    
    需要配置环境变量：
    - FEISHU_ALERT_WEBHOOK: 飞书机器人Webhook地址
    """
    import requests
    
    webhook = os.getenv('FEISHU_ALERT_WEBHOOK')
    if not webhook:
        return
    
    try:
        payload = {
            "msg_type": "text",
            "content": {
                "text": message
            }
        }
        response = requests.post(webhook, json=payload, timeout=5)
        response.raise_for_status()
        logger.info("飞书告警发送成功")
    except Exception as e:
        logger.error(f"发送飞书告警失败: {e}")


def send_email_alert(task_name, error_msg, retry_count):
    """
    发送邮件告警（可选功能，需要实现）
    
    需要配置环境变量：
    - EMAIL_ALERT_ENABLED: true
    - EMAIL_SMTP_HOST: SMTP服务器
    - EMAIL_SMTP_PORT: SMTP端口
    - EMAIL_FROM: 发件人
    - EMAIL_TO: 收件人（多个用逗号分隔）
    """
    # TODO: 实现邮件发送逻辑
    # 可以使用 smtplib 或第三方库
    logger.info(f"邮件告警功能待实现: {task_name}")


def is_retry_enabled():
    """
    检查重试机制是否已启用
    
    Returns:
        bool: True表示已启用，False表示未启用
    """
    return RETRY_ENABLED


def get_retry_config():
    """
    获取当前重试配置
    
    Returns:
        dict: 重试配置信息
    """
    return {
        'enabled': RETRY_ENABLED,
        'max_retries': DEFAULT_MAX_RETRIES,
        'retry_delay': DEFAULT_RETRY_DELAY,
        'backoff_factor': DEFAULT_BACKOFF_FACTOR
    }

