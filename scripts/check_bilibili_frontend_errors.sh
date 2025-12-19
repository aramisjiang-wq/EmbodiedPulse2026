#!/bin/bash
# 检查前端访问B站页面时的错误

echo "=========================================="
echo "B站前端页面错误检查"
echo "=========================================="
echo ""

APP_DIR="/srv/EmbodiedPulse2026"
cd "$APP_DIR"

echo "【1. 检查最近的HTTP请求日志】"
echo "----------------------------------------"
journalctl -u embodiedpulse --since "1 hour ago" --no-pager | grep -i "bilibili\|/api/bilibili" | tail -30
echo ""

echo "【2. 检查前端访问时的错误响应】"
echo "----------------------------------------"
journalctl -u embodiedpulse --since "1 hour ago" --no-pager | grep -E "GET.*bilibili|POST.*bilibili|500|404|400" | tail -30
echo ""

echo "【3. 测试前端页面路由】"
echo "----------------------------------------"
source venv/bin/activate
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    from app import app
    with app.test_client() as client:
        # 测试前端页面
        print("测试 /bilibili 页面...")
        response = client.get('/bilibili')
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ 页面返回成功")
            content = response.data.decode('utf-8')
            # 检查关键元素
            if 'bilibili' in content.lower():
                print(f"   ✅ 页面包含bilibili相关内容")
            if 'latest-video-title' in content:
                print(f"   ✅ 页面包含最新视频元素")
            if 'api/bilibili/all' in content:
                print(f"   ✅ 页面包含API调用")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"   响应: {response.data.decode('utf-8')[:500]}")
            
        # 测试API端点（模拟前端调用）
        print("\n测试 /api/bilibili/all 端点（模拟前端）...")
        response = client.get('/api/bilibili/all?force=1')
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            if data and data.get('success'):
                cards = data.get('data', [])
                print(f"✅ API返回成功")
                print(f"   UP主数量: {len(cards)}")
                
                # 检查数据格式
                if cards:
                    first_card = cards[0]
                    print(f"\n   第一条数据检查:")
                    print(f"   - user_info: {bool(first_card.get('user_info'))}")
                    print(f"   - videos: {len(first_card.get('videos', []))}")
                    
                    # 检查逐际动力的数据
                    limx_card = next((c for c in cards if c.get('user_info', {}).get('mid') == 1172054289), None)
                    if limx_card:
                        print(f"\n   ✅ 找到逐际动力数据")
                        videos = limx_card.get('videos', [])
                        print(f"   - 视频数量: {len(videos)}")
                        if videos:
                            latest = videos[0]
                            print(f"   - 最新视频: {latest.get('title', 'N/A')[:50]}")
                            print(f"   - 播放量: {latest.get('play', 'N/A')}")
                    else:
                        print(f"\n   ❌ 未找到逐际动力数据")
            else:
                print(f"❌ API返回失败: {data.get('error', '未知错误') if data else '无数据'}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo ""
echo "【4. 检查Nginx配置（如果使用）】"
echo "----------------------------------------"
if [ -f /etc/nginx/sites-available/embodiedpulse ] || [ -f /etc/nginx/conf.d/embodiedpulse.conf ]; then
    echo "找到Nginx配置文件"
    grep -i "bilibili\|/api/bilibili" /etc/nginx/sites-available/embodiedpulse /etc/nginx/conf.d/embodiedpulse.conf 2>/dev/null || echo "未找到相关配置"
else
    echo "未找到Nginx配置文件"
fi
echo ""

echo "【5. 检查实时访问日志】"
echo "----------------------------------------"
echo "请在前端访问 https://essay.gradmotion.com/bilibili"
echo "然后查看以下日志（按Ctrl+C停止）:"
echo ""
journalctl -u embodiedpulse -f --no-pager | grep -i "bilibili\|/api/bilibili\|error\|exception"

