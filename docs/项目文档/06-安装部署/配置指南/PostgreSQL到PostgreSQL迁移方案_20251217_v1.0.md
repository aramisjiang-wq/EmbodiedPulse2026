# PostgreSQL到PostgreSQL迁移方案

**版本**: v1.0  
**日期**: 2025-12-17  
**适用场景**: 本地使用PostgreSQL，需要迁移到服务器PostgreSQL

---

## 📊 迁移方案

### 方案概述

使用 `pg_dump` 导出本地PostgreSQL数据，然后通过 `psql` 导入到服务器PostgreSQL。

**流程**:
```
本地PostgreSQL → pg_dump导出 → 传输到服务器 → psql导入 → 服务器PostgreSQL
```

---

## 🚀 快速迁移（一键脚本）

### 步骤1：修改脚本配置

编辑 `scripts/migrate_postgresql_to_server.sh`，修改以下配置：

```bash
# 本地PostgreSQL配置
LOCAL_PG_HOST="localhost"
LOCAL_PG_PORT="5432"
LOCAL_PG_USER="robotics_user"
LOCAL_PG_PASSWORD="robotics_password"  # ⚠️ 修改为你的本地密码
LOCAL_PG_DB="robotics_arxiv"

# 服务器PostgreSQL配置
SERVER_PG_USER="embodied_user"
SERVER_PG_PASSWORD='MyStrongPass123!@#'  # ⚠️ 修改为服务器密码
SERVER_PG_DB="embodied_pulse"
```

### 步骤2：执行迁移

```bash
cd "/Users/dong/Documents/Cursor/Embodied Pulse"
bash scripts/migrate_postgresql_to_server.sh
```

脚本会自动：
1. ✅ 检查本地PostgreSQL连接
2. ✅ 检查本地数据量
3. ✅ 导出本地数据（pg_dump）
4. ✅ 传输到服务器
5. ✅ 导入到服务器PostgreSQL
6. ✅ 验证数据量

---

## 🔧 手动迁移步骤

如果脚本无法使用，可以手动执行：

### 步骤1：导出本地数据

```bash
# 在本地执行
pg_dump -h localhost -p 5432 -U robotics_user -d robotics_arxiv \
    --no-owner --no-acl \
    -t papers -t bilibili_ups -t bilibili_videos \
    -t jobs -t news -t datasets \
    > embodied_pulse_dump.sql
```

### 步骤2：传输到服务器

```bash
scp embodied_pulse_dump.sql root@101.200.222.139:/tmp/
```

### 步骤3：在服务器上导入

```bash
# SSH到服务器
ssh root@101.200.222.139

# 导入数据
cd /srv/EmbodiedPulse2026
export PGPASSWORD='MyStrongPass123!@#'  # 服务器密码
psql -h localhost -U embodied_user -d embodied_pulse < /tmp/embodied_pulse_dump.sql

# 验证数据
psql -h localhost -U embodied_user -d embodied_pulse -c "SELECT COUNT(*) FROM papers;"
psql -h localhost -U embodied_user -d embodied_pulse -c "SELECT COUNT(*) FROM bilibili_ups;"
psql -h localhost -U embodied_user -d embodied_pulse -c "SELECT COUNT(*) FROM bilibili_videos;"
```

---

## 📝 获取本地PostgreSQL连接信息

### 方法1：检查docker-compose.yml

```bash
cat docker-compose.yml | grep -A 5 "postgres:"
```

**输出示例**:
```yaml
postgres:
  environment:
    POSTGRES_USER: robotics_user
    POSTGRES_PASSWORD: robotics_password
    POSTGRES_DB: robotics_arxiv
```

### 方法2：检查.env文件

```bash
cat .env | grep DATABASE_URL
```

**输出示例**:
```
DATABASE_URL=postgresql://robotics_user:robotics_password@localhost:5432/robotics_arxiv
```

### 方法3：检查Docker容器

```bash
# 如果使用Docker
docker ps | grep postgres
docker exec -it embodied-pulse-postgres psql -U robotics_user -d robotics_arxiv -c "\conninfo"
```

---

## ✅ 迁移后验证

### 1. 检查数据量

```bash
# 在服务器上执行
cd /srv/EmbodiedPulse2026
python3 scripts/check_current_database.py
```

### 2. 检查网站功能

- 访问 https://essay.gradmotion.com
- 访问 https://blibli.gradmotion.com
- 检查数据是否正常显示

### 3. 重启服务

```bash
ssh root@101.200.222.139 'systemctl restart embodiedpulse'
```

---

## ⚠️ 注意事项

1. **密码安全**: 脚本中包含密码，注意保护脚本文件
2. **网络连接**: 确保可以SSH到服务器
3. **PostgreSQL版本**: 建议使用相同或兼容的PostgreSQL版本
4. **数据备份**: 迁移前建议备份服务器上的现有数据

---

## 🔍 故障排查

### 问题1：pg_dump连接失败

**解决**:
```bash
# 检查PostgreSQL服务是否运行
docker ps | grep postgres
# 或
ps aux | grep postgres

# 检查连接
psql -h localhost -p 5432 -U robotics_user -d robotics_arxiv -c "\q"
```

### 问题2：导入失败

**解决**:
```bash
# 检查表结构是否已创建
psql -h localhost -U embodied_user -d embodied_pulse -c "\dt"

# 如果表不存在，先初始化
cd /srv/EmbodiedPulse2026
python3 init_database.py
```

### 问题3：数据量不一致

**解决**:
```bash
# 对比本地和服务器数据量
# 本地
psql -h localhost -U robotics_user -d robotics_arxiv -c "SELECT COUNT(*) FROM papers;"

# 服务器
ssh root@101.200.222.139 'psql -h localhost -U embodied_user -d embodied_pulse -c "SELECT COUNT(*) FROM papers;"'
```

---

**文档版本**: v1.0  
**最后更新**: 2025-12-17

