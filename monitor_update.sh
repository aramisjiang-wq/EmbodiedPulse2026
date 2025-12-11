#!/bin/bash
# 实时监控Semantic Scholar数据更新进度

echo "============================================================"
echo "Semantic Scholar数据更新监控"
echo "============================================================"
echo ""

while true; do
    clear
    echo "============================================================"
    echo "Semantic Scholar数据更新进度（实时监控）"
    echo "============================================================"
    echo ""
    
    # 检查更新脚本是否在运行
    if [ -f /tmp/semantic_scholar_update.pid ]; then
        PID=$(cat /tmp/semantic_scholar_update.pid)
        if ps -p $PID > /dev/null 2>&1; then
            echo "✅ 更新任务正在运行 (PID: $PID)"
        else
            echo "❌ 更新任务已停止"
        fi
    else
        echo "⚠️  未找到更新任务PID文件"
    fi
    
    echo ""
    echo "数据库统计:"
    python3 check_update_progress.py
    
    echo ""
    echo "最新日志（最后5行）:"
    tail -5 /tmp/semantic_scholar_update.log 2>/dev/null || echo "日志文件不存在"
    
    echo ""
    echo "按 Ctrl+C 退出监控"
    echo "============================================================"
    
    sleep 5
done


