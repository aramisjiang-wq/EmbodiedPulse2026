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
- ✅ **全局搜索** - 支持按标题、作者、摘要关键词搜索
- ✅ **数据可视化** - 研究方向活跃度、论文统计、作者排行榜等

---

## 🚀 核心功能

### 1. 具身论文清单 (`/`)

#### 论文浏览与搜索
- **研究方向分类**：感知层、决策层、运动层、操作层等
  - 感知层：2D感知、3D感知、目标检测、分割、VLM、点云、场景理解、生成等
  - 决策层：规划、图建模、强化学习、模仿学习等
  - 运动层：运动控制、导航、SLAM等
  - 操作层：操作、抓取、灵巧操作、操作与交互等
- **全局搜索**：支持按标题、作者、摘要关键词搜索（OR逻辑）
- **筛选排序**：按类别筛选、按日期/相关性排序
- **分页显示**：支持20/50/100条每页，便于浏览
- **摘要展示**：支持折叠/展开查看完整摘要

#### 数据统计与可视化
- **论文统计挂件**：显示总数、今日、本周、本月新增论文数
- **研究方向活跃度**：周度/月度趋势分析
  - 分类视图：按研究方向（感知层、决策层等）统计
  - 子标签视图：按具体子标签统计，支持分类筛选
  - 时间范围：支持4周/8周/12周/16周
- **活跃作者排行榜**：显示活跃作者及其论文数量趋势

### 2. 具身视频Hub (`/bilibili`)

#### 视频展示
- **7天内最新视频**：展示具身智能相关UP主最新发布的视频
- **视频发布趋势**：近30天各公司视频发布数量趋势
- **TOP 5公司**：近30天发布数量最多的5家公司

#### 播放量统计
- **月度播放量对比**：近1年各公司月度播放量热力图
- **年度总播放量**：当年各公司总播放量对比（横向柱状图）
- **公司列表**：展示所有公司及其视频信息

### 3. 其他功能

- **新闻资讯**：自动抓取具身智能领域最新新闻
- **招聘信息**：展示相关岗位机会
- **数据集信息**：整理具身智能相关数据集

---

## 🛠️ 技术栈

### 前端
- **HTML5 + CSS3 + JavaScript** - 原生实现，无框架依赖
- **响应式设计** - 适配桌面和移动端
- **Chart.js** - 数据可视化（折线图、柱状图、热力图）

### 后端
- **Flask** - Python Web框架
- **PostgreSQL/SQLite** - 关系型数据库
- **SQLAlchemy** - ORM框架
- **APScheduler** - 定时任务调度

### 数据源
- **ArXiv API** - 论文数据抓取
- **Bilibili API** - 视频数据抓取（使用bilibili-api-python）
- **RSS/NewsAPI** - 新闻数据抓取

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
├── app.py                      # Flask应用主文件
├── models.py                   # 论文数据库模型
├── bilibili_models.py          # B站数据模型
├── taxonomy.py                 # 论文分类体系（336个检索词）
├── daily_arxiv.py              # ArXiv论文抓取
├── fetch_new_data.py           # 数据抓取调度
├── save_paper_to_db.py         # 论文保存和分类逻辑
├── fetch_bilibili_data.py      # B站数据抓取脚本
├── bilibili_client.py          # B站API客户端
├── templates/                  # HTML模板
│   ├── index.html             # 论文清单页面
│   └── bilibili.html           # B站视频页面
├── static/                     # 静态资源
│   ├── css/                    # 样式文件
│   ├── js/                     # JavaScript文件
│   │   └── app.js              # 前端主要逻辑
│   └── images/                 # 图片资源
├── scripts/                    # 工具脚本
│   ├── reclassify_all_papers.py    # 论文重新分类
│   ├── fetch_benchmark_papers.py   # 基准论文抓取
│   └── ...                     # 其他脚本
└── docs/                       # 文档目录
    └── README.md               # 文档说明
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

### 论文分类体系

论文分类基于 `taxonomy.py` 中定义的检索词体系：
- **4个主分类**：感知层、决策层、运动层、操作层
- **33个子标签**：涵盖具身智能各个研究方向
- **336个检索词**：用于智能匹配和分类论文

---

## 📊 API接口

### 论文相关
- `GET /api/papers` - 获取论文列表
- `GET /api/search?q=关键词` - 搜索论文（标题、作者、摘要）
- `GET /api/paper-stats` - 获取论文统计信息
- `GET /api/research-activity` - 获取研究方向活跃度数据
- `GET /api/authors/ranking` - 获取活跃作者排行榜
- `POST /api/fetch` - 手动触发论文抓取

### B站相关
- `GET /api/bilibili/all` - 获取所有UP主和视频数据
- `GET /api/bilibili/monthly_stats` - 获取月度播放量统计
- `GET /api/bilibili/yearly_stats` - 获取年度播放量统计

### 其他
- `GET /api/news` - 获取新闻列表
- `GET /api/jobs` - 获取招聘信息
- `GET /api/datasets` - 获取数据集信息

---

## 🎨 功能特性

### 论文清单页面
- ✅ 全局搜索（标题、作者、摘要）
- ✅ 分类筛选和排序
- ✅ 分页显示（20/50/100条每页）
- ✅ 摘要折叠/展开
- ✅ 研究方向活跃度可视化
- ✅ 论文统计和作者排行榜

### B站视频页面
- ✅ 最新视频展示
- ✅ 视频发布趋势
- ✅ 播放量统计（月度热力图、年度对比）
- ✅ 公司列表和排序

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
- Bilibili - 视频数据源
- Chart.js - 数据可视化库

---

**最后更新**: 2025-12-16
