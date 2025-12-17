# PostgreSQL迁移问题解决

**版本**: v2.0  
**日期**: 2025-12-17

---

## 🔍 问题诊断

### 问题：本地PostgreSQL连接失败

**错误信息**:
```
connection to server at "localhost" (::1), port 5432 failed: Connection refused
```

**可能原因**:
1. Docker容器未运行
2. 本地PostgreSQL服务未安装或未启动
3. 端口未映射或配置错误

---

## 🚀 解决方案

### 方案1：启动Docker PostgreSQL（如果使用Docker）

```bash
cd "/Users/dong/Documents/Cursor/Embodied Pulse"

# 启动PostgreSQL容器
docker-compose up -d postgres

# 等待容器启动（约10秒）
sleep 10

# 检查容器状态
docker ps | grep postgres

# 检查端口映射
docker port embodied-pulse-postgres
# 应该看到: 5432/tcp -> 0.0.0.0:5432

# 测试连接
docker exec -it embodied-pulse-postgres psql -U robotics_user -d robotics_arxiv -c "SELECT COUNT(*) FROM papers;"
```

### 方案2：如果本地没有PostgreSQL数据

**最简单方案**：直接在服务器上切换到PostgreSQL，让系统自动抓取数据

```bash
# 在服务器上执行
ssh root@101.200.222.139

cd /srv/EmbodiedPulse2026
git pull origin main
bash scripts/switch_to_postgresql.sh
```

然后访问网站，点击"刷新论文数据"按钮，系统会自动抓取。

### 方案3：从服务器SQLite迁移到PostgreSQL（如果服务器有数据）

如果服务器上的SQLite文件有数据，可以直接在服务器上迁移：

```bash
# 在服务器上执行
ssh root@101.200.222.139

cd /srv/EmbodiedPulse2026
source venv/bin/activate

# 设置密码
DB_PASSWORD='MyStrongPass123!@#'
ENCODED_PASSWORD=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$DB_PASSWORD', safe=''))")
export DATABASE_URL="postgresql://embodied_user:$ENCODED_PASSWORD@localhost:5432/embodied_pulse"
export BILIBILI_DATABASE_URL="postgresql://embodied_user:$ENCODED_PASSWORD@localhost:5432/embodied_pulse"

# 初始化表结构
python3 init_database.py

# 从SQLite迁移到PostgreSQL
python3 migrate_sqlite_to_postgresql.py
```

---

## 📋 推荐方案

**根据你的情况，推荐使用方案2或方案3**：

1. **如果服务器上SQLite有完整数据** → 使用方案3（在服务器上迁移）
2. **如果服务器上SQLite数据不完整或为空** → 使用方案2（直接切换，自动抓取）

---

## ✅ 检查服务器数据

先检查服务器上的数据量：

```bash
ssh root@101.200.222.139 << 'EOF'
cd /srv/EmbodiedPulse2026
source venv/bin/activate

# 检查SQLite数据量
python3 << 'PYEOF'
import os
os.environ['DATABASE_URL'] = 'sqlite:///./papers.db'
os.environ['BILIBILI_DATABASE_URL'] = 'sqlite:///./bilibili.db'

try:
    from models import get_session, Paper
    session = get_session()
    papers_count = session.query(Paper).count()
    session.close()
    print(f"SQLite论文数据: {papers_count} 篇")
except Exception as e:
    print(f"无法查询: {e}")

try:
    from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
    bilibili_session = get_bilibili_session()
    ups_count = bilibili_session.query(BilibiliUp).count()
    videos_count = bilibili_session.query(BilibiliVideo).count()
    bilibili_session.close()
    print(f"SQLite UP主数据: {ups_count} 个")
    print(f"SQLite视频数据: {videos_count} 个")
except Exception as e:
    print(f"无法查询: {e}")
PYEOF
EOF
```

**根据数据量决定**：
- 如果数据量 > 1000 → 使用方案3（迁移）
- 如果数据量 < 1000 → 使用方案2（重新抓取）

---

**文档版本**: v2.0  
**最后更新**: 2025-12-17

