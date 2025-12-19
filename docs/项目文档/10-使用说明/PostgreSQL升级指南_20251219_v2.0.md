# PostgreSQL升级指南

## 📋 概述

本项目已全面升级支持PostgreSQL数据库，替代原有的SQLite数据库。升级后可以获得更好的并发性能、数据完整性和可扩展性。

## 🎯 升级内容

### 数据库升级
- ✅ **论文数据库** (papers.db → PostgreSQL)
- ✅ **招聘信息数据库** (jobs.db → PostgreSQL)
- ✅ **新闻数据库** (news.db → PostgreSQL)
- ✅ **数据集数据库** (datasets.db → PostgreSQL)

### 技术改进
- ✅ 添加PostgreSQL驱动 (`psycopg2-binary`)
- ✅ 所有模型文件支持PostgreSQL连接
- ✅ 连接池配置（提高并发性能）
- ✅ 自动重连机制（`pool_pre_ping=True`）
- ✅ Docker Compose集成PostgreSQL服务

## 🚀 快速开始

### 方式1: 使用Docker Compose（推荐）

**步骤1: 启动服务**
```bash
docker-compose up -d
```

这将自动启动：
- PostgreSQL数据库服务（端口5432）
- Web应用服务（端口5001）

**步骤2: 初始化数据库**
```bash
docker-compose exec web python3 init_database.py
```

**步骤3: 迁移现有数据（如果有SQLite数据）**
```bash
docker-compose exec web python3 migrate_sqlite_to_postgresql.py
```

### 方式2: 本地PostgreSQL安装

**步骤1: 安装PostgreSQL**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql
brew services start postgresql

# 或使用Docker
docker run --name postgres -e POSTGRES_PASSWORD=robotics_password -e POSTGRES_USER=robotics_user -e POSTGRES_DB=robotics_arxiv -p 5432:5432 -d postgres:15-alpine
```

**步骤2: 创建数据库**
```bash
# 连接到PostgreSQL
psql -U postgres

# 创建数据库和用户
CREATE DATABASE robotics_arxiv;
CREATE USER robotics_user WITH PASSWORD 'robotics_password';
GRANT ALL PRIVILEGES ON DATABASE robotics_arxiv TO robotics_user;
\q
```

**步骤3: 配置环境变量**
```bash
export DATABASE_URL=postgresql://robotics_user:robotics_password@localhost:5432/robotics_arxiv
```

**步骤4: 初始化数据库**
```bash
python3 init_database.py
```

**步骤5: 迁移数据（如果有SQLite数据）**
```bash
python3 migrate_sqlite_to_postgresql.py
```

## 📝 环境变量配置

### 基本配置

```bash
# 主数据库（论文数据库）
DATABASE_URL=postgresql://robotics_user:robotics_password@localhost:5432/robotics_arxiv
```

### 独立数据库配置（可选）

如果需要为不同模块使用独立的PostgreSQL数据库：

```bash
# 主数据库
DATABASE_URL=postgresql://user:password@localhost:5432/robotics_arxiv

# 招聘信息数据库（可选，默认使用DATABASE_URL）
JOBS_DATABASE_URL=postgresql://user:password@localhost:5432/robotics_jobs

# 新闻数据库（可选，默认使用DATABASE_URL）
NEWS_DATABASE_URL=postgresql://user:password@localhost:5432/robotics_news

# 数据集数据库（可选，默认使用DATABASE_URL）
DATASETS_DATABASE_URL=postgresql://user:password@localhost:5432/robotics_datasets
```

### Docker Compose环境变量

在`docker-compose.yml`中已配置：
```yaml
environment:
  - DATABASE_URL=postgresql://robotics_user:robotics_password@postgres:5432/robotics_arxiv
