# Semantic Scholar API 集成

**文档创建时间**: 2025-12-09  
**最后更新时间**: 2025-12-09  
**功能状态**: ✅ 已完成

---

## 📋 功能概述

集成 Semantic Scholar API，通过 ArXiv ID 查询获取论文的补充数据：
- **被引用数量** (`citation_count`)
- **高影响力引用数** (`influential_citation_count`)
- **作者机构信息** (`author_affiliations`)
- **发表场所** (`venue`)
- **发表年份** (`publication_year`)

---

## ✅ 实现内容

### 1. Semantic Scholar API 客户端

**文件**: `semantic_scholar_client.py`

**功能**：
- 通过 ArXiv ID 查询 Semantic Scholar API
- 解析返回数据，提取所需字段
- 处理速率限制和错误重试
- 提取作者机构信息

**主要函数**：
- `get_paper_metadata(arxiv_id)`: 获取论文元数据
- `get_paper_supplement_data(arxiv_id)`: 获取补充数据（封装函数）
- `extract_author_affiliations(authors)`: 提取机构信息
- `parse_semantic_scholar_data(data, arxiv_id)`: 解析数据

**速率限制处理**：
- 默认延迟：100ms（避免超过 100 requests/5min 限制）
- 重试机制：最多3次
- 429错误处理：自动等待后重试

### 2. 数据库模型扩展

**文件**: `models.py`

**新增字段**：
```python
citation_count = Column(Integer, default=0, nullable=True)  # 被引用数量
influential_citation_count = Column(Integer, default=0, nullable=True)  # 高影响力引用数
author_affiliations = Column(Text, nullable=True)  # 作者机构信息（JSON字符串）
venue = Column(String, nullable=True)  # 发表期刊/会议
publication_year = Column(Integer, nullable=True)  # 发表年份
semantic_scholar_updated_at = Column(DateTime, nullable=True)  # 数据更新时间
```

**更新 `to_dict()` 方法**：
- 自动解析机构信息（JSON字符串转数组）
- 包含所有新增字段

### 3. 数据库迁移脚本

**文件**: `migrate_add_semantic_scholar_fields.py`

**功能**：
- 检查字段是否已存在
- 添加不存在的字段
- 支持多次运行（幂等操作）

**使用方法**：
```bash
python3 migrate_add_semantic_scholar_fields.py
```

### 4. 保存逻辑集成

**文件**: `save_paper_to_db.py`

**新增功能**：
- `fetch_semantic_scholar` 参数：控制是否获取 Semantic Scholar 数据
- `update_semantic_scholar_data()` 函数：更新论文的 Semantic Scholar 数据

**注意**：
- 默认不启用（`fetch_semantic_scholar=False`），避免抓取时速度过慢
- 可以通过批量更新脚本单独更新已有论文的数据

### 5. 批量更新脚本

**文件**: `update_semantic_scholar_data.py`

**功能**：
- 批量更新所有论文的 Semantic Scholar 数据
- 支持按类别更新
- 支持限制更新数量
- 自动跳过已有数据的论文（可选）

**使用方法**：
```bash
# 更新所有论文（跳过已有数据）
python3 update_semantic_scholar_data.py

# 更新前100篇论文
python3 update_semantic_scholar_data.py --limit 100

# 更新指定类别
python3 update_semantic_scholar_data.py --category "RL/IL"

# 强制更新所有论文（不跳过已有数据）
python3 update_semantic_scholar_data.py --no-skip
```

### 6. 前端显示优化

**文件**: `static/js/app.js`, `static/css/style.css`

**新增显示内容**：
- **被引用数量**：显示引用数和高影响力引用数（带⭐标记）
- **机构信息**：显示作者所属机构（最多显示3个）
- **发表信息**：显示发表场所和年份

**样式特点**：
- 引用数：蓝色图标 + 数字
- 高影响力引用：金色徽章（⭐标记）
- 机构信息：紫色图标 + 文本（支持省略）
- 发表信息：绿色图标 + 文本

---

## 🔧 使用指南

### 方式1：抓取新论文时自动获取（不推荐）

修改 `daily_arxiv.py` 中的调用：
```python
success, action = save_paper_to_db(parsed, keyword, 
                                  enable_title_dedup=enable_dedup, 
                                  fetch_semantic_scholar=True)  # 启用
```

**注意**：这会显著降低抓取速度，因为每篇论文需要额外调用一次 API。

### 方式2：批量更新已有论文（推荐）

```bash
# 更新所有论文
python3 update_semantic_scholar_data.py

# 更新指定类别
python3 update_semantic_scholar_data.py --category "VLM" --limit 50
```

**优点**：
- 不影响抓取速度
- 可以分批更新
- 可以重试失败的论文

### 方式3：手动更新单篇论文

```python
from models import get_session, Paper
from save_paper_to_db import update_semantic_scholar_data

session = get_session()
paper = session.query(Paper).filter_by(id='2504.13120').first()
if paper:
    update_semantic_scholar_data(paper, paper.id, session)
    session.commit()
session.close()
```

---

## 📊 API 速率限制

**Semantic Scholar API 限制**：
- 免费版：约 100 requests/5min
- 每秒约 1000 次请求（理论值）

**实际使用建议**：
- 延迟设置：150ms（确保不超过限制）
- 批量更新：建议每次更新 50-100 篇论文后暂停
- 错误处理：自动重试 3 次

---

## 🎯 数据示例

### API 返回数据
```json
{
  "citationCount": 42,
  "influentialCitationCount": 5,
  "venue": "arXiv.org",
  "year": 2025,
  "authors": [
    {
      "name": "John Doe",
      "affiliations": ["MIT", "Stanford"]
    }
  ]
}
```

### 数据库存储
```python
paper.citation_count = 42
paper.influential_citation_count = 5
paper.venue = "arXiv.org"
paper.publication_year = 2025
paper.author_affiliations = '["MIT", "Stanford"]'  # JSON字符串
```

### 前端显示
- 引用数：📄 42 ⭐ 5
- 机构：🏢 MIT, Stanford
- 发表：📚 arXiv.org (2025)

---

## ⚠️ 注意事项

1. **数据可用性**：
   - 不是所有 ArXiv 论文都在 Semantic Scholar 中
   - 新论文可能需要一段时间才会出现在 Semantic Scholar

2. **速率限制**：
   - 严格遵守 API 速率限制
   - 批量更新时建议分批处理

3. **错误处理**：
   - API 调用失败不影响论文保存
   - 可以后续重试更新

4. **数据更新**：
   - 被引用数量会随时间变化
   - 建议定期更新（如每月一次）

---

## 📚 相关文档

- [功能需求分析（自定义标签和论文数据）_20251208.md](./功能需求分析（自定义标签和论文数据）_20251208.md)
- [Semantic Scholar API 文档](https://api.semanticscholar.org/api-docs/graph)

---

**完成时间**: 2025-12-09  
**开发人员**: AI Assistant  
**验证状态**: ✅ 已验证

