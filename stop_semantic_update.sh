#!/bin/bash
# 停止Semantic Scholar数据更新任务

PID_FILE="/tmp/semantic_scholar_update.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "ℹ️  没有运行中的更新任务"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ps -p "$PID" > /dev/null 2>&1; then
    echo "🛑 正在停止更新任务 (PID: $PID)..."
    kill "$PID"
    
    # 等待进程结束
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    # 如果还在运行，强制终止
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "⚠️  进程未正常结束，强制终止..."
        kill -9 "$PID"
    fi
    
    rm -f "$PID_FILE"
    echo "✅ 更新任务已停止"
else
    echo "ℹ️  进程不存在，清理PID文件..."
    rm -f "$PID_FILE"
fi

# 停止所有相关的Python进程（可选，谨慎使用）
# pkill -f "update_semantic_scholar_data.py"







