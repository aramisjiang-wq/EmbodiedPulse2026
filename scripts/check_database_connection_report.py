#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接检查报告
检查B站相关页面的数据库连接配置
"""

import os
import sys
from pathlib import Path

print("=" * 80)
print("数据库连接配置检查报告")
print("=" * 80)
print()
print("检查时间:", __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print()

# 1. 检查代码中的数据库配置
print("【1. 代码中的数据库配置】")
print("-" * 80)

# 读取 bilibili_models.py
bilibili_models_path = Path(__file__).parent.parent / 'bilibili_models.py'
if bilibili_models_path.exists():
    with open(bilibili_models_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'BILIBILI_DATABASE_URL = os.getenv' in content:
            # 提取默认值
            import re
            match = re.search(r"BILIBILI_DATABASE_URL = os\.getenv\('BILIBILI_DATABASE_URL', '([^']+)'\)", content)
            if match:
                default_db = match.group(1)
                print(f"✅ 默认数据库URL: {default_db}")
                if default_db.startswith('sqlite'):
                    print(f"   ⚠️  使用SQLite，路径为相对路径: {default_db}")
                    print(f"   ⚠️  相对路径会在当前工作目录下创建数据库文件")
                    print(f"   ⚠️  如果工作目录不同，会连接到不同的数据库文件")
                elif default_db.startswith('postgresql'):
                    print(f"   ✅ 使用PostgreSQL")
            else:
                print("❌ 无法解析默认数据库URL")
        else:
            print("❌ 未找到BILIBILI_DATABASE_URL配置")
else:
    print("❌ 未找到bilibili_models.py文件")

print()

# 2. 检查环境变量
print("【2. 环境变量配置】")
print("-" * 80)

# 检查本地.env文件
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    print(f"✅ 找到.env文件: {env_file}")
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        found_bilibili = False
        for line in lines:
            if line.strip().startswith('BILIBILI_DATABASE_URL'):
                found_bilibili = True
                # 隐藏密码
                db_url = line.split('=', 1)[1].strip() if '=' in line else ''
                if '@' in db_url:
                    # PostgreSQL格式，隐藏密码
                    parts = db_url.split('@')
                    user_part = parts[0].split('//')[1] if '//' in parts[0] else ''
                    if ':' in user_part:
                        user = user_part.split(':')[0]
                        print(f"   BILIBILI_DATABASE_URL: {db_url.split('@')[0].split('//')[0]}//{user}:***@{parts[1]}")
                    else:
                        print(f"   BILIBILI_DATABASE_URL: {db_url}")
                else:
                    print(f"   BILIBILI_DATABASE_URL: {db_url}")
        if not found_bilibili:
            print("   ⚠️  .env文件中未设置BILIBILI_DATABASE_URL")
            print("   ⚠️  将使用代码中的默认值: sqlite:///./bilibili.db")
else:
    print("❌ 未找到.env文件")
    print("   ⚠️  将使用代码中的默认值: sqlite:///./bilibili.db")

# 检查系统环境变量
bilibili_db_env = os.getenv('BILIBILI_DATABASE_URL')
if bilibili_db_env:
    print(f"✅ 系统环境变量BILIBILI_DATABASE_URL已设置")
    if '@' in bilibili_db_env:
        parts = bilibili_db_env.split('@')
        user_part = parts[0].split('//')[1] if '//' in parts[0] else ''
        if ':' in user_part:
            user = user_part.split(':')[0]
            print(f"   值: {bilibili_db_env.split('@')[0].split('//')[0]}//{user}:***@{parts[1]}")
        else:
            print(f"   值: {bilibili_db_env}")
    else:
        print(f"   值: {bilibili_db_env}")
else:
    print("⚠️  系统环境变量BILIBILI_DATABASE_URL未设置")

print()

# 3. 检查实际使用的数据库
print("【3. 实际使用的数据库（本地测试）】")
print("-" * 80)

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from bilibili_models import BILIBILI_DATABASE_URL, get_bilibili_engine
    
    print(f"✅ 实际数据库URL: {BILIBILI_DATABASE_URL}")
    
    if BILIBILI_DATABASE_URL.startswith('sqlite'):
        db_file = BILIBILI_DATABASE_URL.replace('sqlite:///', '').replace('sqlite:///', '')
        db_path = Path(db_file)
        
        if db_path.is_absolute():
            print(f"   ✅ 绝对路径: {db_path}")
        else:
            # 相对路径，需要确定当前工作目录
            cwd = Path.cwd()
            abs_path = cwd / db_path
            print(f"   ⚠️  相对路径: {db_file}")
            print(f"   ⚠️  当前工作目录: {cwd}")
            print(f"   ⚠️  实际数据库文件路径: {abs_path}")
        
        if db_path.exists() or abs_path.exists():
            actual_path = db_path if db_path.is_absolute() else abs_path
            size = actual_path.stat().st_size / (1024 * 1024)  # MB
            print(f"   ✅ 数据库文件存在")
            print(f"   📁 文件路径: {actual_path}")
            print(f"   📊 文件大小: {size:.2f} MB")
        else:
            print(f"   ⚠️  数据库文件不存在（首次运行时会创建）")
            print(f"   📁 将创建在: {abs_path if not db_path.is_absolute() else db_path}")
    
    elif BILIBILI_DATABASE_URL.startswith('postgresql') or BILIBILI_DATABASE_URL.startswith('postgres'):
        print(f"   ✅ 使用PostgreSQL数据库")
        from urllib.parse import urlparse
        parsed = urlparse(BILIBILI_DATABASE_URL)
        print(f"   📍 主机: {parsed.hostname}")
        print(f"   🔌 端口: {parsed.port or 5432}")
        print(f"   📚 数据库: {parsed.path.lstrip('/').split('?')[0]}")
        print(f"   👤 用户: {parsed.username}")
        
        # 测试连接
        try:
            engine = get_bilibili_engine()
            with engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("SELECT current_database(), current_user, version()"))
                row = result.fetchone()
                print(f"   ✅ 连接测试成功")
                print(f"   📊 当前数据库: {row[0]}")
                print(f"   👤 当前用户: {row[1]}")
        except Exception as e:
            print(f"   ❌ 连接测试失败: {e}")
    
except Exception as e:
    print(f"❌ 无法检查实际数据库: {e}")
    import traceback
    traceback.print_exc()

print()

# 4. 服务器配置检查指南
print("【4. 服务器配置检查指南】")
print("-" * 80)
print("""
需要在服务器上执行以下检查：

