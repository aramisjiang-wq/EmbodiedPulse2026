# 自动部署设置指南

## 部署逻辑确认

✅ **目标部署流程**：
1. 本地生产代码
2. 推送到GitHub (main分支)
3. 服务器自动从GitHub抓取并自动部署

## 自动部署方案

### 方案一：GitHub Actions自动部署（推荐）

**优点**：每次push自动触发，无需服务器定时检查

**设置步骤**：

1. **在GitHub仓库设置Secrets**：
   - 进入仓库 Settings → Secrets and variables → Actions
   - 添加以下Secrets：
     - `SERVER_HOST`: `115.190.77.57`
     - `SERVER_USER`: `root`
     - `SERVER_PASSWORD`: `ash@2025`

2. **工作流已创建**：
   - 文件：`.github/workflows/auto-deploy.yml`
   - 触发条件：push到main分支时自动执行

3. **使用方式**：
   ```bash
   # 本地修改代码后
   git add .
   git commit -m "更新说明"
   git push origin main
   # 推送后，GitHub Actions会自动部署到服务器
   ```

### 方案二：服务器定时检查（备选）

**优点**：不依赖GitHub Actions，服务器自主控制

**设置步骤**：

1. **将自动部署脚本上传到服务器**：
   ```bash
   scp server_auto_deploy.sh root@115.190.77.57:/opt/EmbodiedPulse/
   ```

2. **在服务器上设置cron定时任务**：
   ```bash
   ssh root@115.190.77.57
   crontab -e
   # 添加以下行（每5分钟检查一次）
   */5 * * * * /opt/EmbodiedPulse/server_auto_deploy.sh >> /var/log/embodied-pulse-deploy.log 2>&1
   ```

3. **使用方式**：
   ```bash
   # 本地修改代码后
   git add .
   git commit -m "更新说明"
   git push origin main
   # 5分钟内，服务器会自动检测并部署
   ```

## 当前状态

⚠️ **目前还没有设置自动部署**，需要选择上述方案之一进行配置。

## 推荐方案

**推荐使用方案一（GitHub Actions）**，因为：
- 立即触发，无需等待
- 有部署日志可查看
- 不占用服务器资源做定时检查

## 设置完成后

设置完成后，部署流程将是：
1. ✅ 本地修改代码
2. ✅ `git push origin main`
3. ✅ 自动部署到服务器（无需手动操作）

## 验证自动部署

设置完成后，可以通过以下方式验证：

1. **GitHub Actions方式**：
   - 推送代码后，在GitHub仓库的Actions标签页查看部署日志

2. **服务器定时检查方式**：
   - 查看日志：`tail -f /var/log/embodied-pulse-deploy.log`
   - 查看cron任务：`crontab -l`

