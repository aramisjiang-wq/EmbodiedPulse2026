#!/bin/bash
# 在服务器上检查数据库连接配置

echo "=========================================="
echo "服务器数据库连接配置检查"
echo "=========================================="
echo ""

APP_DIR="/srv/EmbodiedPulse2026"
cd "$APP_DIR"

source venv/bin/activate

echo "【1. 检查环境变量】"
echo "----------------------------------------"
echo "系统环境变量BILIBILI_DATABASE_URL:"
echo "$BILIBILI_DATABASE_URL" || echo "未设置"
echo ""

echo ".env文件中的配置:"
if [ -f .env ]; then
    grep -E "^BILIBILI_DATABASE_URL=" .env | head -1 || echo "未在.env文件中找到"
else
    echo "❌ .env文件不存在"
fi
echo ""

echo "【2. 检查gunicorn配置】"
echo "----------------------------------------"
if [ -f gunicorn_config.py ]; then
    echo "gunicorn_config.py内容:"
    cat gunicorn_config.py | grep -E "chdir|bind|workers" || echo "未找到相关配置"
else
    echo "❌ gunicorn_config.py不存在"
fi
echo ""

echo "【3. 检查systemd服务配置】"
echo "----------------------------------------"
if [ -f /etc/systemd/system/embodiedpulse.service ]; then
    echo "WorkingDirectory:"
    systemctl show embodiedpulse | grep WorkingDirectory || echo "未设置"
    echo ""
    echo "Environment:"
    systemctl show embodiedpulse | grep Environment || echo "未设置环境变量"
else
    echo "❌ systemd服务文件不存在"
fi
echo ""

echo "【4. 检查实际数据库文件位置】"
echo "----------------------------------------"
echo "查找bilibili.db文件:"
find "$APP_DIR" -name "bilibili.db" -type f 2>/dev/null | while read file; do
    echo "  ✅ 找到: $file"
    ls -lh "$file" | awk '{print "     大小: " $5 ", 修改时间: " $6 " " $7 " " $8}'
done
echo ""

echo "检查相对路径数据库文件:"
if [ -f "$APP_DIR/bilibili.db" ]; then
    echo "  ✅ 找到: $APP_DIR/bilibili.db"
    ls -lh "$APP_DIR/bilibili.db" | awk '{print "     大小: " $5 ", 修改时间: " $6 " " $7 " " $8}'
else
    echo "  ⚠️  未找到: $APP_DIR/bilibili.db"
fi
echo ""

echo "【5. Python代码实际使用的数据库】"
echo "----------------------------------------"
python3 << 'EOF'
import os
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    from bilibili_models import BILIBILI_DATABASE_URL, get_bilibili_engine
    print(f"实际使用的数据库URL: {BILIBILI_DATABASE_URL}")
    
    if BILIBILI_DATABASE_URL.startswith('sqlite'):
        import os as os_module
        db_file = BILIBILI_DATABASE_URL.replace('sqlite:///', '').replace('sqlite:///', '')
        if os_module.path.isabs(db_file):
            print(f"   ✅ 绝对路径: {db_file}")
        else:
            cwd = os_module.getcwd()
            abs_path = os_module.path.join(cwd, db_file)
            print(f"   ⚠️  相对路径: {db_file}")
            print(f"   ⚠️  当前工作目录: {cwd}")
            print(f"   ⚠️  实际数据库文件路径: {abs_path}")
        
        if os_module.path.exists(db_file) or os_module.path.exists(abs_path):
            actual_path = db_file if os_module.path.isabs(db_file) else abs_path
            size = os_module.path.getsize(actual_path) / (1024 * 1024)
            print(f"   ✅ 数据库文件存在")
            print(f"   📁 文件路径: {actual_path}")
            print(f"   📊 文件大小: {size:.2f} MB")
        else:
            print(f"   ⚠️  数据库文件不存在")
    
    elif BILIBILI_DATABASE_URL.startswith('postgresql') or BILIBILI_DATABASE_URL.startswith('postgres'):
        from urllib.parse import urlparse
        parsed = urlparse(BILIBILI_DATABASE_URL)
        print(f"   ✅ 使用PostgreSQL")
        print(f"   📍 主机: {parsed.hostname}")
        print(f"   🔌 端口: {parsed.port or 5432}")
        print(f"   📚 数据库: {parsed.path.lstrip('/').split('?')[0]}")
        print(f"   👤 用户: {parsed.username}")
        
        # 测试连接
        try:
            engine = get_bilibili_engine()
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(text("SELECT current_database(), current_user"))
                row = result.fetchone()
                print(f"   ✅ 连接测试成功")
                print(f"   📊 当前数据库: {row[0]}")
                print(f"   👤 当前用户: {row[1]}")
        except Exception as e:
            print(f"   ❌ 连接测试失败: {e}")
    
except Exception as e:
    print(f"❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()
EOF

echo ""
echo "【6. 检查数据库中的数据】"
echo "----------------------------------------"
python3 << 'EOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
    
    session = get_bilibili_session()
    try:
        up_count = session.query(BilibiliUp).count()
        video_count = session.query(BilibiliVideo).count()
        
        print(f"UP主数量: {up_count}")
        print(f"视频数量: {video_count}")
        
        # 检查逐际动力的数据
        limx_up = session.query(BilibiliUp).filter_by(uid=1172054289).first()
        if limx_up:
            print(f"\n✅ 找到逐际动力:")
            print(f"   名称: {limx_up.name}")
            print(f"   视频数: {limx_up.videos_count}")
            print(f"   总播放量: {limx_up.views_count}")
            
            # 检查最新视频
            latest_video = session.query(BilibiliVideo).filter_by(
                uid=1172054289, is_deleted=False
            ).order_by(BilibiliVideo.pubdate.desc()).first()
            
            if latest_video:
                print(f"\n   最新视频:")
                print(f"   BV号: {latest_video.bvid}")
                print(f"   标题: {latest_video.title[:50]}...")
                print(f"   播放量: {latest_video.play:,}")
                print(f"   发布时间: {latest_video.pubdate}")
        else:
            print("\n❌ 未找到逐际动力数据")
    finally:
        session.close()
except Exception as e:
    print(f"❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()
EOF

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="

