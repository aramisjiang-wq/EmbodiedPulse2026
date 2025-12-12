#!/bin/bash
# 重启Flask服务器的脚本

echo "正在查找运行在5001端口的进程..."

# 查找并杀死占用5001端口的进程
PID=$(lsof -ti:5001 2>/dev/null)
if [ ! -z "$PID" ]; then
    echo "找到进程 $PID，正在停止..."
    kill $PID
    sleep 2
    
    # 如果还没停止，强制杀死
    if kill -0 $PID 2>/dev/null; then
        echo "强制停止进程..."
        kill -9 $PID
    fi
    echo "✅ 服务器已停止"
else
    echo "未找到运行中的服务器"
fi

echo ""
echo "正在启动新服务器..."
python3 app.py







