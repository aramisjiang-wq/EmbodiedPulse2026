# PostgreSQL直接切换方案（无需迁移）

**版本**: v1.0  
**日期**: 2025-12-17  
**适用场景**: 服务器上数据量少或可以重新抓取

---

## 💡 为什么直接切换更简单？

如果服务器上的数据：
- ✅ 数据量少（< 1000条）
- ✅ 可以重新抓取
- ✅ 或者数据不重要

**直接切换到PostgreSQL，让系统自动重新抓取数据，比迁移简单100倍！**

---

## 🚀 超简单切换步骤（5分钟搞定）

### 步骤1：安装PostgreSQL（如果还没安装）

```bash
# 安装PostgreSQL
apt update
apt install -y postgresql postgresql-contrib

# 启动服务
systemctl start postgresql
systemctl enable postgresql
```

### 步骤2：创建数据库和用户

```bash
# 切换到postgres用户
sudo -u postgres psql

# 在PostgreSQL命令行中执行（替换密码）
CREATE DATABASE embodied_pulse;
CREATE USER embodied_user WITH PASSWORD 'MyStrongPass123!@#';
GRANT ALL PRIVILEGES ON DATABASE embodied_pulse TO embodied_user;
ALTER USER embodied_user CREATEDB;
\q
```

### 步骤3：安装Python依赖

```bash
cd /srv/EmbodiedPulse2026
source venv/bin/activate
pip install psycopg2-binary
```

### 步骤4：更新.env文件（最关键！）

```bash
cd /srv/EmbodiedPulse2026

# 备份.env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# 设置密码（使用单引号）
DB_PASSWORD='MyStrongPass123!@#'

# 编码密码
ENCODED_PASSWORD=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$DB_PASSWORD', safe=''))")

# 更新.env文件
cat >> .env << EOF

# PostgreSQL配置（直接切换，无需迁移）
DATABASE_URL=postgresql://embodied_user:$ENCODED_PASSWORD@localhost:5432/embodied_pulse
BILIBILI_DATABASE_URL=postgresql://embodied_user:$ENCODED_PASSWORD@localhost:5432/embodied_pulse
EOF

# 如果.env中已有DATABASE_URL，先删除旧配置
sed -i '/^DATABASE_URL=/d' .env
sed -i '/^BILIBILI_DATABASE_URL=/d' .env

# 添加新配置
echo "DATABASE_URL=postgresql://embodied_user:$ENCODED_PASSWORD@localhost:5432/embodied_pulse" >> .env
echo "BILIBILI_DATABASE_URL=postgresql://embodied_user:$ENCODED_PASSWORD@localhost:5432/embodied_pulse" >> .env

# 验证
cat .env | grep DATABASE_URL
```

### 步骤5：初始化PostgreSQL表结构

```bash
cd /srv/EmbodiedPulse2026
source venv/bin/activate

# 设置环境变量（确保生效）
export DATABASE_URL="postgresql://embodied_user:$ENCODED_PASSWORD@localhost:5432/embodied_pulse"
export BILIBILI_DATABASE_URL="postgresql://embodied_user:$ENCODED_PASSWORD@localhost:5432/embodied_pulse"

# 初始化所有表结构
python3 init_database.py
```

### 步骤6：重启服务

```bash
systemctl restart embodiedpulse
sleep 5
systemctl status embodiedpulse
```

### 步骤7：触发数据抓取（让系统自动抓取数据）

```bash
# 方式1：手动触发论文抓取（通过网站）
# 访问 https://essay.gradmotion.com，点击"刷新论文数据"按钮

# 方式2：手动触发B站数据抓取（通过API）
curl -X POST http://127.0.0.1:5001/api/bilibili/fetch

# 方式3：等待定时任务自动抓取（如果已配置）
# 检查定时任务状态
journalctl -u embodiedpulse | grep -i "scheduled\|fetch"
```

---

## ✅ 完成！

**就这么简单！** 不需要迁移，系统会自动重新抓取数据。

---

## 📊 数据抓取时间估算

- **论文数据**: 约30-60分钟（取决于关键词数量）
- **B站数据**: 约10-20分钟（取决于UP主数量）

**建议**: 
- 先触发论文抓取，让它慢慢跑
- 再触发B站数据抓取
- 或者等待定时任务自动执行

---

## 🔍 验证数据

```bash
# 检查数据量
python3 scripts/check_current_database.py

# 或者直接查询
python3 << 'EOF'
import os
from dotenv import load_dotenv
load_dotenv()

from models import get_session, Paper
from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo

session = get_session()
papers_count = session.query(Paper).count()
session.close()
print(f"论文: {papers_count} 篇")

bilibili_session = get_bilibili_session()
ups_count = bilibili_session.query(BilibiliUp).count()
videos_count = bilibili_session.query(BilibiliVideo).count()
bilibili_session.close()
print(f"UP主: {ups_count} 个")
print(f"视频: {videos_count} 个")
EOF
```

---

## ⚠️ 注意事项

1. **SQLite文件保留**: 旧的SQLite文件（`papers.db`, `bilibili.db`）会保留，作为备份
2. **数据重新抓取**: 所有数据会重新抓取，需要一些时间
3. **定时任务**: 确保定时任务已配置，会自动更新数据

---

## 🎯 为什么这个方案更好？

| 方案 | 迁移方案 | 直接切换方案 |
|------|---------|------------|
| 步骤数 | 10+ 步 | 7 步 |
| 复杂度 | 高（需要处理数据迁移） | 低（只需配置） |
| 时间 | 1-2小时 | 5-10分钟 |
| 风险 | 中等（数据迁移可能出错） | 低（自动抓取） |
| 适用场景 | 数据量大且重要 | 数据可重新抓取 |

---

**文档版本**: v1.0  
**最后更新**: 2025-12-17

