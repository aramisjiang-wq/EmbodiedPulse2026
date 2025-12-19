#!/bin/bash
# B站API测试脚本

echo "=== B站API测试 ==="
echo ""

BASE_URL="${BASE_URL:-http://localhost:5001}"

# 1. 测试前端API
echo "1. 测试 /api/bilibili/all"
echo "   请求: ${BASE_URL}/api/bilibili/all?force=1"
echo ""

response=$(curl -s "${BASE_URL}/api/bilibili/all?force=1")
echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        print(f\"   ✅ 成功: 返回 {len(data.get('data', []))} 个UP主\")
        if data.get('data'):
            first = data['data'][0]
            up_name = first.get('user_info', {}).get('name', '未知')
            print(f\"   第一个UP主: {up_name}\")
            videos = first.get('videos', [])
            if videos:
                print(f\"   视频数: {len(videos)}\")
                first_video = videos[0]
                print(f\"   第一个视频: {first_video.get('title', '')[:40]}\")
                print(f\"   播放量: {first_video.get('play')} (原始: {first_video.get('play_raw')})\")
            else:
                print(f\"   ⚠️  该UP主没有视频\")
        print(f\"   更新时间: {data.get('updated_at', '未知')}\")
    else:
        print(f\"   ❌ 失败: {data.get('message', '未知错误')}\")
except Exception as e:
    print(f\"   ❌ 解析失败: {e}\")
    print(f\"   原始响应: {sys.stdin.read()[:200]}\")
"

echo ""
echo "2. 测试管理后台API（需要token）"
echo "   请手动测试:"
echo "   curl -H 'Authorization: Bearer YOUR_TOKEN' ${BASE_URL}/api/admin/bilibili/videos?page=1&per_page=10"
echo ""

# 3. 检查API响应时间
echo "3. API响应时间测试"
time curl -s -o /dev/null "${BASE_URL}/api/bilibili/all?force=1"

