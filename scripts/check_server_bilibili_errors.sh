#!/bin/bash
# 检查服务器上具身视频页面的错误日志

echo "=========================================="
echo "服务器B站页面错误检查"
echo "=========================================="
echo ""

APP_DIR="/srv/EmbodiedPulse2026"
cd "$APP_DIR"

echo "【1. 检查服务状态】"
echo "----------------------------------------"
systemctl status embodiedpulse --no-pager -l | head -20
echo ""

echo "【2. 检查systemd服务日志（最近50行）】"
echo "----------------------------------------"
journalctl -u embodiedpulse -n 50 --no-pager | tail -50
echo ""

echo "【3. 检查Flask应用日志文件】"
echo "----------------------------------------"
# 查找可能的日志文件
LOG_FILES=(
    "$APP_DIR/logs/app.log"
    "$APP_DIR/app.log"
    "$APP_DIR/flask.log"
    "/var/log/embodiedpulse/app.log"
    "/var/log/embodiedpulse/error.log"
)

for log_file in "${LOG_FILES[@]}"; do
    if [ -f "$log_file" ]; then
        echo "✅ 找到日志文件: $log_file"
        echo "最近50行（包含bilibili相关错误）:"
        grep -i "bilibili\|error\|exception\|traceback" "$log_file" | tail -50 || echo "  未找到相关错误"
        echo ""
    fi
done

echo "【4. 检查Gunicorn错误日志】"
echo "----------------------------------------"
# Gunicorn通常输出到stderr，会被systemd捕获
journalctl -u embodiedpulse -n 100 --no-pager | grep -i "error\|exception\|traceback\|bilibili" | tail -30
echo ""

echo "【5. 测试API端点】"
echo "----------------------------------------"
source venv/bin/activate

# 测试B站API端点
echo "测试 /api/bilibili/all 端点:"
python3 << 'EOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    from app import app
    with app.test_client() as client:
        response = client.get('/api/bilibili/all?force=1')
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            if data and data.get('success'):
                print(f"✅ API返回成功")
                print(f"   数据条数: {len(data.get('data', []))}")
            else:
                print(f"❌ API返回失败: {data.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"   响应: {response.data.decode('utf-8')[:500]}")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
EOF

echo ""
echo "【6. 检查数据库连接】"
echo "----------------------------------------"
python3 << 'EOF'
import sys
import os
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    from bilibili_models import BILIBILI_DATABASE_URL, get_bilibili_session, BilibiliUp, BilibiliVideo
    
    print(f"数据库URL: {BILIBILI_DATABASE_URL}")
    
    # 测试连接
    try:
        session = get_bilibili_session()
        up_count = session.query(BilibiliUp).count()
        video_count = session.query(BilibiliVideo).count()
        print(f"✅ 数据库连接成功")
        print(f"   UP主数量: {up_count}")
        print(f"   视频数量: {video_count}")
        session.close()
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
EOF

echo ""
echo "【7. 检查最近的Python错误】"
echo "----------------------------------------"
# 检查Python相关的错误
journalctl -u embodiedpulse --since "1 hour ago" --no-pager | grep -i "python\|traceback\|exception\|error" | tail -30
echo ""

echo "【8. 检查B站数据获取相关错误】"
echo "----------------------------------------"
journalctl -u embodiedpulse --since "24 hours ago" --no-pager | grep -i "bilibili\|fetch.*video\|get.*bilibili" | tail -30
echo ""

echo "【9. 检查完整的错误堆栈】"
echo "----------------------------------------"
journalctl -u embodiedpulse -n 200 --no-pager | grep -A 20 "Traceback\|Exception\|Error" | tail -50
echo ""

echo "=========================================="
echo "检查完成"
echo "=========================================="
echo ""
echo "如果发现错误，请查看上面的输出信息"

