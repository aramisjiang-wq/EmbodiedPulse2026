# PostgreSQL安装与迁移小白教程

**版本**: v1.0  
**日期**: 2025-12-17  
**目标**: 让小白也能完成从SQLite到PostgreSQL的升级

---

## 📋 目录

1. [准备工作](#一准备工作)
2. [安装PostgreSQL](#二安装postgresql)
3. [创建数据库和用户](#三创建数据库和用户)
4. [迁移数据](#四迁移数据)
5. [更新配置](#五更新配置)
6. [验证和测试](#六验证和测试)
7. [常见问题](#七常见问题)

---

## 一、准备工作

### 1.1 检查当前状态

**在服务器上执行**:

```bash
# SSH登录服务器
ssh root@101.200.222.139
# 输入密码: XLj4kUnh

# 进入项目目录
cd /srv/EmbodiedPulse2026

# 检查当前数据库
ls -lh *.db
# 应该看到: papers.db, bilibili.db 等

# 检查当前数据库配置
cat .env | grep DATABASE_URL
# 应该显示: DATABASE_URL=sqlite:///./papers.db
```

### 1.2 备份当前数据库

**非常重要！先备份再操作**:

```bash
cd /srv/EmbodiedPulse2026

# 创建备份目录
mkdir -p backups/postgresql_migration

# 备份所有数据库文件
cp papers.db backups/postgresql_migration/papers_backup_$(date +%Y%m%d_%H%M%S).db
cp bilibili.db backups/postgresql_migration/bilibili_backup_$(date +%Y%m%d_%H%M%S).db
cp instance/papers.db backups/postgresql_migration/auth_backup_$(date +%Y%m%d_%H%M%S).db 2>/dev/null || true

# 验证备份
ls -lh backups/postgresql_migration/
# 应该看到备份文件
```

---

## 二、安装PostgreSQL

### 2.1 更新系统包

```bash
# 更新软件包列表
apt update

# 升级系统（可选，但建议）
apt upgrade -y
```

### 2.2 安装PostgreSQL

```bash
# 安装PostgreSQL和客户端工具
apt install -y postgresql postgresql-contrib

# 验证安装
postgresql --version
# 或
psql --version
# 应该显示版本号，例如: psql (PostgreSQL) 12.x
```

### 2.3 启动PostgreSQL服务

```bash
# 启动PostgreSQL服务
systemctl start postgresql

# 设置开机自启
systemctl enable postgresql

# 检查服务状态
systemctl status postgresql
# 应该显示: active (running)
```

---

## 三、创建数据库和用户

### 3.1 切换到postgres用户

```bash
# 切换到postgres用户（PostgreSQL的默认管理员）
sudo -u postgres psql

# 现在进入了PostgreSQL命令行，提示符变成: postgres=#
```

### 3.2 创建数据库

**在PostgreSQL命令行中执行**（注意：提示符是 `postgres=#`）:

```sql
-- 创建数据库
CREATE DATABASE embodied_pulse;

-- 验证数据库创建成功
\l
-- 应该能看到 embodied_pulse 数据库
```

### 3.3 创建用户并设置权限

**继续在PostgreSQL命令行中执行**:

```sql
-- 创建用户（替换 your_password 为你想要的密码）
CREATE USER embodied_user WITH PASSWORD 'your_strong_password_here';

-- 授予数据库权限
GRANT ALL PRIVILEGES ON DATABASE embodied_pulse TO embodied_user;

-- 退出PostgreSQL命令行
\q
```

**⚠️ 重要**: 
- 将 `your_strong_password_here` 替换为强密码（建议包含大小写字母、数字、特殊字符）
- 记住这个密码，稍后配置需要用到

### 3.4 验证创建成功

```bash
# 测试连接（使用新创建的用户）
psql -U embodied_user -d embodied_pulse -h localhost

# 如果连接成功，会看到提示符: embodied_pulse=>
# 输入 \q 退出
\q
```

---

## 四、迁移数据

### 4.1 安装Python依赖

```bash
cd /srv/EmbodiedPulse2026

# 激活虚拟环境
source venv/bin/activate

# 确保安装了psycopg2（PostgreSQL驱动）
pip install psycopg2-binary

# 验证安装
python3 -c "import psycopg2; print('psycopg2已安装')"
```

### 4.2 设置环境变量

```bash
# 设置PostgreSQL连接URL（替换密码）
export DATABASE_URL=postgresql://embodied_user:your_strong_password_here@localhost:5432/embodied_pulse

# 验证环境变量
echo $DATABASE_URL
# 应该显示: postgresql://embodied_user:your_password@localhost:5432/embodied_pulse
```

### 4.3 初始化PostgreSQL表结构

```bash
cd /srv/EmbodiedPulse2026
source venv/bin/activate

# 初始化数据库表结构
python3 init_database.py

# 应该看到: "✅ 所有数据库表创建成功"
```

### 4.4 迁移数据

```bash
# 迁移SQLite数据到PostgreSQL
python3 migrate_sqlite_to_postgresql.py

# 这个过程可能需要几分钟，请耐心等待
# 应该看到迁移进度和成功信息
```

**迁移过程说明**:
- 脚本会依次迁移 papers、jobs、news、datasets 表
- 每个表会显示迁移进度
- 如果表已存在数据，会提示是否覆盖

---

## 五、更新配置

### 5.1 更新.env文件

```bash
cd /srv/EmbodiedPulse2026

# 备份.env文件
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# 编辑.env文件
nano .env
```

**在nano编辑器中**:
1. 找到 `DATABASE_URL=sqlite:///./papers.db` 这一行
2. 修改为: `DATABASE_URL=postgresql://embodied_user:your_strong_password_here@localhost:5432/embodied_pulse`
3. 保存: 按 `Ctrl+O`，然后 `Enter`
4. 退出: 按 `Ctrl+X`

**或者使用sed命令（更简单）**:

```bash
# 替换DATABASE_URL（替换your_strong_password_here为实际密码）
sed -i 's|DATABASE_URL=sqlite:///./papers.db|DATABASE_URL=postgresql://embodied_user:your_strong_password_here@localhost:5432/embodied_pulse|' .env

# 验证修改
cat .env | grep DATABASE_URL
# 应该显示PostgreSQL连接URL
```

### 5.2 更新其他数据库配置（可选）

如果使用独立的数据库，可以配置：

```bash
# 编辑.env文件
nano .env

# 添加以下配置（如果需要）
BILIBILI_DATABASE_URL=postgresql://embodied_user:your_password@localhost:5432/embodied_pulse
JOBS_DATABASE_URL=postgresql://embodied_user:your_password@localhost:5432/embodied_pulse
NEWS_DATABASE_URL=postgresql://embodied_user:your_password@localhost:5432/embodied_pulse
```

**注意**: 如果使用同一个PostgreSQL数据库，可以不配置这些，会使用主 `DATABASE_URL`。

---

## 六、验证和测试

### 6.1 重启服务

```bash
# 重启服务使新配置生效
systemctl restart embodiedpulse

# 检查服务状态
systemctl status embodiedpulse
# 应该显示: active (running)
```

### 6.2 验证数据库连接

```bash
cd /srv/EmbodiedPulse2026
source venv/bin/activate

# 测试数据库连接
python3 << 'EOF'
import os
from models import get_session, Paper

# 设置环境变量（如果还没设置）
os.environ['DATABASE_URL'] = 'postgresql://embodied_user:your_password@localhost:5432/embodied_pulse'

try:
    session = get_session()
    count = session.query(Paper).count()
    print(f"✅ PostgreSQL连接成功！")
    print(f"   论文数量: {count}")
    session.close()
except Exception as e:
    print(f"❌ 连接失败: {e}")
EOF
```

### 6.3 验证网站功能

1. **访问网站**: https://essay.gradmotion.com
2. **检查数据**: 应该能看到论文数据正常显示
3. **检查B站页面**: https://blibli.gradmotion.com
4. **检查管理端**: https://admin123.gradmotion.com

### 6.4 检查日志

```bash
# 查看服务日志
journalctl -u embodiedpulse -n 50

# 检查是否有数据库相关错误
journalctl -u embodiedpulse | grep -i "database\|postgres\|error"
```

---

## 七、常见问题

### 问题1：PostgreSQL服务无法启动

**症状**: `systemctl status postgresql` 显示失败

**解决方法**:

```bash
# 查看详细错误
journalctl -u postgresql -n 50

# 检查端口是否被占用
lsof -i:5432

# 重启服务
systemctl restart postgresql
```

### 问题2：无法连接到PostgreSQL

**症状**: `psql -U embodied_user -d embodied_pulse` 失败

**解决方法**:

```bash
# 检查PostgreSQL配置
sudo -u postgres psql

# 在PostgreSQL中检查用户
\du
# 应该能看到 embodied_user

# 检查数据库
\l
# 应该能看到 embodied_pulse

# 检查权限
\c embodied_pulse
\dn
\q
```

### 问题3：迁移数据失败

**症状**: `migrate_sqlite_to_postgresql.py` 执行失败

**解决方法**:

```bash
# 1. 检查PostgreSQL连接
psql -U embodied_user -d embodied_pulse -h localhost

# 2. 检查表结构是否创建
psql -U embodied_user -d embodied_pulse -h localhost -c "\dt"
# 应该能看到表列表

# 3. 如果表不存在，重新初始化
python3 init_database.py

# 4. 重新迁移
python3 migrate_sqlite_to_postgresql.py
```

### 问题4：迁移后数据不完整

**症状**: 网站显示数据为空或部分数据丢失

**解决方法**:

```bash
# 1. 检查PostgreSQL中的数据
psql -U embodied_user -d embodied_pulse -h localhost -c "SELECT COUNT(*) FROM papers;"
psql -U embodied_user -d embodied_pulse -h localhost -c "SELECT COUNT(*) FROM bilibili_ups;"

# 2. 如果数据不完整，从备份恢复SQLite，重新迁移
# 恢复SQLite数据库
cp backups/postgresql_migration/papers_backup_*.db papers.db

# 重新迁移
python3 migrate_sqlite_to_postgresql.py
```

### 问题5：服务启动失败

**症状**: `systemctl restart embodiedpulse` 后服务无法启动

**解决方法**:

```bash
# 1. 查看错误日志
journalctl -u embodiedpulse -n 100

# 2. 检查.env文件配置
cat .env | grep DATABASE_URL

# 3. 测试数据库连接
python3 -c "from models import get_session; session = get_session(); print('OK')"

# 4. 如果连接失败，检查密码是否正确
```

---

## 八、回滚方案（如果出现问题）

### 8.1 回滚到SQLite

如果PostgreSQL迁移出现问题，可以回滚：

```bash
cd /srv/EmbodiedPulse2026

# 1. 恢复.env文件
cp .env.backup.* .env
# 或手动修改
nano .env
# 将 DATABASE_URL 改回: sqlite:///./papers.db

# 2. 恢复数据库文件（如果需要）
cp backups/postgresql_migration/papers_backup_*.db papers.db
cp backups/postgresql_migration/bilibili_backup_*.db bilibili.db

# 3. 重启服务
systemctl restart embodiedpulse

# 4. 验证
systemctl status embodiedpulse
```

---

## 九、完整操作流程（一键执行）

### 9.1 完整脚本

创建脚本 `scripts/setup_postgresql.sh`:

```bash
#!/bin/bash
# PostgreSQL安装和迁移完整脚本

set -e

APP_DIR="/srv/EmbodiedPulse2026"
DB_NAME="embodied_pulse"
DB_USER="embodied_user"
DB_PASSWORD="your_strong_password_here"  # ⚠️ 修改为你的密码

echo "=========================================="
echo "PostgreSQL安装和迁移"
echo "=========================================="

# 1. 备份数据库
echo "1. 备份当前数据库..."
cd "$APP_DIR"
mkdir -p backups/postgresql_migration
cp papers.db backups/postgresql_migration/papers_backup_$(date +%Y%m%d_%H%M%S).db
cp bilibili.db backups/postgresql_migration/bilibili_backup_$(date +%Y%m%d_%H%M%S).db
echo "✅ 备份完成"

# 2. 安装PostgreSQL
echo ""
echo "2. 安装PostgreSQL..."
apt update
apt install -y postgresql postgresql-contrib
systemctl start postgresql
systemctl enable postgresql
echo "✅ PostgreSQL已安装"

# 3. 创建数据库和用户
echo ""
echo "3. 创建数据库和用户..."
sudo -u postgres psql << EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\q
EOF
echo "✅ 数据库和用户已创建"

# 4. 安装Python依赖
echo ""
echo "4. 安装Python依赖..."
cd "$APP_DIR"
source venv/bin/activate
pip install psycopg2-binary
echo "✅ Python依赖已安装"

# 5. 初始化表结构
echo ""
echo "5. 初始化PostgreSQL表结构..."
export DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
python3 init_database.py
echo "✅ 表结构已创建"

# 6. 迁移数据
echo ""
echo "6. 迁移数据..."
python3 migrate_sqlite_to_postgresql.py
echo "✅ 数据迁移完成"

# 7. 更新.env文件
echo ""
echo "7. 更新.env文件..."
sed -i "s|DATABASE_URL=sqlite:///./papers.db|DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME|" .env
echo "✅ 配置已更新"

# 8. 重启服务
echo ""
echo "8. 重启服务..."
systemctl restart embodiedpulse
echo "✅ 服务已重启"

echo ""
echo "=========================================="
echo "✅ PostgreSQL安装和迁移完成！"
echo "=========================================="
echo ""
echo "数据库信息:"
echo "  数据库名: $DB_NAME"
echo "  用户名: $DB_USER"
echo "  连接URL: postgresql://$DB_USER:***@localhost:5432/$DB_NAME"
echo ""
echo "下一步:"
echo "  1. 访问网站验证数据: https://essay.gradmotion.com"
echo "  2. 检查服务日志: journalctl -u embodiedpulse -n 50"
```

---

## 十、验证清单

迁移完成后，请验证以下项目：

- [ ] PostgreSQL服务运行正常
- [ ] 数据库和用户创建成功
- [ ] 表结构创建成功
- [ ] 数据迁移成功（数据量正确）
- [ ] `.env` 文件配置正确
- [ ] 服务重启成功
- [ ] 网站数据正常显示
- [ ] 没有错误日志

---

## 📝 注意事项

1. **密码安全**: 使用强密码，不要使用简单密码
2. **备份优先**: 迁移前一定要备份
3. **逐步操作**: 按照步骤一步步来，不要跳步
4. **验证结果**: 每步完成后验证结果
5. **保留备份**: 迁移成功后，备份文件可以保留一段时间

---

**文档版本**: v1.0  
**最后更新**: 2025-12-17  
**维护者**: AI Assistant

