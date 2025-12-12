# Robotics ArXiv Daily

> 一个专注于具身智能和机器人领域的ArXiv论文自动抓取、分类和展示平台

**🎯 专为具身智能研究人员打造 | 📊 6,000+ 论文 | 🔄 每小时自动更新**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 产品简介

**Robotics ArXiv Daily** 是一个专为具身智能和机器人领域研究人员打造的论文聚合平台。每天自动从ArXiv抓取最新论文，按9个研究方向智能分类，帮助研究人员快速发现和跟踪领域最新进展。

### 🎯 核心价值

- ✅ **自动化抓取** - 每天自动从ArXiv抓取最新论文，无需手动搜索
- ✅ **智能分类** - 按9个研究方向自动分类，快速定位相关论文
- ✅ **实时更新** - 支持定时自动更新，确保数据最新
- ✅ **代码链接** - 自动提取GitHub等代码链接，方便复现研究
- ✅ **多维度信息** - 集成Semantic Scholar数据，提供引用数、机构等信息

---

## 🚀 核心功能

### 1. 论文浏览与搜索

- **9个研究方向分类**：Perception、VLM、Planning、RL/IL、Manipulation、Locomotion、Dexterous、VLA、Humanoid
- **智能搜索**：支持按标题、作者关键词搜索
- **筛选功能**：按类别、日期筛选论文
- **代码链接**：自动提取并展示GitHub代码链接

### 2. 数据统计与可视化

- **实时统计**：总论文数、各类别论文数量
- **研究方向活跃度**：7天/30天趋势分析，环比增长统计
- **数据仪表盘**：可视化展示数据概况

### 3. 具身智能资讯

- **24小时新闻**：自动抓取具身智能领域最新新闻
- **招聘信息**：展示相关岗位机会
- **数据集信息**：整理具身智能相关数据集

### 4. 特色功能

- **具身赛博🙏**：每日祝福语系统，为研究工作加油打气
- **B站信息**：展示逐际动力B站UP主最新视频
- **新论文提示**：红点提示今日新增论文

---

## 🛠️ 技术栈

### 前端
- **HTML5 + CSS3 + JavaScript** - 原生实现，无框架依赖
- **响应式设计** - 适配桌面和移动端
- **Chart.js** - 数据可视化

### 后端
- **Flask** - Python Web框架
- **PostgreSQL** - 关系型数据库（支持高并发）
- **SQLAlchemy** - ORM框架
- **APScheduler** - 定时任务调度

### 数据源
- **ArXiv API** - 论文数据抓取
- **Semantic Scholar API** - 论文元数据补充
- **RSS/NewsAPI** - 新闻数据抓取
- **GitHub API** - 招聘信息抓取

---

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/aramisjiang-wq/EmbodiedPulse2026.git
cd EmbodiedPulse2026

# 2. 启动服务（包含PostgreSQL）
docker-compose up -d

# 3. 初始化数据库
docker-compose exec web python3 init_database.py

# 4. 访问应用
# 打开浏览器: http://localhost:5001
```

### 方式二：本地部署

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置PostgreSQL数据库
# 创建数据库和用户（参考下方配置说明）

# 3. 配置环境变量
export DATABASE_URL=postgresql://user:password@localhost:5432/robotics_arxiv

# 4. 初始化数据库
python3 init_database.py

# 5. 启动应用
python3 app.py
# 或使用Gunicorn（生产环境）
gunicorn -c gunicorn_config.py app:app
```

### 数据库配置

```sql
-- 创建数据库
CREATE DATABASE robotics_arxiv;
CREATE USER robotics_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE robotics_arxiv TO robotics_user;
```

```bash
# 环境变量
export DATABASE_URL=postgresql://robotics_user:your_password@localhost:5432/robotics_arxiv
```

---

## 📊 功能展示

### 研究方向分类

平台覆盖具身智能领域的9个核心研究方向：

- **感知层**：Perception（感知理解）、VLM（视觉语言模型）
- **决策层**：Planning（规划决策）、RL/IL（强化学习/模仿学习）
- **执行层**：Manipulation（机器人操作）、Locomotion（运动控制）、Dexterous（灵巧操作）
- **集成层**：VLA（视觉语言动作）、Humanoid（人形机器人）

### 数据统计

- 当前论文总数：6,000+ 篇
- 每日新增：动态更新
- 代码链接覆盖率：持续提升
- 数据更新频率：每小时自动更新

---

## 🔧 配置说明

### 环境变量

```bash
# 数据库配置（必需）
DATABASE_URL=postgresql://user:password@localhost:5432/robotics_arxiv

# 自动抓取配置（可选）
AUTO_FETCH_ENABLED=true                    # 启用自动抓取
AUTO_FETCH_SCHEDULE="0 * * * *"           # Cron表达式（每小时整点）
AUTO_FETCH_MAX_RESULTS=100                # 每次抓取数量

# 服务器配置
PORT=5001                                  # 服务端口
FLASK_ENV=production                      # 环境模式
```

### 定时任务

支持配置多个定时任务：

- **论文抓取**：每小时整点执行（默认）
- **新闻抓取**：每小时整点执行（默认）
- **招聘信息抓取**：每小时整点执行（默认）
- **Semantic Scholar更新**：每天凌晨3点执行

---

## 📁 项目结构

