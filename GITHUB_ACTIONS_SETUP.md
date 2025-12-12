# GitHub Actions 自动部署设置指南

## 📋 设置步骤

### 第一步：在GitHub仓库添加Secrets

1. 打开GitHub仓库：https://github.com/aramisjiang-wq/EmbodiedPulse2026
2. 点击 **Settings**（设置）
3. 在左侧菜单找到 **Secrets and variables** → **Actions**
4. 点击 **New repository secret** 按钮，依次添加以下三个Secrets：

#### Secret 1: SERVER_HOST
- **Name**: `SERVER_HOST`
- **Value**: `115.190.77.57`

#### Secret 2: SERVER_USER
- **Name**: `SERVER_USER`
- **Value**: `root`

#### Secret 3: SERVER_PASSWORD
- **Name**: `SERVER_PASSWORD`
- **Value**: `ash@2025`

### 第二步：确认工作流文件已存在

工作流文件位置：`.github/workflows/auto-deploy.yml`

如果文件不存在，需要先推送到GitHub：
```bash
git add .github/workflows/auto-deploy.yml
git commit -m "添加GitHub Actions自动部署工作流"
git push origin main
```

### 第三步：测试自动部署

1. **推送代码触发部署**：
   ```bash
   # 做一个小改动（比如修改README）
   echo "# 测试自动部署" >> README.md
   git add .
   git commit -m "测试自动部署"
   git push origin main
   ```

2. **查看部署状态**：
   - 在GitHub仓库页面，点击 **Actions** 标签
   - 查看 "Auto Deploy to Server" 工作流的执行状态
   - 点击进入查看详细日志

3. **验证部署结果**：
   - 访问：http://115.190.77.57:5001
   - 确认服务正常运行

## 🎯 部署流程

设置完成后，每次部署流程：

1. ✅ **本地修改代码**
2. ✅ **提交并推送**：
   ```bash
   git add .
   git commit -m "更新说明"
   git push origin main
   ```
3. ✅ **GitHub Actions自动触发部署**
4. ✅ **服务器自动更新并重启服务**

## 📊 工作流说明

### 触发条件
- ✅ Push到 `main` 分支时自动触发
- ✅ 可以手动在Actions页面触发
- ✅ 忽略文档文件的变更（避免不必要的部署）

### 部署步骤
1. 拉取最新代码
2. 停止旧容器
3. 构建新镜像
4. 启动新容器
5. 初始化数据库（如果需要）
6. 检查服务状态

### 超时设置
- 工作流超时：15分钟
- SSH连接超时：10分钟

## 🔍 查看部署日志

### 在GitHub上查看
1. 进入仓库的 **Actions** 标签
2. 点击最新的工作流运行
3. 查看 "Deploy to server via SSH" 步骤的日志

### 在服务器上查看
```bash
ssh root@115.190.77.57
cd /opt/EmbodiedPulse
docker-compose logs -f web
```

## ⚠️ 注意事项

1. **首次部署**：如果服务器上还没有项目，工作流会自动创建目录并克隆代码
2. **数据库**：数据库初始化只在首次部署时执行，后续会跳过
3. **服务中断**：部署过程中服务会短暂中断（约20-30秒）
4. **失败处理**：如果部署失败，可以在Actions页面查看详细错误信息

## 🛠️ 故障排查

### 部署失败
1. 检查GitHub Secrets是否正确设置
2. 检查服务器SSH连接是否正常
3. 查看Actions日志中的错误信息

### 服务无法访问
1. 检查容器状态：`docker-compose ps`
2. 查看容器日志：`docker-compose logs web`
3. 检查防火墙：确保5001端口开放

### 手动触发部署
如果自动部署失败，可以手动触发：
1. 进入GitHub仓库的 **Actions** 标签
2. 选择 "Auto Deploy to Server" 工作流
3. 点击 **Run workflow** 按钮

## ✅ 设置完成检查清单

- [ ] GitHub Secrets已添加（SERVER_HOST, SERVER_USER, SERVER_PASSWORD）
- [ ] 工作流文件已推送到GitHub
- [ ] 测试推送已成功触发部署
- [ ] 服务可以正常访问

设置完成后，你就可以享受自动部署的便利了！🚀