1. 检查环境变量：
   cd /srv/EmbodiedPulse2026
   source venv/bin/activate
   echo $BILIBILI_DATABASE_URL
   grep BILIBILI_DATABASE_URL .env

2. 检查gunicorn工作目录：
   cat gunicorn_config.py | grep -i "chdir\|working_dir\|bind"
   systemctl show embodiedpulse | grep WorkingDirectory

3. 检查实际数据库文件位置：
   find /srv/EmbodiedPulse2026 -name "bilibili.db" -type f 2>/dev/null
   ls -lh /srv/EmbodiedPulse2026/bilibili.db 2>/dev/null || echo "未找到数据库文件"

4. 检查服务运行时的环境变量：
   systemctl show embodiedpulse | grep Environment
   cat /etc/systemd/system/embodiedpulse.service | grep -i env

5. 检查Python代码实际使用的数据库：
   python3 << 'EOF'
   import os
   import sys
   sys.path.insert(0, '/srv/EmbodiedPulse2026')
   from bilibili_models import BILIBILI_DATABASE_URL
   print(f"实际使用的数据库URL: {BILIBILI_DATABASE_URL}")
   EOF
""")

print()

# 5. 问题诊断
print("【5. 潜在问题诊断】")
print("-" * 80)

if BILIBILI_DATABASE_URL.startswith('sqlite'):
    db_file = BILIBILI_DATABASE_URL.replace('sqlite:///', '').replace('sqlite:///', '')
    if not Path(db_file).is_absolute():
        print("⚠️  问题1: 使用相对路径的SQLite数据库")
        print("   影响: 如果服务器上的工作目录与本地不同，会连接到不同的数据库文件")
        print("   解决: 使用绝对路径或设置环境变量BILIBILI_DATABASE_URL")
        print()
        print("⚠️  问题2: 本地和服务器可能使用不同的数据库文件")
        print("   本地路径: " + str(Path.cwd() / db_file))
        print("   服务器路径: /srv/EmbodiedPulse2026/" + db_file)
        print("   解决: 确保服务器上设置了正确的环境变量或使用PostgreSQL")
        print()
        print("⚠️  问题3: 如果服务器上未设置环境变量，会使用默认的相对路径")
        print("   默认值: sqlite:///./bilibili.db")
        print("   实际文件位置取决于gunicorn的工作目录")
        print("   解决: 在.env文件中设置BILIBILI_DATABASE_URL，或使用systemd环境变量")

print()

# 6. 建议
print("【6. 建议】")
print("-" * 80)
print("""
1. 在服务器上检查.env文件，确保设置了BILIBILI_DATABASE_URL
2. 如果使用SQLite，建议使用绝对路径，例如：
   BILIBILI_DATABASE_URL=sqlite:////srv/EmbodiedPulse2026/bilibili.db
3. 生产环境建议使用PostgreSQL，避免文件路径问题
4. 检查gunicorn的工作目录配置，确保与预期一致
5. 在服务器上运行此脚本，检查实际使用的数据库配置
""")

print("=" * 80)
print("检查完成")
print("=" * 80)

