# Embodied Pulse（具身脉搏）

**版本**: v1.0.0  
**发布日期**: 2025-12-17  
**状态**: ✅ 准备部署上线

---

## 📋 项目简介

Embodied Pulse 是一个专注于具身智能和机器人领域的ArXiv论文自动抓取、分类和展示平台，同时提供B站视频内容追踪和管理功能。

**核心价值**：
- ✅ 自动抓取和分类具身智能领域的最新论文
- ✅ 追踪B站UP主和视频内容，了解行业动态
- ✅ 提供完整的管理平台，方便数据维护
- ✅ 支持自动定时更新，无需人工干预

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- PostgreSQL 12+
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
- 实时进度显示
- 搜索和筛选功能
- 新论文红点提示

### 具身视频Hub页面
- B站UP主信息追踪
- 视频发布趋势可视化
- 月度播放量统计对比
- 自然周数据维度
- 响应式布局设计

### 管理平台
- 用户管理
- 论文管理
- 视频管理
- 日志监控
- 统计仪表盘

### 用户认证系统
- 飞书OAuth登录
- 管理员登录
- 个人中心
- JWT Token认证

---

## 📖 文档

- [产品需求文档](./docs/项目文档/01-需求文档/PRD_产品需求文档_20251217_v1.0.md)
- [技术规格文档](./docs/项目文档/03-技术文档/SPEC_技术规格文档_20251208.md)
- [发版记录](./docs/项目文档/05-开发记录/发版记录_CHANGELOG.md)
- [用户使用指南](./docs/项目文档/10-使用说明/)
- [测试记录](./docs/项目文档/08-测试文档/测试记录_20251217_v1.0.md)

---

## 🔧 技术栈

**后端**：
- Flask（Web框架）
- SQLAlchemy（ORM）
- PostgreSQL（数据库）
- APScheduler（定时任务）
- JWT（认证）

**前端**：
- HTML5 + CSS3 + JavaScript（原生）
- Chart.js（数据可视化）
- Font Awesome（图标库）

**部署**：
- Docker + Docker Compose
- Gunicorn（WSGI服务器）

---

## 📊 数据统计

- **论文数据**：14,000+ 篇论文
- **视频数据**：515个视频
- **UP主数据**：12个UP主
- **用户数据**：支持多用户管理

---

## 🛠️ 开发

### 项目结构

```
EmbodiedPulse2026/
├── app.py                 # Flask应用主入口
├── auth_routes.py         # 认证路由
├── models.py              # 数据库模型
├── templates/             # HTML模板
├── static/                # 静态文件
├── scripts/                # 脚本文件
├── docs/                  # 文档
└── requirements.txt       # Python依赖
```

### 开发规范

- [文档管理规范](./docs/项目文档/11-开发规范/文档管理规范和标准_20251217_v1.0.md)
- [AI开发原则](./docs/项目文档/11-开发规范/AI开发原则与规范_20251212.md)

---

## 📝 许可证

本项目采用 MIT 许可证。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📧 联系方式

如有问题，请通过以下方式联系：
- GitHub Issues: [提交Issue](https://github.com/aramisjiang-wq/EmbodiedPulse2026/issues)
- 产品反馈: [反馈表单](https://paj5uamwttr.feishu.cn/share/base/form/shrcnYlYb0NorOBVv2P8xRAArDe)

---

**最后更新**：2025-12-17  
**维护者**：产品团队

