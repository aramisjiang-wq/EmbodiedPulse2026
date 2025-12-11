"""
Gunicorn配置文件
用于生产环境部署
"""
import multiprocessing
import os

# 服务器socket
# 支持从环境变量获取端口（Railway、Render等平台会自动设置PORT环境变量）
import os
port = os.getenv('PORT', '5001')
# 使用0.0.0.0以监听所有接口（云平台需要）
bind = f"0.0.0.0:{port}"
backlog = 2048

# Worker进程
# 公式: workers = (2 × CPU核心数) + 1
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# 日志
# 注意：需要确保日志目录存在且有写权限
accesslog = "-"  # 输出到stdout
errorlog = "-"   # 输出到stderr
loglevel = os.getenv("LOG_LEVEL", "info")

# 进程命名
proc_name = "robotics-arxiv"

# 环境变量
raw_env = [
    f"FLASK_ENV={os.getenv('FLASK_ENV', 'production')}",
    f"AUTO_FETCH_ENABLED={os.getenv('AUTO_FETCH_ENABLED', 'false')}",
    f"AUTO_FETCH_SCHEDULE={os.getenv('AUTO_FETCH_SCHEDULE', '0 * * * *')}",  # 默认每小时整点
    f"AUTO_FETCH_NEWS_SCHEDULE={os.getenv('AUTO_FETCH_NEWS_SCHEDULE', '0 * * * *')}",  # 默认每小时整点
    f"AUTO_FETCH_JOBS_SCHEDULE={os.getenv('AUTO_FETCH_JOBS_SCHEDULE', '0 * * * *')}",  # 默认每小时整点
    f"AUTO_FETCH_MAX_RESULTS={os.getenv('AUTO_FETCH_MAX_RESULTS', '100')}",  # 默认100篇
]

# 性能优化
preload_app = True
max_requests = 1000
max_requests_jitter = 50

# Gunicorn启动钩子 - 确保定时任务在应用加载后启动
def when_ready(server):
    """Gunicorn服务器就绪时调用（所有worker启动后）"""
    import logging
    logger = logging.getLogger('gunicorn.error')
    logger.info("=" * 60)
    logger.info("Gunicorn服务器已就绪，检查定时任务...")
    logger.info("=" * 60)
    
    # 导入app模块并启动定时任务
    try:
        from app import init_scheduler
        scheduler = init_scheduler()
        if scheduler:
            logger.info("✅ 定时任务调度器已在Gunicorn启动时初始化")
        else:
            logger.info("ℹ️  定时任务未启用（AUTO_FETCH_ENABLED=false）")
    except Exception as e:
        logger.error(f"❌ 启动定时任务失败: {e}")
        import traceback
        logger.error(traceback.format_exc())

def on_exit(server):
    """Gunicorn服务器退出时调用"""
    import logging
    logger = logging.getLogger('gunicorn.error')
    try:
        from app import scheduler
        if scheduler:
            scheduler.shutdown()
            logger.info("定时任务调度器已关闭")
    except:
        pass

