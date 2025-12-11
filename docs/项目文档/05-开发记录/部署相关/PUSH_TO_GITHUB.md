# 推送到GitHub仓库指南

## 当前状态
- ✅ 所有代码已提交到本地仓库
- ✅ .gitignore 已更新（排除数据库、环境变量等敏感文件）
- ⚠️ 需要推送到GitHub

## 方案一：使用现有仓库（需要权限）

如果 `jiangranlv/robotics_arXiv_daily` 是你的仓库，需要配置正确的Git凭据：

### 使用SSH（推荐）
```bash
# 1. 检查SSH密钥
ls -la ~/.ssh

# 2. 如果没有SSH密钥，生成一个
ssh-keygen -t ed25519 -C "your_email@example.com"

# 3. 添加SSH密钥到GitHub账户
cat ~/.ssh/id_ed25519.pub
# 复制输出，在GitHub Settings > SSH and GPG keys 中添加

# 4. 更改远程仓库URL为SSH
git remote set-url origin git@github.com:jiangranlv/robotics_arXiv_daily.git

# 5. 推送代码
git push origin main
```

### 使用Personal Access Token
```bash
# 1. 在GitHub创建Personal Access Token
# Settings > Developer settings > Personal access tokens > Generate new token
# 权限：repo（全部）

# 2. 使用token推送
git remote set-url origin https://YOUR_TOKEN@github.com/jiangranlv/robotics_arXiv_daily.git
git push origin main
```

## 方案二：创建新仓库（推荐）

### 步骤1：在GitHub创建新仓库
1. 访问 https://github.com/new
2. 仓库名称：`robotics-arxiv-daily`（或你喜欢的名字）
3. 描述：`Embodied AI ArXiv Daily - 具身领域前沿论文每日更新`
4. 选择 Public 或 Private
5. **不要**初始化README、.gitignore或license（我们已经有了）
6. 点击 "Create repository"

### 步骤2：添加新远程仓库并推送
```bash
# 1. 移除旧的远程仓库（如果需要）
git remote remove origin

# 2. 添加新的远程仓库（替换YOUR_USERNAME和REPO_NAME）
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# 3. 推送代码
git push -u origin main
```

### 步骤3：验证
访问 `https://github.com/YOUR_USERNAME/REPO_NAME` 查看代码

## 方案三：使用GitHub CLI（最简单）

如果安装了GitHub CLI：
```bash
# 1. 登录GitHub
gh auth login

# 2. 创建仓库并推送
gh repo create robotics-arxiv-daily --public --source=. --remote=origin --push
```

## 已提交的文件清单

✅ **核心代码**
- `app.py` - Flask Web应用
- `models.py` - 数据库模型
- `daily_arxiv.py` - 论文抓取逻辑
- `save_paper_to_db.py` - 数据库保存
- `utils.py` - 工具函数

✅ **前端**
- `templates/index.html` - HTML模板
- `static/css/style.css` - 样式文件
- `static/js/app.js` - JavaScript逻辑

✅ **配置**
- `config.yaml` - 配置文件
- `requirements.txt` - Python依赖
- `gunicorn_config.py` - Gunicorn配置
- `Dockerfile` - Docker配置
- `docker-compose.yml` - Docker Compose配置

✅ **部署**
- `deploy.sh` - 部署脚本
- `Procfile` - Heroku配置

✅ **文档**
- `docs/项目文档/` - 完整项目文档
- `README.md` - 项目说明

❌ **已排除（.gitignore）**
- `*.db` - 数据库文件
- `.env` - 环境变量
- `venv/` - 虚拟环境
- `*.log` - 日志文件

## 注意事项

1. **数据库文件**：`papers.db` 已排除，需要单独备份或使用数据库迁移
2. **环境变量**：`.env` 文件已排除，需要在部署时配置
3. **敏感信息**：确保 `config.yaml` 中没有敏感信息（API密钥等）

