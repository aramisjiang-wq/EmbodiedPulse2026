#!/bin/bash
# 修复三大问题：论文数据、视频数据、登录验证

set -e

APP_DIR="/srv/EmbodiedPulse2026"

echo "============================================================"
echo "开始修复三大问题"
echo "============================================================"
echo ""

cd "$APP_DIR"

# 1. 修复论文数据问题
echo "============================================================"
echo "1. 修复论文数据：手动抓取12月17日的论文"
echo "============================================================"
echo ""

if [ -d "venv" ]; then
    venv/bin/python3 scripts/fix_paper_fetch_dec17.py
elif [ -d ".venv" ]; then
    .venv/bin/python3 scripts/fix_paper_fetch_dec17.py
else
    python3 scripts/fix_paper_fetch_dec17.py
fi

echo ""
echo "============================================================"
echo "2. 修复视频数据：重新抓取缺失的UP主视频"
echo "============================================================"
echo ""

# 创建临时脚本抓取缺失的UP主
cat > /tmp/fix_bilibili_videos.py << 'EOF'
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/srv/EmbodiedPulse2026')

from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from fetch_bilibili_data import fetch_and_save_up_data

session = get_bilibili_session()

# 找出视频数为0的UP主
ups_without_videos = []
for up in session.query(BilibiliUp).filter_by(is_active=True).all():
    video_count = session.query(BilibiliVideo).filter(
        BilibiliVideo.uid == up.uid,
        BilibiliVideo.is_deleted == False
    ).count()
    if video_count == 0:
        ups_without_videos.append(up)
        print(f"发现无视频的UP主: {up.name} (UID: {up.uid})")

print(f"\n共发现 {len(ups_without_videos)} 个UP主没有视频数据")
print("开始重新抓取...\n")

for up in ups_without_videos:
    try:
        print(f"正在抓取 {up.name} (UID: {up.uid})...")
        fetch_and_save_up_data(up.uid, video_count=100, delay_between_requests=3.0)
        print(f"✅ {up.name} 抓取完成\n")
    except Exception as e:
        print(f"❌ {up.name} 抓取失败: {e}\n")

session.close()
print("✅ 视频数据修复完成")
EOF

if [ -d "venv" ]; then
    venv/bin/python3 /tmp/fix_bilibili_videos.py
elif [ -d ".venv" ]; then
    .venv/bin/python3 /tmp/fix_bilibili_videos.py
else
    python3 /tmp/fix_bilibili_videos.py
fi

rm /tmp/fix_bilibili_videos.py

echo ""
echo "============================================================"
echo "3. 修复登录验证：添加版本号强制刷新"
echo "============================================================"
echo ""

# 在user_menu.js引用中添加版本号（通过修改模板）
# 这里我们创建一个修复脚本
cat > /tmp/fix_login_cache.sh << 'EOF'
#!/bin/bash
# 在HTML模板中为user_menu.js添加版本号

cd /srv/EmbodiedPulse2026

# 获取当前时间戳作为版本号
VERSION=$(date +%s)

# 替换index.html中的user_menu.js引用
sed -i "s|user_menu.js|user_menu.js?v=${VERSION}|g" templates/index.html

# 替换bilibili.html中的user_menu.js引用
sed -i "s|user_menu.js|user_menu.js?v=${VERSION}|g" templates/bilibili.html

echo "✅ 已为user_menu.js添加版本号: ${VERSION}"
EOF

bash /tmp/fix_login_cache.sh
rm /tmp/fix_login_cache.sh

echo ""
echo "============================================================"
echo "4. 重启服务"
echo "============================================================"
echo ""

systemctl restart embodiedpulse
sleep 3

if systemctl is-active --quiet embodiedpulse; then
    echo "✅ 服务重启成功"
else
    echo "❌ 服务启动失败"
    echo "查看日志: journalctl -u embodiedpulse -n 50"
    exit 1
fi

echo ""
echo "============================================================"
echo "✅ 修复完成！"
echo "============================================================"
echo ""
echo "📝 验证步骤:"
echo "  1. 清除浏览器缓存（Ctrl+Shift+R 或 Cmd+Shift+R）"
echo "  2. 访问 https://essay.gradmotion.com/ 应该会跳转到登录页"
echo "  3. 访问 https://essay.gradmotion.com/bilibili 应该会跳转到登录页"
echo "  4. 登录后检查论文和视频数据是否正常显示"
echo ""

