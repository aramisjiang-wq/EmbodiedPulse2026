# PostgreSQL数据来源说明

**版本**: v1.0  
**日期**: 2025-12-17

---

## 📊 数据来源说明

### 重要发现

**PostgreSQL数据库的数据来源取决于你使用的方案**：

| 方案 | 数据来源 | 数据完整性 |
|------|---------|-----------|
| **迁移方案** | 服务器上的SQLite文件 | ✅ 完整（如果SQLite文件有数据） |
| **直接切换方案** | 重新抓取 | ⚠️ 需要时间（自动抓取） |

---

## 🔍 当前情况分析

### 情况1：如果执行了迁移方案

**数据来源**: 服务器上的SQLite文件（`papers.db`, `bilibili.db`等）

**迁移流程**:
```
服务器上的SQLite文件 → migrate_sqlite_to_postgresql.py → PostgreSQL数据库
```

**数据完整性**:
- ✅ 如果服务器上的SQLite文件有完整数据，PostgreSQL也会有完整数据
- ⚠️ 如果服务器上的SQLite文件数据不完整，PostgreSQL也不完整

**检查方法**:
```bash
# 1. 检查服务器上SQLite文件的数据量
cd /srv/EmbodiedPulse2026
python3 << 'EOF'
from models import get_session, Paper
from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo

# 检查SQLite数据（临时切换到SQLite）
import os
os.environ['DATABASE_URL'] = 'sqlite:///./papers.db'
os.environ['BILIBILI_DATABASE_URL'] = 'sqlite:///./bilibili.db'

session = get_session()
papers_count = session.query(Paper).count()
session.close()
print(f"SQLite论文数据: {papers_count} 篇")

bilibili_session = get_bilibili_session()
ups_count = bilibili_session.query(BilibiliUp).count()
videos_count = bilibili_session.query(BilibiliVideo).count()
bilibili_session.close()
print(f"SQLite UP主数据: {ups_count} 个")
print(f"SQLite视频数据: {videos_count} 个")
EOF

# 2. 检查PostgreSQL数据量
python3 << 'EOF'
import os
from dotenv import load_dotenv
load_dotenv()

from models import get_session, Paper
from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo

session = get_session()
papers_count = session.query(Paper).count()
session.close()
print(f"PostgreSQL论文数据: {papers_count} 篇")

bilibili_session = get_bilibili_session()
ups_count = bilibili_session.query(BilibiliUp).count()
videos_count = bilibili_session.query(BilibiliVideo).count()
bilibili_session.close()
print(f"PostgreSQL UP主数据: {ups_count} 个")
print(f"PostgreSQL视频数据: {videos_count} 个")
EOF
```

---

### 情况2：如果执行了直接切换方案

**数据来源**: 重新抓取（API）

**数据状态**:
- ⚠️ PostgreSQL数据库是空的（只有表结构）
- ✅ 系统会自动重新抓取数据（通过定时任务或手动触发）

**数据完整性**:
- ⚠️ 需要等待数据抓取完成
- ✅ 抓取完成后数据是完整的

**检查方法**:
```bash
# 检查PostgreSQL数据量
python3 scripts/check_current_database.py

# 如果数据量少，触发抓取
# 1. 论文数据：访问网站点击"刷新论文数据"
# 2. B站数据：等待定时任务或手动触发
```

---

## ❌ 重要：没有从本地直接复制到PostgreSQL

**关键发现**:
- ❌ **没有**从本地直接复制数据到PostgreSQL的机制
- ✅ 迁移脚本是从**服务器上的SQLite**迁移到PostgreSQL
- ✅ 如果本地有完整数据，需要先复制SQLite文件到服务器，再迁移

---

## 🚀 如何确保PostgreSQL数据完整？

### 方案A：从本地SQLite迁移（推荐，如果本地数据完整）

**步骤1**: 从本地复制SQLite文件到服务器

```bash
# 在本地执行
cd "/Users/dong/Documents/Cursor/Embodied Pulse"

# 复制SQLite文件到服务器
scp papers.db root@101.200.222.139:/srv/EmbodiedPulse2026/
scp bilibili.db root@101.200.222.139:/srv/EmbodiedPulse2026/
```

**步骤2**: 在服务器上执行迁移

```bash
# 在服务器上执行
cd /srv/EmbodiedPulse2026

# 设置环境变量
DB_PASSWORD='MyStrongPass123!@#'
ENCODED_PASSWORD=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$DB_PASSWORD', safe=''))")
export DATABASE_URL="postgresql://embodied_user:$ENCODED_PASSWORD@localhost:5432/embodied_pulse"
export BILIBILI_DATABASE_URL="postgresql://embodied_user:$ENCODED_PASSWORD@localhost:5432/embodied_pulse"

# 执行迁移
python3 migrate_sqlite_to_postgresql.py
```

---

### 方案B：直接切换，让系统自动抓取（如果本地数据不重要）

**步骤**: 执行直接切换脚本，然后等待或手动触发数据抓取

```bash
cd /srv/EmbodiedPulse2026
bash scripts/switch_to_postgresql.sh

# 然后触发数据抓取
# 1. 访问网站点击"刷新论文数据"
# 2. 等待定时任务自动抓取B站数据
```

---

## 📝 数据完整性检查清单

执行迁移后，检查以下项目：

- [ ] 服务器上SQLite文件的数据量
- [ ] PostgreSQL数据库的数据量
- [ ] 两者数据量是否一致
- [ ] 如果PostgreSQL数据少，检查迁移日志
- [ ] 如果使用直接切换方案，检查数据抓取进度

---

## 🔧 如果PostgreSQL数据不完整怎么办？

### 情况1：迁移后数据不完整

**原因**: 服务器上的SQLite文件数据不完整

**解决**:
1. 从本地复制完整的SQLite文件到服务器
2. 重新执行迁移

### 情况2：直接切换后数据为空

**原因**: 这是正常的，需要等待数据抓取

**解决**:
1. 手动触发数据抓取
2. 或等待定时任务自动抓取

---

## 💡 建议

**如果本地有完整数据（1万+论文）**:
- ✅ 使用方案A：从本地复制SQLite文件，然后迁移
- ✅ 这样可以快速获得完整数据

**如果本地数据不重要或可以重新抓取**:
- ✅ 使用方案B：直接切换，让系统自动抓取
- ✅ 更简单，但需要等待抓取完成

---

**文档版本**: v1.0  
**最后更新**: 2025-12-17

