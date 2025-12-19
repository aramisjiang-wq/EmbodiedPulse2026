# Embodied Pulse - 项目说明

**版本**: v2.0  
**创建日期**: 2025-12-17  
**最后更新**: 2025-12-19  
**项目状态**: ✅ 已上线运行中

---

## 📋 项目简介

**Embodied Pulse（具身脉搏）** 是一个专注于具身智能和机器人领域的ArXiv论文自动抓取、分类和展示平台，同时提供B站视频内容追踪和管理功能。

**核心价值**：
- ✅ 自动抓取和分类具身智能领域的最新论文
- ✅ 追踪B站UP主和视频内容，了解行业动态
- ✅ 提供完整的管理平台，方便数据维护
- ✅ 支持自动定时更新，无需人工干预

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- PostgreSQL 15+（生产环境）
- Docker 20.10+（可选）

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/aramisjiang-wq/EmbodiedPulse2026.git
cd EmbodiedPulse2026
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp env.example .env
# 编辑 .env 文件，配置数据库连接等信息
```

4. **初始化数据库**
```bash
python3 init_database.py
```

5. **启动应用**
```bash
# 开发环境
python3 app.py

# 生产环境（推荐）
gunicorn -c gunicorn_config.py app:app
```

### Docker部署（推荐）

```bash
docker-compose up -d
```

---

## 📚 功能特性

### 具身论文页面
- 33个精准分类标签
- 350+个检索词
- 研究方向活跃度可视化
- 活跃作者排行榜
- 实时进度显示
- 搜索和筛选功能
- 新论文红点提示

### 具身视频Hub页面
- B站UP主信息追踪（12个UP主）
- 视频发布趋势可视化
- 月度播放量统计对比
- 年度总播放量统计
- TOP 5发布数量排行
- 7天内最新视频
- 响应式布局设计

### 管理平台
- 用户管理
- 论文管理
- 视频管理（支持手动更新）
- 日志监控
- 统计仪表盘

### 用户认证系统
- 飞书OAuth登录
- 管理员登录
- 个人中心
- JWT Token认证

---

## 🌐 访问地址

### 用户端
- **具身论文页面**：https://essay.gradmotion.com/
- **具身视频Hub**：https://essay.gradmotion.com/bilibili
- **登录页面**：https://login.gradmotion.com/login

### 管理端
- **管理后台**：https://admin123.gradmotion.com/admin/
- **仪表盘**：https://admin123.gradmotion.com/admin/dashboard
- **用户管理**：https://admin123.gradmotion.com/admin/users
- **论文管理**：https://admin123.gradmotion.com/admin/papers
- **视频管理**：https://admin123.gradmotion.com/admin/bilibili
- **日志监控**：https://admin123.gradmotion.com/admin/logs

---

## 📊 数据统计

- **论文数据**：14,000+ 篇论文
- **视频数据**：500+ 个视频
- **UP主数据**：12 个UP主
- **分类标签**：33 个精准分类
- **检索词**：350+ 个

---

## 🔄 数据更新

### 自动更新
- **论文数据**：每小时整点自动抓取
- **新闻数据**：每小时整点自动抓取
- **招聘信息**：每小时整点自动抓取
- **B站数据**：每6小时自动更新
- **播放量数据**：每天凌晨2点自动更新

### 手动更新
- **管理后台**：点击"更新B站数据"按钮
- **前端页面**：点击"刷新数据"按钮

---

## 📖 文档

### 核心文档
- [产品需求文档](./01-需求文档/PRD_产品需求文档_20251217_v1.0.md) (PRD)
- [技术规格文档](./03-技术文档/SPEC_技术规格文档_20251217_v1.0.md) (SPEC)
- [发版记录](./05-开发记录/发版记录_CHANGELOG.md) (CHANGELOG)
- [账号手册](./账号手册_20251219_v1.0.md) 🔒

### 使用文档
- [用户产品介绍](./02-产品文档/用户产品介绍_微信版_20251218_v1.0.md)
- [服务器操作完整指南](./06-安装部署/运维管理/服务器操作完整指南.md)
- [服务器脚本命令手册](./10-使用说明/服务器脚本命令手册_20251219_v1.0.md)
- [B站数据问题完整解决方案](./09-问题修复/B站数据问题完整解决方案.md)

---

## 🛠️ 技术栈

### 后端
- Python 3.9+
- Flask 3.0+
- SQLAlchemy 2.0+
- PostgreSQL 15+
- APScheduler 3.10+
- Gunicorn

### 前端
- HTML5 + CSS3 + JavaScript (原生)
- Chart.js (数据可视化)
- Font Awesome 6.4 (图标库)

### 部署
- Docker + Docker Compose
- Gunicorn (WSGI服务器)
- Nginx (反向代理)
- systemd (服务管理)

---

## 📝 开发规范

### 代码管理
- ✅ 所有代码修改必须先提交到GitHub
- ✅ 服务器代码必须从GitHub拉取（`git pull origin main`）
- ✅ 使用标准化的脚本和流程

### 文档管理
- ✅ 一个目的一个文档
- ✅ 删除冗余文档
- ✅ 归档历史文档
- ✅ 保持文档更新

---

## 🔗 相关链接

- **GitHub仓库**：https://github.com/aramisjiang-wq/EmbodiedPulse2026
- **具身算法工具箱**：https://gradmotion.com/
- **具身知识库**：https://paj5uamwttr.feishu.cn/wiki/GaozwfU3iiWA9Nk0LVUcUzKZnHc
- **产品反馈**：https://paj5uamwttr.feishu.cn/share/base/form/shrcnYlYb0NorOBVv2P8xRAArDe

---

## 📞 支持

如有问题或建议，请通过以下方式反馈：
- 产品反馈表单：https://paj5uamwttr.feishu.cn/share/base/form/shrcnYlYb0NorOBVv2P8xRAArDe
- GitHub Issues

---

**最后更新**: 2025-12-19

