# 修复B站数据字段后如何更新数据

## 问题说明

修复代码已经推送，但前端显示的数据还是旧的，因为：
1. 前端显示的数据来自数据库
2. 数据库中的数据还是旧的（修复前抓取的）
3. 需要重新抓取数据，才能让修复生效

## 解决方案

### 步骤1：在服务器上拉取最新代码

```bash
cd /srv/EmbodiedPulse2026
git pull origin main
```

### 步骤2：重启服务

```bash
systemctl restart embodiedpulse
systemctl status embodiedpulse
```

### 步骤3：重新抓取B站数据

有两种方式：

#### 方式A：手动运行抓取脚本（推荐）

```bash
cd /srv/EmbodiedPulse2026
source venv/bin/activate  # 如果使用虚拟环境
python3 fetch_bilibili_data.py
```

#### 方式B：等待定时任务自动执行

定时任务默认每6小时执行一次，可以通过环境变量 `AUTO_FETCH_BILIBILI_SCHEDULE` 配置。

### 步骤4：验证修复

抓取完成后，运行检查脚本：

```bash
python3 scripts/check_bilibili_stats_fields.py
```

应该看到：
- `videos_count` 显示实际的视频数量（比如 49、50 个）
- `views_count` 显示总播放量（比如 3307108）
- 两个字段的值不再相同

### 步骤5：刷新前端

在前端页面点击"刷新数据"按钮，或者直接刷新页面，应该能看到新的数据。

## 注意事项

1. **抓取需要时间**：12个UP主的数据抓取可能需要几分钟
2. **避免频繁抓取**：B站API有风控，建议间隔至少2秒
3. **检查日志**：如果抓取失败，查看日志文件 `app.log` 或 `flask.log`

## 如果还是看不到新数据

1. **检查代码是否已更新**：
   ```bash
   cd /srv/EmbodiedPulse2026
   git log -1 --oneline
   # 应该看到最新的提交：修复B站总播放量和总视频数字段数据获取问题
   ```

2. **检查服务是否重启**：
   ```bash
   systemctl status embodiedpulse
   # 查看服务状态和最后启动时间
   ```

3. **检查数据库数据**：
   ```bash
   python3 scripts/check_bilibili_stats_fields.py
   ```

4. **清除前端缓存**：
   - 浏览器按 `Ctrl+Shift+R` (Windows) 或 `Cmd+Shift+R` (Mac) 强制刷新
   - 或者清除浏览器缓存

