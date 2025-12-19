#!/bin/bash
# 通过SSH远程检查服务器错误

SERVER_USER="${SERVER_USER:-root}"
SERVER_HOST="${SERVER_HOST:-your-server-ip}"

if [ "$SERVER_HOST" = "your-server-ip" ]; then
    echo "请设置服务器地址："
    echo "export SERVER_HOST=your-server-ip"
    echo "export SERVER_USER=root"
    echo ""
    echo "或直接运行："
    echo "SERVER_HOST=your-server-ip SERVER_USER=root $0"
    exit 1
fi

echo "=========================================="
echo "远程检查服务器B站页面错误"
echo "=========================================="
echo "服务器: ${SERVER_USER}@${SERVER_HOST}"
echo ""

# 将检查脚本上传到服务器并执行
ssh ${SERVER_USER}@${SERVER_HOST} << 'ENDSSH'
cd /srv/EmbodiedPulse2026

echo "【1. 检查服务状态】"
echo "----------------------------------------"
systemctl status embodiedpulse --no-pager -l | head -20
echo ""

echo "【2. 检查systemd服务日志（最近100行）】"
echo "----------------------------------------"
journalctl -u embodiedpulse -n 100 --no-pager | tail -100
echo ""

echo "【3. 检查最近的错误和异常】"
echo "----------------------------------------"
journalctl -u embodiedpulse --since "1 hour ago" --no-pager | grep -i "error\|exception\|traceback" | tail -50
echo ""

echo "【4. 检查B站相关错误】"
echo "----------------------------------------"
journalctl -u embodiedpulse --since "24 hours ago" --no-pager | grep -i "bilibili" | tail -30
echo ""

echo "【5. 测试API端点】"
echo "----------------------------------------"
source venv/bin/activate
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    from app import app
    with app.test_client() as client:
        print("测试 /api/bilibili/all 端点...")
        response = client.get('/api/bilibili/all?force=1')
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            if data and data.get('success'):
                print(f"✅ API返回成功")
                print(f"   数据条数: {len(data.get('data', []))}")
            else:
                print(f"❌ API返回失败")
                print(f"   错误: {data.get('error', '未知错误') if data else '无数据'}")
                if data:
                    print(f"   完整响应: {data}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            try:
                error_text = response.data.decode('utf-8')
                print(f"   响应内容: {error_text[:500]}")
            except:
                print(f"   响应数据: {response.data[:500]}")
                
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo ""
echo "【6. 检查数据库连接】"
echo "----------------------------------------"
python3 << 'PYEOF'
import sys
import os
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    from bilibili_models import BILIBILI_DATABASE_URL, get_bilibili_session, BilibiliUp, BilibiliVideo
    
    print(f"数据库URL: {BILIBILI_DATABASE_URL}")
    
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
PYEOF

echo ""
echo "【7. 检查完整的错误堆栈（最近200行）】"
echo "----------------------------------------"
journalctl -u embodiedpulse -n 200 --no-pager | grep -B 5 -A 20 "Traceback\|Exception\|Error" | tail -100
echo ""

ENDSSH

echo ""
echo "=========================================="
echo "远程检查完成"
echo "=========================================="

