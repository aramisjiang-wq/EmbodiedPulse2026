#!/bin/bash
# B站数据库配置检查脚本

echo "=== B站数据库配置检查 ==="
echo ""

# 1. 检查环境变量
echo "1. 环境变量检查"
echo "   BILIBILI_DATABASE_URL: $BILIBILI_DATABASE_URL"
echo ""

# 2. 检查.env文件
echo "2. .env文件检查"
if [ -f .env ]; then
    grep BILIBILI_DATABASE_URL .env || echo "   ⚠️  .env文件中未找到BILIBILI_DATABASE_URL"
else
    echo "   ⚠️  .env文件不存在"
fi
echo ""

# 3. 检查Python代码中的配置
echo "3. Python代码中的配置"
python3 << EOF
import os
import sys
sys.path.insert(0, os.getcwd())

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

from bilibili_models import BILIBILI_DATABASE_URL, get_bilibili_engine
print(f"   数据库URL: {BILIBILI_DATABASE_URL}")

if BILIBILI_DATABASE_URL.startswith('sqlite'):
    db_file = BILIBILI_DATABASE_URL.replace('sqlite:///', '').replace('sqlite:///', '')
    import os
    if os.path.isabs(db_file):
        print(f"   ✅ 使用绝对路径: {db_file}")
        if os.path.exists(db_file):
            size = os.path.getsize(db_file) / (1024 * 1024)
            mtime = os.path.getmtime(db_file)
            from datetime import datetime
            print(f"   文件大小: {size:.2f} MB")
            print(f"   修改时间: {datetime.fromtimestamp(mtime)}")
        else:
            print(f"   ❌ 数据库文件不存在")
    else:
        cwd = os.getcwd()
        abs_path = os.path.join(cwd, db_file)
        print(f"   ⚠️  使用相对路径: {db_file}")
        print(f"   实际路径: {abs_path}")
        if os.path.exists(abs_path):
            size = os.path.getsize(abs_path) / (1024 * 1024)
            mtime = os.path.getmtime(abs_path)
            from datetime import datetime
            print(f"   文件大小: {size:.2f} MB")
            print(f"   修改时间: {datetime.fromtimestamp(mtime)}")
        else:
            print(f"   ❌ 数据库文件不存在")
elif BILIBILI_DATABASE_URL.startswith('postgresql') or BILIBILI_DATABASE_URL.startswith('postgres'):
    print(f"   ✅ 使用PostgreSQL")
    try:
        engine = get_bilibili_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        print(f"   ✅ 数据库连接成功")
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {e}")
EOF

echo ""
echo "4. 查找所有bilibili.db文件"
find . -name "bilibili.db" -type f 2>/dev/null | head -10

