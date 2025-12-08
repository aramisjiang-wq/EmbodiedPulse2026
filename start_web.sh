#!/bin/bash
# 启动 Web 应用

echo "正在启动 Robotics ArXiv Daily Web 应用..."
echo "访问地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务器"
echo ""

cd "$(dirname "$0")"
python3 app.py

