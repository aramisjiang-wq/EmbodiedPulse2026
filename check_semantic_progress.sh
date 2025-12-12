#!/bin/bash
# 检查Semantic Scholar数据更新进度

PID_FILE="/tmp/semantic_scholar_update.pid"
LOG_FILE="/tmp/semantic_scholar_update.log"

echo "=========================================="
echo "Semantic Scholar数据更新进度"
echo "=========================================="
echo ""

# 检查任务状态
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "🟢 状态: 运行中 (PID: $PID)"
    else
        echo "🔴 状态: 已停止（PID文件存在但进程不存在）"
    fi
else
    echo "⚪ 状态: 未运行"
fi

echo ""

# 统计数据库状态
python3 << 'EOF'
from models import get_session, Paper
from sqlalchemy import func

session = get_session()

# 统计总数
total = session.query(Paper).count()
print(f"📊 论文总数: {total}")

# 统计有Semantic Scholar数据的论文数
with_semantic = session.query(Paper).filter(
    Paper.semantic_scholar_updated_at.isnot(None)
).count()
print(f"✅ 已有Semantic Scholar数据: {with_semantic} ({with_semantic/total*100:.1f}%)")

# 统计没有Semantic Scholar数据的论文数
without_semantic = total - with_semantic
print(f"❌ 缺少Semantic Scholar数据: {without_semantic} ({without_semantic/total*100:.1f}%)")

# 统计有引用数的论文数
with_citation = session.query(Paper).filter(
    Paper.citation_count.isnot(None),
    Paper.citation_count > 0
).count()
print(f"📈 有引用数的论文: {with_citation} ({with_citation/total*100:.1f}%)")

# 统计有机构信息的论文数
with_affiliation = session.query(Paper).filter(
    Paper.author_affiliations.isnot(None),
    Paper.author_affiliations != ''
).count()
print(f"🏢 有机构信息的论文: {with_affiliation} ({with_affiliation/total*100:.1f}%)")

session.close()

# 计算进度
if total > 0:
    progress = (with_semantic / total) * 100
    print(f"\n📊 总体进度: {progress:.1f}%")
    
    if without_semantic > 0:
        print(f"⏱️  预计剩余: 约 {without_semantic // 200} 批次（按200篇/批计算）")
EOF

echo ""

# 显示最近的日志
if [ -f "$LOG_FILE" ]; then
    echo "📝 最近日志（最后10行）："
    echo "----------------------------------------"
    tail -10 "$LOG_FILE"
    echo ""
    echo "📄 完整日志: $LOG_FILE"
    echo "   查看实时日志: tail -f $LOG_FILE"
else
    echo "ℹ️  日志文件不存在"
fi

echo ""







