#!/bin/bash
# 检查B站数据自动更新配置

echo "=== B站数据自动更新配置检查 ==="
echo ""

cd /srv/EmbodiedPulse2026

# 1. 检查环境变量配置
echo "1. 检查环境变量配置"
echo "=" * 80

if [ -f .env ]; then
    echo "✅ .env文件存在"
    
    # 检查 AUTO_FETCH_ENABLED
    if grep -q "^AUTO_FETCH_ENABLED" .env; then
        auto_fetch=$(grep "^AUTO_FETCH_ENABLED" .env | cut -d'=' -f2 | tr -d ' ')
        echo "   AUTO_FETCH_ENABLED: $auto_fetch"
        if [ "$auto_fetch" = "true" ]; then
            echo "   ✅ 定时任务已启用"
        else
            echo "   ⚠️  定时任务未启用（需要设置为 true）"
        fi
    else
        echo "   ⚠️  未找到 AUTO_FETCH_ENABLED 配置"
    fi
    
    # 检查 B站数据抓取定时任务
    if grep -q "^AUTO_FETCH_BILIBILI_SCHEDULE" .env; then
        bilibili_schedule=$(grep "^AUTO_FETCH_BILIBILI_SCHEDULE" .env | cut -d'=' -f2 | tr -d ' ')
        echo "   AUTO_FETCH_BILIBILI_SCHEDULE: $bilibili_schedule"
        echo "   ✅ B站数据抓取定时任务已配置"
    else
        echo "   ⚠️  未找到 AUTO_FETCH_BILIBILI_SCHEDULE 配置（默认每6小时执行）"
    fi
    
    # 检查播放量更新定时任务
    if grep -q "^AUTO_UPDATE_PLAY_COUNTS_SCHEDULE" .env; then
        play_schedule=$(grep "^AUTO_UPDATE_PLAY_COUNTS_SCHEDULE" .env | cut -d'=' -f2 | tr -d ' ')
        echo "   AUTO_UPDATE_PLAY_COUNTS_SCHEDULE: $play_schedule"
        echo "   ✅ 播放量更新定时任务已配置"
    else
        echo "   ⚠️  未找到 AUTO_UPDATE_PLAY_COUNTS_SCHEDULE 配置（默认每天2点执行）"
    fi
else
    echo "❌ .env文件不存在"
fi

echo ""
echo "2. 检查定时任务调度器状态"
echo "=" * 80

python3 << EOF
import os
import sys
sys.path.insert(0, os.getcwd())

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# 检查环境变量
auto_fetch_enabled = os.getenv('AUTO_FETCH_ENABLED', 'false').lower() == 'true'
bilibili_schedule = os.getenv('AUTO_FETCH_BILIBILI_SCHEDULE', '0 */6 * * *')
play_schedule = os.getenv('AUTO_UPDATE_PLAY_COUNTS_SCHEDULE', '0 2 * * *')

print(f"   AUTO_FETCH_ENABLED: {auto_fetch_enabled}")
print(f"   B站数据抓取计划: {bilibili_schedule} (每6小时执行一次)")
print(f"   播放量更新计划: {play_schedule} (每天2点执行)")

if auto_fetch_enabled:
    print("   ✅ 定时任务已启用")
    print("   ✅ B站数据会自动更新")
    print("   ✅ 播放量会自动更新")
else:
    print("   ⚠️  定时任务未启用")
    print("   ⚠️  需要设置 AUTO_FETCH_ENABLED=true")
EOF

echo ""
echo "3. 检查服务状态"
echo "=" * 80

if systemctl is-active --quiet embodiedpulse; then
    echo "   ✅ embodiedpulse 服务正在运行"
else
    echo "   ⚠️  embodiedpulse 服务未运行"
fi

echo ""
echo "4. 建议的配置"
echo "=" * 80
echo "   确保 .env 文件中包含以下配置："
echo "   AUTO_FETCH_ENABLED=true"
echo "   AUTO_FETCH_BILIBILI_SCHEDULE=0 */6 * * *"
echo "   AUTO_UPDATE_PLAY_COUNTS_SCHEDULE=0 2 * * *"
echo ""
echo "   然后重启服务："
echo "   systemctl restart embodiedpulse"

