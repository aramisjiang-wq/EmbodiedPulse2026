# PostgreSQL迁移问题解决指南

**版本**: v1.0  
**日期**: 2025-12-17

---

## 问题1：索引重复创建错误

**错误信息**:
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DuplicateTable) relation "idx_created_at" already exists
```

**原因**: PostgreSQL中索引已存在，但`create_all()`尝试重新创建。

**解决方案**: 已修复所有`init_*_db()`函数，添加了`checkfirst=True`参数和异常处理。

---

## 问题2：脚本文件不存在

**错误信息**:
```
bash: scripts/setup_postgresql.sh: No such file or directory
```

**原因**: 服务器上文件被删除，但git pull显示"Already up to date"。

**解决方案**:

```bash
cd /srv/EmbodiedPulse2026

# 方法1：强制重置到远程版本
git fetch origin
git reset --hard origin/main

# 方法2：或者直接克隆脚本文件
git checkout origin/main -- scripts/setup_postgresql.sh
chmod +x scripts/setup_postgresql.sh
```

---

## 继续迁移步骤

修复后，继续执行：

```bash
cd /srv/EmbodiedPulse2026

# 1. 拉取最新代码（包含修复）
git pull origin main

# 2. 如果脚本不存在，强制拉取
git checkout origin/main -- scripts/setup_postgresql.sh
chmod +x scripts/setup_postgresql.sh

# 3. 设置密码编码环境变量
ENCODED_PASSWORD=$(python3 -c "import urllib.parse; print(urllib.parse.quote('MyStrongPass123!@#', safe=''))")
export DATABASE_URL="postgresql://embodied_user:$ENCODED_PASSWORD@localhost:5432/embodied_pulse"

# 4. 重新初始化数据库（现在不会报索引错误了）
python3 init_database.py

# 5. 迁移数据
python3 migrate_sqlite_to_postgresql.py

# 6. 更新.env文件
ENCODED_PASSWORD=$(python3 -c "import urllib.parse; print(urllib.parse.quote('MyStrongPass123!@#', safe=''))")
sed -i "s|DATABASE_URL=sqlite:///./papers.db|DATABASE_URL=postgresql://embodied_user:$ENCODED_PASSWORD@localhost:5432/embodied_pulse|" .env

# 7. 重启服务
systemctl restart embodiedpulse
```

---

**文档版本**: v1.0  
**最后更新**: 2025-12-17

