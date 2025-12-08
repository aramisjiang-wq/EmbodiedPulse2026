"""
Gunicorn配置文件
用于生产环境部署
"""
import multiprocessing
import os

# 服务器socket
bind = "127.0.0.1:5001"
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
    f"AUTO_FETCH_SCHEDULE={os.getenv('AUTO_FETCH_SCHEDULE', '0 2 * * *')}",
    f"AUTO_FETCH_MAX_RESULTS={os.getenv('AUTO_FETCH_MAX_RESULTS', '10')}",
]

# 性能优化
preload_app = True
max_requests = 1000
max_requests_jitter = 50

