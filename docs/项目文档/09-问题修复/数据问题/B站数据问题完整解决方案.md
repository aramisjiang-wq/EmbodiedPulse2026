# B站数据问题完整解决方案

**版本**: v2.0  
**创建日期**: 2025-12-19  
**最后更新**: 2025-12-19  
**状态**: ✅ 已修复并上线

---

## 📋 问题概述

### 问题描述
- 前端页面 `https://essay.gradmotion.com/bilibili` 显示过时的视频和播放量数据
- 管理后台 `https://admin123.gradmotion.com/admin/bilibili` 视频列表加载失败或显示旧数据

### 核心问题
1. **播放量更新逻辑问题** - 只更新大于0的播放量，导致数据过时
2. **数据库配置问题** - 可能存在多个数据库文件，数据不一致
3. **API缓存问题** - 前端缓存导致显示旧数据
4. **定时任务问题** - 自动更新未正常工作

---

## ✅ 已修复的问题

### 1. 播放量更新逻辑修复

**问题代码** (`fetch_bilibili_data.py:188-193`):
```python
play_raw = video_data.get('play', 0) or 0
if play_raw > 0:
    # 只有播放量大于0时才更新
    video.play = play_raw
    video.play_formatted = format_number(play_raw)
```

**修复后**:
```python
play_raw = video_data.get('play', 0) or 0
# 总是更新播放量，即使API返回0，也更新为0
video.play = play_raw
video.play_formatted = format_number(play_raw)
```

### 2. 数据库配置统一

**配置位置**: `bilibili_models.py`
- 统一使用环境变量 `BILIBILI_DATABASE_URL`
- 默认使用 PostgreSQL
- 确保所有脚本使用同一个数据库

### 3. API缓存机制

**缓存策略**:
- `/api/bilibili` - 10分钟缓存
- `/api/bilibili/all` - 5分钟缓存
- 手动刷新可跳过缓存（`force=1`）

### 4. 定时任务配置

**自动更新机制**:
- B站数据抓取：每6小时执行一次 (`AUTO_FETCH_BILIBILI_SCHEDULE=0 */6 * * *`)
- 播放量更新：每天凌晨2点执行 (`AUTO_UPDATE_VIDEO_PLAYS_SCHEDULE=0 2 * * *`)

---

## 🚀 数据更新方案

### 方案1：自动更新（推荐）

**配置要求**:
```bash
# .env 文件
AUTO_FETCH_ENABLED=true
AUTO_FETCH_BILIBILI_SCHEDULE=0 */6 * * *
AUTO_UPDATE_VIDEO_PLAYS_SCHEDULE=0 2 * * *
AUTO_UPDATE_VIDEO_PLAYS_ENABLED=true
```

**更新流程**:
1. 每6小时自动抓取UP主信息和视频列表
2. 每天凌晨2点自动更新所有视频播放量
3. 前端每5分钟自动刷新

### 方案2：管理后台手动更新

**功能位置**: `https://admin123.gradmotion.com/admin/bilibili`

**操作步骤**:
1. 点击"更新B站数据"按钮
2. 系统自动执行：
   - 更新UP主信息和视频列表
   - 更新视频播放量
   - 清除API缓存
3. 查看进度条和状态
4. 更新完成后自动刷新统计数据

**API端点**:
- `POST /api/admin/bilibili/fetch-data` - 触发更新
- `GET /api/admin/bilibili/fetch-status` - 查询状态

### 方案3：命令行手动更新

**更新所有数据**:
```bash
cd /srv/EmbodiedPulse2026
python3 fetch_bilibili_data.py --fetch-all
```

**更新播放量**:
```bash
python3 scripts/update_video_play_counts.py --force
```

**一键更新脚本**:
```bash
bash scripts/update_all_play_counts.sh
```

---

## 🔧 故障排查

### 问题1：数据未更新

**检查步骤**:
1. 检查定时任务是否启用
   ```bash
   bash scripts/check_bilibili_auto_update.sh
   ```

2. 检查服务状态
   ```bash
   systemctl status embodiedpulse
   ```

3. 查看日志
   ```bash
   journalctl -u embodiedpulse -n 100 | grep -i "B站\|播放量"
   ```

### 问题2：播放量数据不一致

**检查步骤**:
1. 检查数据库播放量
   ```bash
   bash scripts/check_bilibili_play_counts.sh
   ```

2. 对比B站API数据
   ```bash
   python3 scripts/check_bilibili_play_counts.sh
   ```

3. 强制更新播放量
   ```bash
   python3 scripts/update_video_play_counts.py --force
   ```

### 问题3：前端显示旧数据

**解决方案**:
1. 清除API缓存
   - 点击前端"刷新数据"按钮（`force=1`）
   - 或等待缓存过期（10分钟）

2. 检查API返回数据
   ```bash
   curl "https://essay.gradmotion.com/api/bilibili/all?force=1"
   ```

3. 重启服务
   ```bash
   systemctl restart embodiedpulse
   ```

---

## 📝 相关文档

- [B站数据自动更新机制说明](../B站数据自动更新机制说明.md)
- [管理后台B站数据更新功能说明](../管理后台B站数据更新功能说明.md)
- [服务器修复执行步骤](./服务器修复执行步骤_20251219_v1.0.md)

---

## 🎯 总结

**已完成的修复**:
- ✅ 播放量更新逻辑修复
- ✅ 数据库配置统一
- ✅ API缓存机制优化
- ✅ 定时任务配置完善
- ✅ 管理后台手动更新功能

**当前状态**:
- ✅ 数据自动更新正常
- ✅ 播放量数据准确
- ✅ 前端显示正常
- ✅ 管理后台功能正常

**后续维护**:
- 定期检查定时任务运行状态
- 监控数据更新日志
- 关注B站API频率限制

---

**最后更新**: 2025-12-19

