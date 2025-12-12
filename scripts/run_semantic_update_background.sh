#!/bin/bash
# Semantic Scholar数据后台更新脚本
# 持续运行，自动补齐数据库中的Semantic Scholar数据

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/semantic_scholar_update.log"
PID_FILE="/tmp/semantic_scholar_update.pid"
BATCH_SIZE=200  # 每批更新的数量
DELAY_BETWEEN_BATCHES=300  # 批次之间的延迟（秒，5分钟）

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  更新任务已在运行中 (PID: $OLD_PID)"
        echo "   如需重启，请先运行: ./stop_semantic_update.sh"
        exit 1
    else
        echo "🧹 清理旧的PID文件..."
        rm -f "$PID_FILE"
    fi
fi

# 创建日志文件
touch "$LOG_FILE"

echo "=========================================="
echo "Semantic Scholar数据后台更新任务"
echo "=========================================="
echo "📋 配置信息："
echo "   - 批次大小: $BATCH_SIZE 篇/批"
echo "   - 批次间隔: $DELAY_BETWEEN_BATCHES 秒"
echo "   - 日志文件: $LOG_FILE"
echo "   - PID文件: $PID_FILE"
echo ""
echo "🚀 启动后台更新任务..."
echo ""

# 后台运行更新脚本
nohup python3 "$SCRIPT_DIR/update_semantic_scholar_data.py" \
    --limit "$BATCH_SIZE" \
    >> "$LOG_FILE" 2>&1 &

# 保存PID
echo $! > "$PID_FILE"
PID=$(cat "$PID_FILE")

echo "✅ 后台任务已启动 (PID: $PID)"
echo ""
echo "📊 查看进度："
echo "   tail -f $LOG_FILE"
echo ""
echo "🛑 停止任务："
echo "   ./stop_semantic_update.sh"
echo ""
echo "📈 查看统计："
echo "   ./check_semantic_progress.sh"
echo ""

# 启动持续更新循环（在后台）
(
    while true; do
        # 等待当前批次完成
        while ps -p "$PID" > /dev/null 2>&1; do
            sleep 10
        done
        
        # 检查是否还有需要更新的论文
        REMAINING=$(python3 -c "
from models import get_session, Paper
session = get_session()
total = session.query(Paper).count()
with_semantic = session.query(Paper).filter(
    Paper.semantic_scholar_updated_at.isnot(None)
).count()
without_semantic = total - with_semantic
session.close()
print(without_semantic)
" 2>/dev/null)
        
        if [ "$REMAINING" -gt 0 ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] 还有 $REMAINING 篇论文需要更新，继续下一批..." >> "$LOG_FILE"
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] 等待 $DELAY_BETWEEN_BATCHES 秒后继续..." >> "$LOG_FILE"
            sleep "$DELAY_BETWEEN_BATCHES"
            
            # 启动下一批
            nohup python3 "$SCRIPT_DIR/update_semantic_scholar_data.py" \
                --limit "$BATCH_SIZE" \
                >> "$LOG_FILE" 2>&1 &
            
            echo $! > "$PID_FILE"
            PID=$(cat "$PID_FILE")
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 所有论文的Semantic Scholar数据已补齐！" >> "$LOG_FILE"
            rm -f "$PID_FILE"
            break
        fi
    done
) &

echo "🔄 持续更新循环已启动"
echo "   系统将自动检测并持续更新，直到所有论文数据补齐"
echo ""







