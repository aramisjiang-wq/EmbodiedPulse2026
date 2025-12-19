# B站数据问题修复标准流程

## 原则

1. **所有修复必须先提交到GitHub**
2. **服务器必须从GitHub拉取代码**
3. **使用标准化的脚本和流程**
4. **记录所有操作和结果**

## 标准修复流程

### 步骤1: 本地修复代码

1. 在本地修复代码
2. 测试修复
3. 提交到GitHub

```bash
# 本地操作
git add .
git commit -m "修复描述"
git push origin main
```

### 步骤2: 服务器更新代码

```bash
# SSH登录服务器
ssh root@101.200.222.139

# 进入项目目录
cd /srv/EmbodiedPulse2026

# 拉取最新代码
git pull origin main

# 验证代码更新
git log --oneline -1
```

### 步骤3: 执行诊断（如果需要）

```bash
# 执行完整诊断
bash scripts/full_bilibili_diagnosis.sh

# 或执行快速检查
bash scripts/check_video_play_counts.sh
```

### 步骤4: 应用修复

```bash
# 如果代码有语法错误，先修复
bash scripts/fix_indentation_error.sh

# 验证修复
python3 -m py_compile bilibili_models.py
python3 -m py_compile auth_routes.py
```

### 步骤5: 重启服务

```bash
# 重启服务
systemctl restart embodiedpulse

# 等待启动
sleep 5

# 检查状态
systemctl status embodiedpulse --no-pager -l | head -20
```

### 步骤6: 验证修复

```bash
# 测试API
curl -s "http://localhost:5001/api/bilibili/all?force=1" | python3 -m json.tool | head -30

# 测试管理后台API（需要token）
# 在浏览器中测试
```

## 常见问题修复流程

### 问题1: 代码语法错误

```bash
# 1. 从GitHub拉取最新代码
cd /srv/EmbodiedPulse2026
git pull origin main

# 2. 如果还有错误，使用修复脚本
bash scripts/fix_indentation_error.sh

# 3. 验证
python3 -m py_compile bilibili_models.py

# 4. 重启服务
systemctl restart embodiedpulse
```

### 问题2: 数据过时

```bash
# 1. 检查数据新鲜度
bash scripts/check_video_play_counts.sh

# 2. 如果数据过时，更新数据
python3 fetch_bilibili_data.py --video-count 50

# 3. 如果只是播放量过时，更新播放量
python3 scripts/update_video_play_counts.py --uids 1172054289 --force
```

### 问题3: 服务502错误

```bash
# 1. 检查服务状态
systemctl status embodiedpulse --no-pager -l

# 2. 检查代码语法
python3 -m py_compile bilibili_models.py

# 3. 从GitHub拉取最新代码
git pull origin main

# 4. 重启服务
systemctl restart embodiedpulse

# 5. 如果还不行，执行完整诊断
bash scripts/fix_502_error.sh
```

### 问题4: 前端显示老数据

```bash
# 1. 检查数据库数据是否最新
bash scripts/check_video_play_counts.sh

# 2. 检查API返回的数据
curl -s "http://localhost:5001/api/bilibili/all?force=1" | python3 -m json.tool | head -50

# 3. 清除后端缓存（重启服务）
systemctl restart embodiedpulse

# 4. 如果数据确实过时，更新数据
python3 fetch_bilibili_data.py --video-count 50
```

## 代码更新检查清单

每次修复后，必须检查：

- [ ] 代码已提交到GitHub
- [ ] 服务器已拉取最新代码
- [ ] 代码语法正确
- [ ] 服务已重启
- [ ] API测试通过
- [ ] 前端页面正常显示

## 禁止的操作

❌ **禁止直接在服务器上手动编辑代码**
- 所有代码修改必须在本地完成
- 提交到GitHub后，服务器拉取

❌ **禁止跳过GitHub直接修改服务器代码**
- 这会导致代码不同步
- 无法追踪修改历史

❌ **禁止不测试就重启服务**
- 必须先验证代码语法
- 确保修复正确

## 推荐的完整修复流程

```bash
# ========== 本地操作 ==========
# 1. 修复代码
# 2. 测试修复
# 3. 提交到GitHub
git add .
git commit -m "修复描述"
git push origin main

# ========== 服务器操作 ==========
# 4. SSH登录服务器
ssh root@101.200.222.139

# 5. 拉取最新代码
cd /srv/EmbodiedPulse2026
git pull origin main

# 6. 验证代码更新
git log --oneline -1

# 7. 检查代码语法
python3 -m py_compile bilibili_models.py
python3 -m py_compile auth_routes.py

# 8. 如果语法错误，使用修复脚本
bash scripts/fix_indentation_error.sh

# 9. 重启服务
systemctl restart embodiedpulse
sleep 5

# 10. 检查服务状态
systemctl status embodiedpulse --no-pager -l | head -20

# 11. 测试API
curl -s "http://localhost:5001/api/bilibili/all?force=1" | python3 -m json.tool | head -30

# 12. 如果还有问题，执行完整诊断
bash scripts/full_bilibili_diagnosis.sh
```

## 紧急修复流程（如果GitHub不可用）

如果GitHub暂时不可用，可以临时手动修复，但必须：

1. **记录所有修改**
2. **GitHub恢复后立即提交**
3. **在服务器上创建备份**

```bash
# 1. 备份原文件
cp bilibili_models.py bilibili_models.py.backup.$(date +%Y%m%d_%H%M%S)

# 2. 手动修复（记录修改内容）

# 3. 验证修复
python3 -m py_compile bilibili_models.py

# 4. 重启服务
systemctl restart embodiedpulse

# 5. GitHub恢复后，立即提交修改
git add bilibili_models.py
git commit -m "紧急修复: 描述"
git push origin main
```

## 总结

**核心原则**:
1. ✅ 所有代码修改 → GitHub
2. ✅ 服务器代码 → 从GitHub拉取
3. ✅ 使用标准化脚本
4. ✅ 记录所有操作

**标准流程**:
1. 本地修复 → 提交GitHub
2. 服务器拉取 → 验证 → 重启
3. 测试验证 → 记录结果

