#!/bin/bash
# 一键修复播放量显示问题

echo "=========================================="
echo "B站播放量显示问题一键修复"
echo "=========================================="
echo ""

cd /srv/EmbodiedPulse2026
source venv/bin/activate

echo "【步骤1: 备份原文件】"
echo "----------------------------------------"
cp app.py app.py.backup.$(date +%Y%m%d_%H%M%S)
cp bilibili_models.py bilibili_models.py.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ 备份完成"

echo ""
echo "【步骤2: 修复 app.py】"
echo "----------------------------------------"
# 检查是否已修复
if grep -q "format_number(video.play)" app.py; then
    echo "✅ app.py 已修复，跳过"
else
    # 修复 app.py 第1321行
    python3 << 'PYEOF'
import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 play 字段
old_pattern = r"'play':\s*video\.play_formatted\s+or\s+'0'"
new_pattern = "'play': format_number(video.play) if video.play else '0'"

if re.search(old_pattern, content):
    content = re.sub(old_pattern, new_pattern, content)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ app.py 已修复")
else:
    print("⚠️  未找到需要修复的代码，可能已修复或代码结构不同")
PYEOF
fi

echo ""
echo "【步骤3: 修复 bilibili_models.py】"
echo "----------------------------------------"
# 检查是否已修复
if grep -q "format_number(self.play)" bilibili_models.py; then
    echo "✅ bilibili_models.py 已修复，跳过"
else
    python3 << 'PYEOF'
import re

with open('bilibili_models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 添加 import（如果不存在）
if 'from bilibili_client import format_number' not in content:
    # 在文件开头添加import
    if 'from bilibili_client import' in content:
        # 如果已有其他import，添加到那一行
        content = re.sub(
            r'(from bilibili_client import[^\n]+)',
            r'\1, format_number',
            content
        )
    else:
        # 在import区域添加
        content = content.replace(
            'from sqlalchemy import create_engine',
            'from sqlalchemy import create_engine\nfrom bilibili_client import format_number'
        )

# 替换 play 字段
old_pattern = r"'play':\s*self\.play_formatted\s+or\s+'0'"
new_pattern = "'play': format_number(self.play) if self.play else '0'"

if re.search(old_pattern, content):
    content = re.sub(old_pattern, new_pattern, content)
    with open('bilibili_models.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ bilibili_models.py 已修复")
else:
    print("⚠️  未找到需要修复的代码，可能已修复或代码结构不同")
PYEOF
fi

echo ""
echo "【步骤4: 验证修复】"
echo "----------------------------------------"
echo "检查 app.py:"
if grep -q "format_number(video.play)" app.py; then
    echo "✅ app.py 修复成功"
else
    echo "❌ app.py 修复失败"
fi

echo "检查 bilibili_models.py:"
if grep -q "format_number(self.play)" bilibili_models.py; then
    echo "✅ bilibili_models.py 修复成功"
else
    echo "❌ bilibili_models.py 修复失败"
fi

echo ""
echo "【步骤5: 清除缓存】"
echo "----------------------------------------"
python3 << 'EOF'
import sys
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
    print(f"⚠️  清除缓存失败: {e}")
EOF

echo ""
echo "【步骤6: 重启服务】"
echo "----------------------------------------"
systemctl restart embodiedpulse
sleep 3
if systemctl is-active embodiedpulse > /dev/null 2>&1; then
    echo "✅ 服务重启成功"
    systemctl status embodiedpulse --no-pager -l | head -10
else
    echo "❌ 服务重启失败，请检查日志"
    journalctl -u embodiedpulse -n 20 --no-pager
fi

echo ""
echo "【步骤7: 测试API】"
echo "----------------------------------------"
python3 << 'PYEOF'
from app import app

with app.test_client() as client:
    response = client.get('/api/bilibili/all?force=1')
    data = response.get_json()
    if data and data.get('success'):
        cards = data.get('data', [])
        for card in cards:
            if card.get('user_info', {}).get('mid') == 1172054289:
                videos = card.get('videos', [])
                if videos:
                    latest = videos[0]
                    print(f"✅ API测试结果:")
                    print(f"   BV号: {latest.get('bvid')}")
                    print(f"   播放量(play): {latest.get('play')}")
                    print(f"   播放量原始(play_raw): {latest.get('play_raw')}")
                    if latest.get('play_raw') == 171419:
                        print("✅ 数据正确！")
                    else:
                        print(f"⚠️  数据: {latest.get('play_raw')}，期望: 171419")
                    break
    else:
        print(f"❌ API测试失败: {data}")
PYEOF

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="
echo ""
echo "请访问以下页面验证："
echo "1. https://essay.gradmotion.com/bilibili"
echo "2. https://admin123.gradmotion.com/admin/bilibili"
echo ""
echo "如果仍显示旧值，请："
echo "1. 强制刷新浏览器：Ctrl+Shift+R (Windows) 或 Cmd+Shift+R (Mac)"
echo "2. 清除浏览器缓存"
echo "3. 检查浏览器控制台的 Network 标签，查看 API 返回的数据"