```
robotics_arXiv_daily/
├── app.py                      # Flask应用主入口
├── models.py                   # 数据库模型（论文）
├── jobs_models.py              # 招聘信息模型
├── news_models.py              # 新闻模型
├── datasets_models.py          # 数据集模型
├── daily_arxiv.py              # 论文抓取核心逻辑
├── fetch_new_data.py           # 统一数据抓取函数
├── init_database.py            # 数据库初始化
├── migrate_sqlite_to_postgresql.py  # 数据迁移工具
├── requirements.txt            # Python依赖
├── docker-compose.yml          # Docker Compose配置
│
├── templates/                  # HTML模板
│   └── index.html
│
├── static/                     # 静态资源
│   ├── css/style.css
│   ├── js/app.js
│   └── js/blessing_messages.js
│
└── docs/                       # 数据文件
    └── cv-arxiv-daily.json     # JSON备份
```

---

## 🌟 主要特性

### 自动化
- ✅ 自动抓取ArXiv最新论文
- ✅ 自动分类到9个研究方向
- ✅ 自动提取代码链接
- ✅ 定时任务自动更新

### 智能化
- ✅ 智能关键词匹配分类
- ✅ 研究方向活跃度分析
- ✅ 新论文自动提示

### 数据完整性
- ✅ Semantic Scholar数据集成
- ✅ 引用数和机构信息
- ✅ 多源数据聚合

### 用户体验
- ✅ 现代化UI设计
- ✅ 响应式布局
- ✅ 实时搜索和筛选
- ✅ 数据可视化展示

---

## 📈 数据概览

### 研究方向分布

- **VLM**（视觉语言模型）：2,100+ 篇
- **Manipulation**（机器人操作）：1,000+ 篇
- **VLA**（视觉语言动作）：500+ 篇
- **RL/IL**（强化学习/模仿学习）：500+ 篇
- **Locomotion**（运动控制）：400+ 篇
- **Planning**（规划决策）：300+ 篇
- **Perception**（感知理解）：300+ 篇
- **Dexterous**（灵巧操作）：300+ 篇
- **Humanoid**（人形机器人）：300+ 篇

### 数据更新

- **更新频率**：每小时自动更新
- **数据源**：ArXiv API、Semantic Scholar、RSS、GitHub
- **数据量**：持续增长，当前6,000+篇论文
- **招聘信息**：500+ 条
- **新闻资讯**：24小时滚动更新
- **数据集**：持续整理中

---

## 🔗 API接口

### 主要接口

- `GET /api/papers` - 获取论文列表
- `GET /api/stats` - 获取统计信息
- `GET /api/trends` - 获取趋势数据
- `GET /api/news` - 获取新闻列表
- `GET /api/jobs` - 获取招聘信息
- `GET /api/datasets` - 获取数据集列表
- `GET /api/bilibili` - 获取B站信息
- `POST /api/fetch-papers` - 手动触发论文抓取
- `POST /api/refresh-all` - 刷新所有数据

API接口返回JSON格式数据，支持跨域访问。

---

## 🐳 Docker部署

### 使用Docker Compose

```bash
# 启动所有服务（PostgreSQL + Web应用）
docker-compose up -d

# 查看日志
docker-compose logs -f web

# 停止服务
docker-compose down

# 重启服务
docker-compose restart
```

### 数据持久化

PostgreSQL数据存储在Docker卷中，确保数据安全：

```bash
# 查看数据卷
docker volume ls

# 备份数据
docker-compose exec postgres pg_dump -U robotics_user robotics_arxiv > backup.sql
```

---

## 🔒 安全说明

- 所有数据库连接使用环境变量配置
- 支持PostgreSQL连接池和自动重连
- 生产环境建议配置HTTPS和防火墙
- 敏感信息不提交到代码仓库

---

## 📝 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发规范

- 遵循PEP 8代码规范
- 提交前运行测试确保功能正常
- 更新相关文档

---

## 📧 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件

---

## 🙏 致谢

- **ArXiv** - 提供论文数据源
- **Semantic Scholar** - 提供论文元数据
- **Flask** - Web框架
- **PostgreSQL** - 数据库

---

## 📅 更新日志

### v1.3.0 (2025-12-11)
- ✅ PostgreSQL数据库全面升级
- ✅ 具身赛博祝福语系统优化（100条/方向，不重复机制）
- ✅ Docker Compose集成PostgreSQL
- ✅ 数据迁移工具

### v1.2.4 (2025-12-11)
- ✅ Bilibili挂件功能
- ✅ 挂件收起/展开功能
- ✅ 更新红点提示功能

### v1.2.3 (2025-12-11)
- ✅ 定时任务自动更新机制优化
- ✅ 刷新功能优化

### v1.2 (2025-12-09)
- ✅ 具身24h新闻功能
- ✅ 招聘信息展示
- ✅ 数据集信息展示
- ✅ 具身赛博🙏功能
- ✅ Semantic Scholar数据集成

---

---

## 📚 更多信息

- **GitHub仓库**: [EmbodiedPulse2026](https://github.com/aramisjiang-wq/EmbodiedPulse2026)
- **问题反馈**: 提交 [Issue](https://github.com/aramisjiang-wq/EmbodiedPulse2026/issues)
- **功能建议**: 提交 [Feature Request](https://github.com/aramisjiang-wq/EmbodiedPulse2026/issues/new)

---

**最后更新**: 2025-12-11  
**版本**: v1.3.0  
**状态**: ✅ 生产环境运行中

---

> 💡 **提示**: 本项目专注于具身智能和机器人领域，为研究人员提供高效的论文发现和跟踪工具。
