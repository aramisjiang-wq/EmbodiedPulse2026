# B站数据问题修复标准流程

## 🎯 核心原则

1. **✅ 所有代码修改必须先提交到GitHub**
2. **✅ 服务器必须从GitHub拉取代码（禁止直接修改服务器代码）**
3. **✅ 使用标准化的脚本和流程**
4. **✅ 记录所有操作和结果**

## 📋 标准修复流程

### 本地操作（开发者）

```bash
# 1. 修复代码
# ... 编辑代码 ...

# 2. 测试修复
python3 -m py_compile bilibili_models.py
python3 test_bilibili_issues.py

# 3. 提交到GitHub
git add .
git commit -m "修复描述"
git push origin main
```

### 服务器操作（运维）

```bash
# SSH登录服务器
ssh root@101.200.222.139

# 进入项目目录
cd /srv/EmbodiedPulse2026

# 执行标准修复流程（自动完成所有步骤）
bash scripts/server_fix_standard_flow.sh
```

## 🔧 标准修复流程脚本功能

`scripts/server_fix_standard_flow.sh` 会自动执行：

1. ✅ 从GitHub拉取最新代码
2. ✅ 验证代码更新
3. ✅ 检查代码语法
4. ✅ 测试模块导入
5. ✅ 重启服务
6. ✅ 验证API

## 🚫 禁止的操作

❌ **禁止直接在服务器上手动编辑代码**
- 所有代码修改必须在本地完成
- 提交到GitHub后，服务器拉取

❌ **禁止跳过GitHub直接修改服务器代码**
- 这会导致代码不同步
- 无法追踪修改历史

❌ **禁止不测试就重启服务**
- 必须先验证代码语法
- 确保修复正确

## 📝 常见问题修复

### 问题1: 代码语法错误

```bash
# 在服务器上执行
cd /srv/EmbodiedPulse2026

# 方法1: 使用标准流程（推荐）
bash scripts/server_fix_standard_flow.sh

# 方法2: 手动修复
git pull origin main
python3 -m py_compile bilibili_models.py
systemctl restart embodiedpulse
```

### 问题2: 数据过时

```bash
# 在服务器上执行
cd /srv/EmbodiedPulse2026

# 1. 检查数据新鲜度
bash scripts/check_video_play_counts.sh

# 2. 如果数据过时，更新数据
python3 fetch_bilibili_data.py --video-count 50

# 3. 如果只是播放量过时
python3 scripts/update_video_play_counts.py --uids 1172054289 --force
```

### 问题3: 服务502错误

```bash
# 在服务器上执行
cd /srv/EmbodiedPulse2026

# 使用标准流程（会自动修复）
bash scripts/server_fix_standard_flow.sh

# 如果还不行，执行完整诊断
bash scripts/full_bilibili_diagnosis.sh
```

### 问题4: 前端显示老数据

```bash
# 在服务器上执行
cd /srv/EmbodiedPulse2026

# 1. 检查数据是否最新
bash scripts/check_video_play_counts.sh

# 2. 清除缓存（重启服务）
systemctl restart embodiedpulse

# 3. 如果数据确实过时，更新数据
python3 fetch_bilibili_data.py --video-count 50
```

## 📊 完整诊断

如果需要完整诊断，执行：

```bash
cd /srv/EmbodiedPulse2026
bash scripts/full_bilibili_diagnosis.sh
```

诊断脚本会检查：
1. 服务状态
2. 代码语法
3. 数据库连接和数据完整性
4. 数据新鲜度
5. API响应
6. 定时任务
7. 缓存状态

## ✅ 修复后检查清单

每次修复后，必须检查：

- [ ] 代码已提交到GitHub
- [ ] 服务器已拉取最新代码（`git log --oneline -1`）
- [ ] 代码语法正确（`python3 -m py_compile`）
- [ ] 服务已重启（`systemctl status embodiedpulse`）
- [ ] API测试通过（`curl http://localhost:5001/api/bilibili/all?force=1`）
- [ ] 前端页面正常显示

## 🆘 紧急情况

如果GitHub暂时不可用，可以临时手动修复，但必须：

1. **记录所有修改**
2. **GitHub恢复后立即提交**
3. **在服务器上创建备份**

```bash
# 1. 备份
cp bilibili_models.py bilibili_models.py.backup.$(date +%Y%m%d_%H%M%S)

# 2. 手动修复（记录修改内容）

# 3. 验证
python3 -m py_compile bilibili_models.py

# 4. 重启
systemctl restart embodiedpulse

# 5. GitHub恢复后立即提交
git add bilibili_models.py
git commit -m "紧急修复: 描述"
git push origin main
```

## 📚 相关脚本

- `scripts/server_fix_standard_flow.sh` - 标准修复流程（推荐使用）
- `scripts/full_bilibili_diagnosis.sh` - 完整诊断
- `scripts/check_video_play_counts.sh` - 播放量检查
- `scripts/fix_502_error.sh` - 502错误修复
- `scripts/start_server.sh` - 启动服务

## 📞 需要帮助？

如果标准流程无法解决问题，请提供：

1. 完整诊断报告（`bash scripts/full_bilibili_diagnosis.sh`）
2. 错误日志（`journalctl -u embodiedpulse -n 100`）
3. 浏览器开发者工具中的API响应

