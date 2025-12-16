# Embodied Pulse

> 一个专注于具身智能和机器人领域的ArXiv论文自动抓取、分类和展示平台

**🎯 专为具身智能研究人员打造 | 📊 6,000+ 论文 | 🔄 每小时自动更新**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 产品简介

**Embodied Pulse** 是一个专为具身智能和机器人领域研究人员打造的论文聚合平台。每天自动从ArXiv抓取最新论文，按研究方向智能分类，帮助研究人员快速发现和跟踪领域最新进展。

### 🎯 核心价值

- ✅ **自动化抓取** - 每天自动从ArXiv抓取最新论文，无需手动搜索
- ✅ **智能分类** - 按研究方向自动分类，快速定位相关论文
- ✅ **实时更新** - 支持定时自动更新，确保数据最新
- ✅ **代码链接** - 自动提取GitHub等代码链接，方便复现研究
- ✅ **多维度信息** - 集成Semantic Scholar数据，提供引用数、机构等信息

---

## 🚀 核心功能

### 1. 论文浏览与搜索

- **研究方向分类**：感知层、决策层、运动层、操作层等
- **智能搜索**：支持按标题、作者、摘要关键词搜索
- **筛选功能**：按类别、日期筛选论文
- **代码链接**：自动提取并展示GitHub代码链接

### 2. 数据统计与可视化

- **实时统计**：总论文数、各类别论文数量
- **研究方向活跃度**：周度/月度趋势分析，环比增长统计
- **数据仪表盘**：可视化展示数据概况

### 3. 具身智能资讯

- **24小时新闻**：自动抓取具身智能领域最新新闻
- **招聘信息**：展示相关岗位机会
- **数据集信息**：整理具身智能相关数据集

### 4. B站视频聚合

- **视频展示**：展示具身智能相关UP主最新视频
- **播放量统计**：月度/年度播放量对比分析
- **趋势分析**：视频发布趋势和播放量趋势

---

## 🛠️ 技术栈

### 前端
- **HTML5 + CSS3 + JavaScript** - 原生实现，无框架依赖
- **响应式设计** - 适配桌面和移动端
- **Chart.js** - 数据可视化

### 后端
- **Flask** - Python Web框架
- **PostgreSQL/SQLite** - 关系型数据库
- **SQLAlchemy** - ORM框架
- **APScheduler** - 定时任务调度

### 数据源
- **ArXiv API** - 论文数据抓取
- **Semantic Scholar API** - 论文元数据补充
- **RSS/NewsAPI** - 新闻数据抓取
- **Bilibili API** - 视频数据抓取

---

## 🚀 快速开始

### 方式一：本地部署

```bash
# 1. 克隆项目
git clone https://github.com/aramisjiang-wq/EmbodiedPulse2026.git
cd EmbodiedPulse2026

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库
python3 init_database.py

# 4. 启动应用
python3 app.py

# 5. 访问应用
# 打开浏览器: http://localhost:5001
```

### 方式二：Docker Compose（推荐）

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

---

## 📁 项目结构

```
EmbodiedPulse2026/
├── app.py                 # Flask应用主文件
├── models.py              # 数据库模型
├── taxonomy.py            # 论文分类体系
├── daily_arxiv.py         # ArXiv论文抓取
├── fetch_new_data.py      # 数据抓取调度
├── save_paper_to_db.py    # 论文保存逻辑
├── templates/             # HTML模板
│   ├── index.html         # 论文清单页面
│   └── bilibili.html      # B站视频页面
├── static/                # 静态资源
│   ├── css/               # 样式文件
│   ├── js/                # JavaScript文件
│   └── images/            # 图片资源
├── scripts/               # 工具脚本
│   ├── reclassify_all_papers.py  # 论文重新分类
│   └── ...                # 其他脚本
└── docs/                  # 文档目录
    └── README.md          # 文档说明
```

---

## 🔧 配置说明

### 环境变量

```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost/dbname

# 自动抓取开关
AUTO_FETCH_ENABLED=true

# 其他配置...
```

### 定时任务

系统支持自动定时抓取论文，默认每小时执行一次。可通过 `APScheduler` 配置调整抓取频率。

---

## 📚 文档

详细文档请查看 [docs/README.md](./docs/README.md)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

## 👤 作者

**aramisjiang-wq**

- GitHub: [@aramisjiang-wq](https://github.com/aramisjiang-wq)
- Email: aramisjiang.wq@gmail.com

---

## 🙏 致谢

- ArXiv - 论文数据源
- Semantic Scholar - 论文元数据
- Bilibili - 视频数据源

---

**最后更新**: 2025-12-16
