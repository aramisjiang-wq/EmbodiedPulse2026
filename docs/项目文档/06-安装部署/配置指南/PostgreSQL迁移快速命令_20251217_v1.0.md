# PostgreSQL迁移快速命令（服务器端）

**版本**: v1.0  
**日期**: 2025-12-17

---

## ⚠️ 重要：密码设置方法

在bash中，`!` 会被解释为历史扩展，需要使用**单引号**包裹密码：

```bash
# ❌ 错误（会报错：event not found）
DB_PASSWORD="MyStrongPass123!@#"

# ✅ 正确（使用单引号）
DB_PASSWORD='MyStrongPass123!@#'
```

---

## 🚀 完整迁移命令（复制粘贴执行）

```bash
cd /srv/EmbodiedPulse2026

# 1. 拉取最新代码
git pull origin main

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 设置密码（⚠️ 使用单引号，替换为你的实际密码）
DB_PASSWORD='MyStrongPass123!@#'  # ⚠️ 修改这里

# 4. 编码密码并设置环境变量
ENCODED_PASSWORD=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$DB_PASSWORD', safe=''))")
export DATABASE_URL="postgresql://embodied_user:$ENCODED_PASSWORD@localhost:5432/embodied_pulse"
export BILIBILI_DATABASE_URL="postgresql://embodied_user:$ENCODED_PASSWORD@localhost:5432/embodied_pulse"

# 5. 验证环境变量
echo "DATABASE_URL已设置: postgresql://embodied_user:***@localhost:5432/embodied_pulse"

# 6. 初始化表结构
python3 init_database.py

# 7. 迁移数据
python3 migrate_sqlite_to_postgresql.py

# 8. 更新.env文件
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
sed -i "s|DATABASE_URL=sqlite:///./papers.db|DATABASE_URL=postgresql://embodied_user:$ENCODED_PASSWORD@localhost:5432/embodied_pulse|" .env

# 9. 更新BILIBILI_DATABASE_URL（如果存在）
if grep -q "BILIBILI_DATABASE_URL" .env; then
    sed -i "s|BILIBILI_DATABASE_URL=.*|BILIBILI_DATABASE_URL=postgresql://embodied_user:$ENCODED_PASSWORD@localhost:5432/embodied_pulse|" .env
else
    echo "BILIBILI_DATABASE_URL=postgresql://embodied_user:$ENCODED_PASSWORD@localhost:5432/embodied_pulse" >> .env
fi

# 10. 验证配置
echo ""
echo "更新后的配置:"
grep DATABASE_URL .env

# 11. 重启服务
systemctl restart embodiedpulse
sleep 5

# 12. 检查服务状态
systemctl status embodiedpulse --no-pager -l

# 13. 验证数据
python3 << 'PYEOF'
import os
import urllib.parse

# 设置密码（⚠️ 与上面保持一致）
DB_PASSWORD = 'MyStrongPass123!@#'  # ⚠️ 修改这里
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
    print(f"\n✅ 论文数据: {papers_count} 篇")
    
    # 检查B站数据
    bilibili_session = get_bilibili_session()
    ups_count = bilibili_session.query(BilibiliUp).count()
    videos_count = bilibili_session.query(BilibiliVideo).count()
    bilibili_session.close()
    print(f"✅ UP主数据: {ups_count} 个")
    print(f"✅ 视频数据: {videos_count} 个")
    
    print("\n✅ 所有数据验证成功！")
    
except Exception as e:
    print(f"\n❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
PYEOF

echo ""
echo "=========================================="
echo "✅ PostgreSQL迁移完成！"
echo "=========================================="
echo ""
echo "下一步:"
echo "  1. 访问网站验证: https://essay.gradmotion.com"
echo "  2. 检查B站页面: https://blibli.gradmotion.com"
echo "  3. 查看服务日志: journalctl -u embodiedpulse -n 50"
```

---

## 🔧 如果遇到问题

### 问题1：bash历史扩展错误

**错误**: `-bash: !@#: event not found`

**解决**: 使用单引号包裹密码
```bash
DB_PASSWORD='MyStrongPass123!@#'  # ✅ 单引号
```

### 问题2：密码变量为空

**检查**:
```bash
echo "密码: $DB_PASSWORD"
echo "编码后: $ENCODED_PASSWORD"
```

### 问题3：环境变量未生效

**解决**: 确保在同一shell会话中执行所有命令，或使用 `export` 导出变量。

---

**文档版本**: v1.0  
**最后更新**: 2025-12-17

