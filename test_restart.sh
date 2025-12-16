#!/bin/bash
# 重启应用并自动测试

cd "$(dirname "$0")"

echo "===================================================="
echo "重启应用并自动测试"
echo "===================================================="

# 1. 停止旧进程
echo ""
echo "1. 停止旧进程..."
OLD_PIDS=$(ps aux | grep -E "python.*app.py|flask|gunicorn" | grep -v grep | awk '{print $2}')
if [ -n "$OLD_PIDS" ]; then
    echo "   找到进程: $OLD_PIDS"
    kill -9 $OLD_PIDS 2>/dev/null
    sleep 2
    echo "   ✅ 已停止"
else
    echo "   ℹ️  没有运行中的进程"
fi

# 2. 设置环境变量
echo ""
echo "2. 设置环境变量..."
export AUTO_FETCH_ENABLED=true
export AUTO_FETCH_SCHEDULE="0 * * * *"
echo "   ✅ AUTO_FETCH_ENABLED=true"
echo "   ✅ AUTO_FETCH_SCHEDULE=0 * * * *"

# 3. 检查依赖
echo ""
echo "3. 检查依赖..."
python3 -c "import apscheduler" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ APScheduler 已安装"
else
    echo "   ⚠️  APScheduler 未安装"
fi

# 4. 启动应用（后台运行）
echo ""
echo "4. 启动应用..."
python3 app.py > /tmp/embodied_pulse.log 2>&1 &
APP_PID=$!
echo "   应用PID: $APP_PID"
echo "   日志文件: /tmp/embodied_pulse.log"

# 5. 等待应用启动
echo ""
echo "5. 等待应用启动..."
for i in {1..10}; do
    sleep 1
    if curl -s http://localhost:5001/api/stats > /dev/null 2>&1; then
        echo "   ✅ 应用已启动 (等待了 ${i} 秒)"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "   ❌ 应用启动超时"
        exit 1
    fi
done

# 6. 测试API
echo ""
echo "6. 测试API..."
echo "   6.1 测试 /api/stats..."
STATS_RESPONSE=$(curl -s http://localhost:5001/api/stats)
if echo "$STATS_RESPONSE" | grep -q "success"; then
    echo "      ✅ /api/stats 正常"
else
    echo "      ❌ /api/stats 异常"
    echo "      $STATS_RESPONSE"
fi

echo "   6.2 测试 /api/fetch-status..."
FETCH_STATUS=$(curl -s http://localhost:5001/api/fetch-status)
if echo "$FETCH_STATUS" | grep -q "running\|message"; then
    echo "      ✅ /api/fetch-status 正常"
else
    echo "      ❌ /api/fetch-status 异常"
fi

# 7. 测试刷新按钮（触发抓取）
echo ""
echo "7. 测试刷新按钮（触发抓取）..."
FETCH_RESPONSE=$(curl -s -X POST http://localhost:5001/api/fetch \
    -H "Content-Type: application/json" \
    -d '{}')
if echo "$FETCH_RESPONSE" | grep -q "success"; then
    echo "      ✅ 抓取任务已启动"
    echo "      响应: $(echo $FETCH_RESPONSE | python3 -m json.tool | head -5)"
else
    echo "      ❌ 抓取任务启动失败"
    echo "      $FETCH_RESPONSE"
fi

# 8. 检查定时任务
echo ""
echo "8. 检查定时任务..."
sleep 2
if tail -50 /tmp/embodied_pulse.log | grep -q "定时任务\|scheduler\|APScheduler"; then
    echo "      ✅ 定时任务已配置"
else
    echo "      ⚠️  未检测到定时任务配置（可能需要检查日志）"
fi

# 9. 检查日期过滤
echo ""
echo "9. 检查日期过滤修复..."
if grep -q "days_back\|submittedDate\|查询日期范围" /tmp/embodied_pulse.log 2>/dev/null; then
    echo "      ✅ 日期过滤相关代码已加载"
else
    echo "      ℹ️  日期过滤将在抓取时生效"
fi

# 10. 总结
echo ""
echo "===================================================="
echo "测试完成"
echo "===================================================="
echo "应用PID: $APP_PID"
echo "日志文件: /tmp/embodied_pulse.log"
echo ""
echo "查看日志: tail -f /tmp/embodied_pulse.log"
echo "停止应用: kill $APP_PID"
echo "访问地址: http://localhost:5001"
echo "===================================================="

