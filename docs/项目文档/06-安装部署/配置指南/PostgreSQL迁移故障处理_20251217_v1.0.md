# PostgreSQL迁移故障处理

**版本**: v1.0  
**日期**: 2025-12-17

---

## 问题：Git Pull冲突

**错误信息**:
```
error: The following untracked working tree files would be overwritten by merge:
        scripts/setup_postgresql.sh
Please move or remove them before you merge.
```

**原因**: 服务器上存在未跟踪的文件，与GitHub上的文件冲突。

---

## 解决方案

### 方法1：备份并删除本地文件（推荐）

```bash
cd /srv/EmbodiedPulse2026

# 备份本地文件
cp scripts/setup_postgresql.sh scripts/setup_postgresql.sh.backup

# 删除本地文件
rm scripts/setup_postgresql.sh

# 重新拉取代码
git pull origin main
```

### 方法2：强制覆盖本地文件

```bash
cd /srv/EmbodiedPulse2026

# 删除本地文件
rm scripts/setup_postgresql.sh

# 重新拉取代码
git pull origin main
```

### 方法3：使用stash（如果文件有修改）

```bash
cd /srv/EmbodiedPulse2026

# 暂存本地文件
git stash

# 拉取代码
git pull origin main

# 如果需要恢复本地修改
git stash pop
```

---

## 继续PostgreSQL迁移

解决冲突后，继续执行：

```bash
# 1. 确保脚本有执行权限
chmod +x scripts/setup_postgresql.sh

# 2. 检查脚本中的密码（如果需要修改）
nano scripts/setup_postgresql.sh
# 找到第11行，修改 DB_PASSWORD

# 3. 运行脚本
bash scripts/setup_postgresql.sh
```

---

**文档版本**: v1.0  
**最后更新**: 2025-12-17

