# GitHub Actions 自动部署配置教程（小白版）

## 一、什么是 GitHub Actions？

GitHub Actions 是 GitHub 提供的自动化工具，可以让你在推送代码到 GitHub 后，自动在服务器上执行部署操作。

**简单理解：**
- 你在本地修改代码 → 推送到 GitHub
- GitHub 自动检测到代码更新
- GitHub 自动登录你的服务器
- GitHub 自动执行部署脚本（拉取代码、重启服务等）

---

## 二、配置前的准备工作

### 2.1 生成 SSH 密钥对

SSH 密钥就像一把"钥匙"，让 GitHub 可以安全地登录你的服务器。

**在服务器上执行以下命令：**

```bash
# 1. 登录服务器
ssh root@101.200.222.139

# 2. 检查是否已有密钥（如果已有，可以跳过生成步骤）
ls -la ~/.ssh/

# 3. 生成新的 SSH 密钥对（专门用于 GitHub Actions）
ssh-keygen -t rsa -b 4096 -C "github-actions-deploy" -f ~/.ssh/github_actions

# 按提示操作：
# - 提示输入密码时，直接按 Enter（不设密码）
# - 再次确认密码时，直接按 Enter

# 4. 将公钥添加到 authorized_keys（允许这个密钥登录）
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys

# 5. 设置正确的权限（安全要求）
chmod 600 ~/.ssh/github_actions
chmod 644 ~/.ssh/authorized_keys

# 6. 查看私钥内容（复制这个，稍后要用）
cat ~/.ssh/github_actions
```

**重要：** 复制上面第 6 步显示的私钥内容（从 `-----BEGIN OPENSSH PRIVATE KEY-----` 开始，到 `-----END OPENSSH PRIVATE KEY-----` 结束），保存到一个文本文件中，稍后要添加到 GitHub。

---

## 三、在 GitHub 上配置 Secrets

### 3.1 打开 GitHub 仓库设置

1. **打开浏览器**，访问：`https://github.com/aramisjiang-wq/EmbodiedPulse2026`
2. **点击仓库顶部的 `Settings` 标签**（在 `Code`、`Issues` 等标签旁边）
3. **在左侧菜单中找到 `Secrets and variables`** → 点击 `Actions`

### 3.2 添加第一个 Secret：SERVER_HOST

1. **点击右上角的 `New repository secret` 按钮**
2. **填写信息：**
   - **Name（名称）**：`SERVER_HOST`
   - **Secret（值）**：`101.200.222.139`
3. **点击 `Add secret`**

### 3.3 添加第二个 Secret：SERVER_USER

1. **再次点击 `New repository secret`**
2. **填写信息：**
   - **Name（名称）**：`SERVER_USER`
   - **Secret（值）**：`root`
3. **点击 `Add secret`**

### 3.4 添加第三个 Secret：SERVER_SSH_PORT

1. **再次点击 `New repository secret`**
2. **填写信息：**
   - **Name（名称）**：`SERVER_SSH_PORT`
   - **Secret（值）**：`22`
3. **点击 `Add secret`**

### 3.5 添加第四个 Secret：SERVER_SSH_KEY（最重要）

1. **再次点击 `New repository secret`**
2. **填写信息：**
   - **Name（名称）**：`SERVER_SSH_KEY`
   - **Secret（值）**：粘贴之前复制的**完整私钥内容**（包括 `-----BEGIN` 和 `-----END` 这两行）
3. **点击 `Add secret`**

**⚠️ 注意事项：**
- 私钥内容很长，确保完整复制（包括开头和结尾的标记行）
- 不要有多余的空格或换行
- 这是最敏感的信息，不要泄露给任何人

---

## 四、验证配置

### 4.1 检查 Secrets 是否添加成功

在 GitHub 的 `Secrets and variables` → `Actions` 页面，你应该能看到 4 个 secrets：
- ✅ `SERVER_HOST`
- ✅ `SERVER_USER`
- ✅ `SERVER_SSH_PORT`
- ✅ `SERVER_SSH_KEY`

### 4.2 测试自动部署

1. **在本地做一个小的修改**（比如在 README 中添加一行注释）
2. **提交并推送：**
   ```bash
   cd "/Users/dong/Documents/Cursor/Embodied Pulse"
   git add .
   git commit -m "test: 测试自动部署"
   git push origin main
   ```
3. **在 GitHub 上查看部署状态：**
   - 回到 GitHub 仓库页面
   - 点击顶部的 `Actions` 标签
   - 你应该能看到一个新的工作流运行（显示黄色或绿色的圆点）
   - 点击这个工作流，查看详细日志

### 4.3 查看部署日志

在 `Actions` 页面：
1. 点击最新的工作流运行
2. 点击 `deploy` 任务
3. 展开 `SSH Deploy to Production` 步骤
4. 查看日志输出

**成功标志：**
- 看到 `[CI] 开始部署 EmbodiedPulse2026 ...`
- 看到 `[deploy] 拉取最新代码...`
- 看到 `[deploy] 部署完成。`
- 看到 `[CI] 部署脚本执行完毕。`

**如果失败：**
- 检查日志中的错误信息
- 常见问题：
  - SSH 连接失败 → 检查 `SERVER_HOST`、`SERVER_USER`、`SERVER_SSH_KEY`
  - 权限错误 → 检查服务器上的文件权限
  - 脚本路径错误 → 检查 `scripts/deploy_server.sh` 是否存在

---

## 五、日常使用

配置完成后，以后每次部署只需要：

1. **在本地修改代码**
2. **提交并推送：**
   ```bash
   git add .
   git commit -m "你的提交信息"
   git push origin main
   ```
3. **GitHub 会自动部署**（通常 1-2 分钟完成）
4. **在 GitHub Actions 页面查看部署状态**

---

## 六、常见问题

### Q1: 如何查看部署是否成功？

**方法1：** 在 GitHub Actions 页面查看工作流状态（绿色 ✓ 表示成功）

**方法2：** 在服务器上检查：
```bash
ssh root@101.200.222.139
cd /srv/EmbodiedPulse2026
git log -1  # 查看最新提交
systemctl status embodiedpulse  # 查看服务状态
```

### Q2: 部署失败怎么办？

1. **查看 GitHub Actions 日志**，找到错误信息
2. **常见错误：**
   - `Permission denied` → SSH 密钥权限问题
   - `Connection refused` → 服务器 SSH 服务未开启
   - `No such file or directory` → 脚本路径错误

### Q3: 如何手动部署（如果自动部署失败）？

```bash
# 在服务器上手动执行
ssh root@101.200.222.139
cd /srv/EmbodiedPulse2026
git pull origin main
systemctl restart embodiedpulse
```

### Q4: 如何禁用自动部署？

在 GitHub 仓库的 `Settings` → `Actions` → `General` 中，可以禁用 Actions。

---

## 七、安全建议

1. **不要将私钥提交到代码仓库**
2. **定期更换 SSH 密钥**（可选，但建议）
3. **限制服务器 SSH 访问**（只允许特定 IP）
4. **使用非 root 用户**（生产环境建议）

---

## 完成标志

✅ 4 个 Secrets 都已添加  
✅ 测试推送后，GitHub Actions 显示成功  
✅ 服务器上的代码已自动更新  

恭喜！自动部署配置完成！🎉

