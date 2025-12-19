#!/bin/bash
# 清除B站数据缓存并重启服务

echo "=========================================="
echo "清除B站数据缓存"
echo "=========================================="
echo ""

APP_DIR="/srv/EmbodiedPulse2026"
cd "$APP_DIR"

source venv/bin/activate

echo "1. 清除Python缓存..."
python3 << 'EOF'
import sys
import os
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    import app
    
    with app.bilibili_cache_lock:
        app.bilibili_cache['all_data'] = None
        app.bilibili_cache['all_expires_at'] = None
        app.bilibili_cache['data'] = None
        app.bilibili_cache['expires_at'] = None
        print("✅ 缓存已清除")
except Exception as e:
    print(f"❌ 清除缓存失败: {e}")
    import traceback
    traceback.print_exc()
EOF

echo ""
echo "2. 重启服务..."
systemctl restart embodiedpulse

echo ""
echo "3. 等待服务启动..."
sleep 3

echo ""
echo "4. 检查服务状态..."
systemctl status embodiedpulse --no-pager -l | head -10

echo ""
echo "=========================================="
echo "完成"
echo "=========================================="
echo ""
echo "现在可以："
echo "1. 访问: https://essay.gradmotion.com/bilibili?force=1"
echo "2. 或在浏览器中强制刷新（Ctrl+F5）"

