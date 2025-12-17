# PostgreSQL迁移Python方案（无需pg_dump）

**版本**: v1.0  
**日期**: 2025-12-17  
**适用场景**: 本地没有安装pg_dump，或使用Docker PostgreSQL

---

## 🚀 快速迁移（Python方案）

### 优势

- ✅ 不需要安装PostgreSQL客户端工具（pg_dump）
- ✅ 使用Python和SQLAlchemy，代码中已有依赖
- ✅ 支持Docker PostgreSQL
- ✅ 跨平台（Mac/Windows/Linux）

---

## 📝 使用步骤

### 步骤1：确认本地PostgreSQL连接信息

**如果使用Docker**:
```bash
# 检查Docker容器
docker ps | grep postgres

# 查看连接信息（从docker-compose.yml）
cat docker-compose.yml | grep -A 5 "postgres:"
```

**连接信息示例**:
```
POSTGRES_USER: robotics_user
POSTGRES_PASSWORD: robotics_password
POSTGRES_DB: robotics_arxiv
端口: 5432（如果映射到主机）
```

**连接URL格式**:
```
postgresql://robotics_user:robotics_password@localhost:5432/robotics_arxiv
```

### 步骤2：设置环境变量

```bash
cd "/Users/dong/Documents/Cursor/Embodied Pulse"

# 设置本地PostgreSQL连接URL
export LOCAL_DATABASE_URL='postgresql://robotics_user:robotics_password@localhost:5432/robotics_arxiv'

# 设置服务器PostgreSQL连接URL（密码需要URL编码）
# 如果密码包含特殊字符，需要编码
export SERVER_DATABASE_URL='postgresql://embodied_user:MyStrongPass123%21%40%23@101.200.222.139:5432/embodied_pulse'
```

**密码URL编码**:
```bash
# 如果密码包含特殊字符，先编码
python3 -c "import urllib.parse; print(urllib.parse.quote('MyStrongPass123!@#', safe=''))"
# 输出: MyStrongPass123%21%40%23
```

### 步骤3：执行迁移

```bash
# 确保虚拟环境激活（如果需要）
source venv/bin/activate  # 如果使用虚拟环境

# 执行迁移
python3 scripts/migrate_postgresql_python.py
```

---

## 🔧 Docker PostgreSQL连接

### 方法1：如果PostgreSQL端口映射到主机

```bash
# 检查端口映射
docker ps | grep postgres
# 应该看到类似: 0.0.0.0:5432->5432/tcp

# 直接使用localhost连接
export LOCAL_DATABASE_URL='postgresql://robotics_user:robotics_password@localhost:5432/robotics_arxiv'
```

### 方法2：如果PostgreSQL端口未映射

```bash
# 获取容器IP
docker inspect embodied-pulse-postgres | grep IPAddress

# 使用容器IP连接
export LOCAL_DATABASE_URL='postgresql://robotics_user:robotics_password@172.17.0.2:5432/robotics_arxiv'
```

### 方法3：通过Docker exec执行（推荐）

创建一个包装脚本，在Docker容器内执行迁移：

```bash
# 在本地执行，但连接到Docker内的PostgreSQL
docker exec -it embodied-pulse-postgres psql -U robotics_user -d robotics_arxiv -c "SELECT COUNT(*) FROM papers;"
```

---

## 📋 完整示例

```bash
cd "/Users/dong/Documents/Cursor/Embodied Pulse"

# 1. 检查本地PostgreSQL（Docker）
docker ps | grep postgres

# 2. 设置本地连接URL（根据实际情况修改）
export LOCAL_DATABASE_URL='postgresql://robotics_user:robotics_password@localhost:5432/robotics_arxiv'

# 3. 设置服务器连接URL（密码需要URL编码）
SERVER_PASSWORD='MyStrongPass123!@#'
ENCODED_PASSWORD=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$SERVER_PASSWORD', safe=''))")
export SERVER_DATABASE_URL="postgresql://embodied_user:$ENCODED_PASSWORD@101.200.222.139:5432/embodied_pulse"

# 4. 执行迁移
python3 scripts/migrate_postgresql_python.py
```

---

## ✅ 迁移后验证

```bash
# 在服务器上验证数据量
ssh root@101.200.222.139 << 'EOF'
cd /srv/EmbodiedPulse2026
source venv/bin/activate
python3 scripts/check_current_database.py
EOF
```

---

## 🔍 故障排查

### 问题1：无法连接本地PostgreSQL

**检查Docker容器**:
```bash
docker ps | grep postgres
docker logs embodied-pulse-postgres
```

**检查端口映射**:
```bash
docker port embodied-pulse-postgres
```

### 问题2：密码包含特殊字符

**解决**: 使用URL编码
```bash
python3 -c "import urllib.parse; print(urllib.parse.quote('your_password!@#', safe=''))"
```

### 问题3：服务器连接失败

**检查**:
```bash
# 测试服务器连接
psql -h 101.200.222.139 -U embodied_user -d embodied_pulse -c "\q"
```

---

**文档版本**: v1.0  
**最后更新**: 2025-12-17

