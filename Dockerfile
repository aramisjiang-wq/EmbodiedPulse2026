# Dockerfile for Robotics ArXiv Daily
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 初始化数据库（如果不存在）
RUN python3 init_database.py || true

# 创建非root用户（安全考虑）
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 5001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:5001/api/stats', timeout=5)" || exit 1

# 启动命令
CMD ["gunicorn", "-c", "gunicorn_config.py", "app:app"]

