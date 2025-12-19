# B站数据自动更新机制说明

## ✅ 好消息：系统已配置自动更新机制！

根据代码分析，系统已经配置了两层自动更新机制：

### 1. B站数据抓取定时任务

**配置位置：** `app.py:2734-2783`

**功能：**
- 抓取UP主信息和视频列表
- 更新视频基本信息（标题、封面、描述等）
- **已修复：** 播放量更新逻辑已修复，会更新播放量

**默认执行频率：**
- 每6小时执行一次：`AUTO_FETCH_BILIBILI_SCHEDULE=0 */6 * * *`
- 可通过环境变量自定义

**执行内容：**
```python
fetch_all_bilibili_data(video_count=50, delay_between_requests=2.0)
```

### 2. 播放量更新定时任务

**配置位置：** `app.py:2871-2937`

**功能：**
- 专门更新视频播放量数据
- 直接调用B站API获取每个视频的最新播放量
- 增量更新（只更新最近7天未更新的视频）

**默认执行频率：**
- 每天凌晨2点执行：`AUTO_UPDATE_VIDEO_PLAYS_SCHEDULE=0 2 * * *`
- 默认启用：`AUTO_UPDATE_VIDEO_PLAYS_ENABLED=true`
- 可通过环境变量自定义

**执行内容：**
```python
update_video_play_counts(force_update=False)  # 增量更新
```

## 🔧 确保自动更新正常工作的步骤

### 步骤1：检查定时任务配置

在服务器上执行：

```bash
cd /srv/EmbodiedPulse2026
git pull origin main
bash scripts/check_bilibili_auto_update.sh
```

### 步骤2：确保环境变量配置正确

检查 `.env` 文件，确保包含以下配置：

```bash
# 启用定时任务
AUTO_FETCH_ENABLED=true

# B站数据抓取计划（每6小时执行一次）
AUTO_FETCH_BILIBILI_SCHEDULE=0 */6 * * *

# 播放量更新计划（每天凌晨2点执行）
AUTO_UPDATE_VIDEO_PLAYS_SCHEDULE=0 2 * * *

# 播放量更新启用（默认已启用）
AUTO_UPDATE_VIDEO_PLAYS_ENABLED=true
```

### 步骤3：确保服务正在运行

```bash
# 检查服务状态
systemctl status embodiedpulse

# 如果未运行，启动服务
systemctl start embodiedpulse

# 如果配置更改，重启服务
systemctl restart embodiedpulse
```

### 步骤4：验证定时任务是否启动

查看服务日志，确认定时任务已启动：

```bash
# 查看最近的日志
journalctl -u embodiedpulse -n 100 --no-pager | grep -i "定时任务\|scheduler\|B站"

# 应该看到类似输出：
# ✅ 定时任务调度器已启动
# B站数据抓取定时任务已配置: 0 */6 * * *
# 视频播放量更新定时任务已配置: 0 2 * * *
```

## 📋 更新机制说明

### 数据更新流程

```
定时任务1（每6小时）
    ↓
fetch_all_bilibili_data()
    ↓
更新UP主信息 + 视频列表 + 播放量（已修复）
    ↓
数据库更新

定时任务2（每天凌晨2点）
    ↓
update_video_play_counts()
    ↓
直接调用B站API获取每个视频的最新播放量
    ↓
增量更新（只更新最近7天未更新的视频）
    ↓
数据库更新
```

### 更新策略

1. **B站数据抓取（每6小时）：**
   - 更新UP主信息
   - 更新视频列表（新增视频）
   - 更新视频基本信息
   - **已修复：** 更新播放量（如果API返回了数据）

2. **播放量更新（每天凌晨2点）：**
   - 专门更新播放量数据
   - 增量更新（避免触发风控）
   - 新视频（30天内发布）每6小时更新一次
   - 普通视频每7天更新一次

## ✅ 验证自动更新是否正常工作

### 方法1：检查日志

```bash
# 查看定时任务执行日志
journalctl -u embodiedpulse -f | grep -i "B站\|播放量\|定时"
```

### 方法2：检查数据更新时间

```bash
# 检查最近更新的视频
python3 << EOF
from bilibili_models import get_bilibili_session, BilibiliVideo
from datetime import datetime, timedelta
session = get_bilibili_session()
recent = session.query(BilibiliVideo).order_by(
    BilibiliVideo.updated_at.desc()
).limit(5).all()
for v in recent:
    print(f"{v.bvid}: {v.title[:30]} - 更新时间: {v.updated_at}")
session.close()
EOF
```

### 方法3：手动触发测试

```bash
# 测试B站数据抓取（不等待定时任务）
python3 fetch_bilibili_data.py --video-count 10

# 测试播放量更新（不等待定时任务）
python3 scripts/update_video_play_counts.py --force
```

## 🎯 预期结果

### 正常情况

1. **每6小时：**
   - UP主信息更新
   - 新视频添加
   - 视频基本信息更新
   - 播放量更新（如果API返回了数据）

2. **每天凌晨2点：**
   - 所有视频的播放量更新到最新值
   - 新视频（30天内）每6小时更新一次播放量

3. **前端显示：**
   - `https://essay.gradmotion.com/bilibili` - 显示最新数据
   - `https://admin123.gradmotion.com/admin/bilibili` - 显示最新数据

### 如果数据未更新

1. **检查定时任务是否启用：**
   ```bash
   bash scripts/check_bilibili_auto_update.sh
   ```

2. **检查服务日志：**
   ```bash
   journalctl -u embodiedpulse -n 200 | grep -i "错误\|error\|失败\|fail"
   ```

3. **手动触发更新：**
   ```bash
   python3 scripts/update_video_play_counts.py --force
   ```

## 📝 总结

### ✅ 已完成的修复

1. ✅ 修复了 `fetch_bilibili_data.py` 的播放量更新逻辑
2. ✅ 播放量数据已手动更新（331个视频）
3. ✅ 前端显示正常

### ✅ 自动更新机制

1. ✅ B站数据抓取定时任务（每6小时）
2. ✅ 播放量更新定时任务（每天凌晨2点）
3. ✅ 增量更新策略（避免触发风控）

### 🔍 需要确认

1. ⚠️ 定时任务是否启用（`AUTO_FETCH_ENABLED=true`）
2. ⚠️ 服务是否正在运行
3. ⚠️ APScheduler是否已安装

## 🚀 快速检查命令

```bash
cd /srv/EmbodiedPulse2026

# 1. 检查自动更新配置
bash scripts/check_bilibili_auto_update.sh

# 2. 检查服务状态
systemctl status embodiedpulse

# 3. 检查日志
journalctl -u embodiedpulse -n 50 | grep -i "定时\|B站\|播放量"
```

执行这些命令后，如果定时任务已启用且服务正在运行，**数据会自动更新，无需手动干预！**

