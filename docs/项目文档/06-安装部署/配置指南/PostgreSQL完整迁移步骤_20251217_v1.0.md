# PostgreSQL完整迁移步骤（服务器端执行）

**版本**: v1.0  
**日期**: 2025-12-17  
**用途**: 在服务器上完整执行PostgreSQL迁移

---

## 📋 前置条件

- ✅ PostgreSQL已安装并运行
- ✅ 数据库和用户已创建
- ✅ Python依赖已安装（psycopg2-binary）
- ✅ SQLite数据库文件已备份

---

## 🚀 完整迁移步骤

### 步骤1：拉取最新代码

```bash
cd /srv/EmbodiedPulse2026

# 拉取最新代码（包含所有修复）
git pull origin main

# 如果脚本文件不存在，强制拉取
git checkout origin/main -- scripts/setup_postgresql.sh 2>/dev/null || true
chmod +x scripts/setup_postgresql.sh
```

### 步骤2：设置环境变量

```bash
cd /srv/EmbodiedPulse2026
source venv/bin/activate

# 设置数据库信息
DB_NAME="embodied_pulse"
DB_USER="embodied_user"
DB_PASSWORD="MyStrongPass123!@#"  # ⚠️ 替换为你的实际密码

# 对密码进行URL编码
ENCODED_PASSWORD=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$DB_PASSWORD', safe=''))")

# 设置DATABASE_URL环境变量
export DATABASE_URL="postgresql://$DB_USER:$ENCODED_PASSWORD@localhost:5432/$DB_NAME"

# 验证环境变量
echo "DATABASE_URL: $DATABASE_URL"
```

### 步骤3：初始化数据库表结构

```bash
# 初始化所有数据库表（现在会跳过已存在的索引）
python3 init_database.py
```

**预期输出**:
- ✅ 所有数据库表创建成功
- ⚠️ 如果索引已存在，会显示警告但不会中断

### 步骤4：迁移数据

```bash
# 迁移所有SQLite数据到PostgreSQL
python3 migrate_sqlite_to_postgresql.py
```

**迁移内容**:
- ✅ papers（论文）
- ✅ jobs（招聘信息）
- ✅ news（新闻）
- ✅ datasets（数据集）
- ✅ bilibili_ups（B站UP主）
- ✅ bilibili_videos（B站视频）

**预期输出**:
- 每个表显示迁移进度
- 显示成功/跳过/失败的记录数

### 步骤5：更新.env文件

```bash
# 备份.env文件
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# 更新DATABASE_URL（使用编码后的密码）
sed -i "s|DATABASE_URL=sqlite:///./papers.db|DATABASE_URL=postgresql://$DB_USER:$ENCODED_PASSWORD@localhost:5432/$DB_NAME|" .env

# 如果需要，也可以更新BILIBILI_DATABASE_URL（使用同一个PostgreSQL数据库）
sed -i "s|BILIBILI_DATABASE_URL=.*|BILIBILI_DATABASE_URL=postgresql://$DB_USER:$ENCODED_PASSWORD@localhost:5432/$DB_NAME|" .env || \
echo "BILIBILI_DATABASE_URL=postgresql://$DB_USER:$ENCODED_PASSWORD@localhost:5432/$DB_NAME" >> .env

# 验证更新
echo "更新后的配置:"
grep DATABASE_URL .env
```

### 步骤6：重启服务

```bash
# 重启服务使新配置生效
systemctl restart embodiedpulse

# 等待服务启动
sleep 5

# 检查服务状态
systemctl status embodiedpulse
```

### 步骤7：验证数据

```bash
# 验证PostgreSQL连接和数据
python3 << 'EOF'
import os
import urllib.parse

# 设置环境变量
DB_PASSWORD = 'MyStrongPass123!@#'  # ⚠️ 替换为你的实际密码
ENCODED_PASSWORD = urllib.parse.quote(DB_PASSWORD, safe='')
os.environ['DATABASE_URL'] = f'postgresql://embodied_user:{ENCODED_PASSWORD}@localhost:5432/embodied_pulse'
os.environ['BILIBILI_DATABASE_URL'] = f'postgresql://embodied_user:{ENCODED_PASSWORD}@localhost:5432/embodied_pulse'

try:
    from models import get_session, Paper
    from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
    
    # 检查论文数据
    session = get_session()
    papers_count = session.query(Paper).count()
    session.close()
    print(f"✅ 论文数据: {papers_count} 篇")
    
    # 检查B站数据
    bilibili_session = get_bilibili_session()
    ups_count = bilibili_session.query(BilibiliUp).count()
    videos_count = bilibili_session.query(BilibiliVideo).count()
    bilibili_session.close()
    print(f"✅ UP主数据: {ups_count} 个")
    print(f"✅ 视频数据: {videos_count} 个")
    
    print("\n✅ 所有数据验证成功！")
    
except Exception as e:
    print(f"❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
EOF
```

### 步骤8：验证网站功能

1. **访问论文页面**: https://essay.gradmotion.com
   - 检查论文数据是否正常显示
   - 检查分类和搜索功能

2. **访问B站页面**: https://blibli.gradmotion.com
   - 检查UP主和视频数据是否正常显示
   - 检查图表和统计功能

3. **检查管理端**: https://admin123.gradmotion.com
   - 检查数据管理功能

---

## 🔍 故障排查

### 问题1：索引重复创建错误

**已修复**: 所有`init_*_db()`函数已添加异常处理，会自动跳过已存在的索引。

### 问题2：迁移脚本找不到表

**解决**: 确保先运行`python3 init_database.py`创建表结构。

### 问题3：服务启动失败

**检查**:
```bash
# 查看服务日志
journalctl -u embodiedpulse -n 100

# 检查数据库连接
python3 -c "from models import get_session; session = get_session(); print('OK')"
```

### 问题4：数据迁移失败

**解决**:
- 检查SQLite数据库文件是否存在
- 检查PostgreSQL表是否已创建
- 检查环境变量是否正确设置

---

## 📝 一键执行脚本

创建文件 `migrate_to_postgresql.sh`:

```bash
#!/bin/bash
# PostgreSQL迁移一键脚本

set -e

cd /srv/EmbodiedPulse2026
source venv/bin/activate

DB_NAME="embodied_pulse"
DB_USER="embodied_user"
DB_PASSWORD="MyStrongPass123!@#"  # ⚠️ 修改为你的密码

# 编码密码
ENCODED_PASSWORD=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$DB_PASSWORD', safe=''))")
export DATABASE_URL="postgresql://$DB_USER:$ENCODED_PASSWORD@localhost:5432/$DB_NAME"

echo "1. 初始化表结构..."
python3 init_database.py

echo "2. 迁移数据..."
python3 migrate_sqlite_to_postgresql.py

echo "3. 更新.env文件..."
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
sed -i "s|DATABASE_URL=sqlite:///./papers.db|DATABASE_URL=postgresql://$DB_USER:$ENCODED_PASSWORD@localhost:5432/$DB_NAME|" .env

echo "4. 重启服务..."
systemctl restart embodiedpulse

echo "✅ 迁移完成！"
```

---

**文档版本**: v1.0  
**最后更新**: 2025-12-17