```

## 🔄 数据迁移

### 从SQLite迁移到PostgreSQL

**自动迁移脚本：**
```bash
python3 migrate_sqlite_to_postgresql.py
```

**迁移过程：**
1. 检查PostgreSQL连接
2. 读取SQLite数据
3. 检查PostgreSQL表结构
4. 迁移数据（自动跳过已存在的记录）
5. 显示迁移统计

**注意事项：**
- 迁移前请先运行 `python3 init_database.py` 创建表结构
- 迁移不会删除PostgreSQL中的现有数据
- 如果记录已存在（根据主键），将自动跳过

### 手动迁移（高级）

如果需要更精细的控制，可以手动导出和导入：

```bash
# 1. 导出SQLite数据
sqlite3 papers.db .dump > papers_backup.sql

# 2. 修改SQL语法（SQLite → PostgreSQL）
# 注意：需要手动修改一些SQL语法差异

# 3. 导入到PostgreSQL
psql -U robotics_user -d robotics_arxiv -f papers_backup.sql
```

## 🔧 配置说明

### 连接池配置

所有模型文件已配置连接池：

```python
create_engine(
    DATABASE_URL,
    pool_size=10,        # 连接池大小
    max_overflow=20,     # 最大溢出连接数
    pool_pre_ping=True   # 自动重连
)
```

### 性能优化

PostgreSQL相比SQLite的优势：
- ✅ **并发性能**: 支持多用户同时读写
- ✅ **连接池**: 复用连接，减少开销
- ✅ **事务支持**: 更好的ACID特性
- ✅ **索引优化**: 更强大的索引功能
- ✅ **全文搜索**: 支持PostgreSQL全文搜索

## 🐛 故障排查

### 连接失败

**问题**: `psycopg2.OperationalError: could not connect to server`

**解决方案**:
1. 检查PostgreSQL服务是否运行
   ```bash
   # Docker
   docker-compose ps
   
   # 本地
   sudo systemctl status postgresql
   ```

2. 检查连接URL是否正确
   ```bash
   echo $DATABASE_URL
   ```

3. 检查防火墙设置
   ```bash
   # 确保5432端口开放
   sudo ufw allow 5432
   ```

### 权限错误

**问题**: `permission denied for database`

**解决方案**:
```sql
-- 连接到PostgreSQL
psql -U postgres

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE robotics_arxiv TO robotics_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO robotics_user;
```

### 表不存在

**问题**: `relation "papers" does not exist`

**解决方案**:
```bash
# 运行初始化脚本
python3 init_database.py
```

## 📊 验证升级

### 检查数据库连接

```bash
python3 -c "
from models import get_session, Paper
session = get_session()
count = session.query(Paper).count()
print(f'论文数量: {count}')
session.close()
"
```

### 检查所有数据库

```bash
python3 tests/test_database_connections.py
```

## 🔄 回退到SQLite

如果需要回退到SQLite：

1. **修改环境变量**
   ```bash
   export DATABASE_URL=sqlite:///./papers.db
   export JOBS_DATABASE_URL=sqlite:///./jobs.db
   export NEWS_DATABASE_URL=sqlite:///./news.db
   export DATASETS_DATABASE_URL=sqlite:///./datasets.db
   ```

2. **重新初始化**
   ```bash
   python3 init_database.py
   ```

3. **迁移数据（从PostgreSQL到SQLite）**
   - 需要手动导出PostgreSQL数据
   - 转换为SQLite格式
   - 导入SQLite数据库

## 📚 相关文档

- [数据库需求分析与方案选型](../03-技术文档/数据库需求分析与方案选型_20251208.md)
- [生产环境部署方案](./生产环境部署方案_20251210.md)
- [Docker Compose配置](../03-技术文档/部署方案_20251208.md)

## ✅ 升级检查清单

- [ ] PostgreSQL服务已安装并运行
- [ ] 环境变量已正确配置
- [ ] 数据库和用户已创建
- [ ] 运行 `init_database.py` 创建表结构
- [ ] 运行 `migrate_sqlite_to_postgresql.py` 迁移数据（如果有）
- [ ] 运行 `test_database_connections.py` 验证连接
- [ ] 测试应用功能是否正常
- [ ] 备份原有SQLite数据（可选）

## 🎉 升级完成

升级完成后，你将获得：
- ✅ 更好的并发性能
- ✅ 更强的数据完整性
- ✅ 更好的可扩展性
- ✅ 生产环境就绪

如有问题，请查看故障排查部分或提交Issue。
