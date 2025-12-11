# 批量更新Semantic Scholar数据

**文档创建时间**: 2025-12-09  
**最后更新时间**: 2025-12-09  
**操作状态**: 🔄 进行中

---

## 📋 操作概述

批量更新所有论文的Semantic Scholar补充数据，包括：
- 被引用数量 (`citation_count`)
- 高影响力引用数 (`influential_citation_count`)
- 作者机构信息 (`author_affiliations`)
- 发表场所 (`venue`)
- 发表年份 (`publication_year`)

---

## 📊 数据统计

**总论文数**: 5365篇

**更新前状态**：
- 已有Semantic Scholar数据：26篇
- 需要更新：5339篇

**预计时间**：
- 按150ms延迟计算：约13.3分钟
- 考虑速率限制和重试：约15-20分钟

---

## 🚀 执行方式

### 启动批量更新

```bash
# 后台运行，强制更新所有论文
nohup python3 update_semantic_scholar_data.py --no-skip > /tmp/semantic_scholar_update.log 2>&1 &
echo $! > /tmp/semantic_scholar_update.pid
```

### 监控进度

**方式1：查看当前进度**
```bash
python3 check_update_progress.py
```

**方式2：实时监控（每5秒刷新）**
```bash
./monitor_update.sh
```

**方式3：查看日志**
```bash
# 查看最新日志
tail -20 /tmp/semantic_scholar_update.log

# 实时跟踪日志
tail -f /tmp/semantic_scholar_update.log
```

### 停止更新

```bash
kill $(cat /tmp/semantic_scholar_update.pid)
```

---

## ⚙️ 技术细节

### 速率限制处理

- **API限制**：约100 requests/5min
- **延迟设置**：150ms（确保不超过限制）
- **重试机制**：遇到429错误时自动等待后重试（最多3次）

### 错误处理

- API调用失败不影响论文保存
- 论文在Semantic Scholar中不存在时，字段保存为0或空
- 所有错误都会记录到日志中

### 数据保存

- 即使引用数为0，也会保存字段（值为0）
- 即使论文在Semantic Scholar中不存在，也会保存字段（值为空）
- 确保所有论文都有完整的字段结构

---

## 📈 更新进度

**实时查看**：
```bash
python3 check_update_progress.py
```

**输出示例**：
```
总论文数: 5365
已有数据: 5365 (100.0%)
有引用数据: 32 (0.6%)
待更新: 0 (0.0%)
```

---

## ✅ 更新完成后的效果

1. **所有论文都有Semantic Scholar字段**
   - 即使值为0或空，字段也会存在

2. **前端显示**
   - 有引用数的论文会显示引用数量
   - 有发表场所的论文会显示发表信息
   - 有机构信息的论文会显示机构

3. **数据完整性**
   - 所有论文的数据结构统一
   - 便于后续查询和筛选

---

## 📝 注意事项

1. **更新过程不影响网站使用**
   - 更新在后台进行
   - 网站可以正常访问

2. **速率限制**
   - 严格遵守API速率限制
   - 自动处理429错误

3. **数据更新**
   - 被引用数量会随时间变化
   - 建议定期更新（如每月一次）

4. **查看结果**
   - 更新完成后，刷新网页即可看到新数据
   - 使用`check_update_progress.py`查看统计

---

## 🔄 后续维护

### 定期更新

建议每月运行一次批量更新，获取最新的引用数据：

```bash
# 只更新没有数据的论文（跳过已有数据）
python3 update_semantic_scholar_data.py

# 或强制更新所有论文
python3 update_semantic_scholar_data.py --no-skip
```

### 增量更新

对于新抓取的论文，可以在抓取时启用Semantic Scholar数据获取：

```python
# 在save_paper_to_db中设置
save_paper_to_db(paper_data, category, fetch_semantic_scholar=True)
```

**注意**：这会显著降低抓取速度，建议使用批量更新方式。

---

## 📚 相关文档

- [Semantic_Scholar_API集成_20251209.md](./Semantic_Scholar_API集成_20251209.md)
- [功能需求分析（自定义标签和论文数据）_20251208.md](./功能需求分析（自定义标签和论文数据）_20251208.md)

---

**操作时间**: 2025-12-09  
**操作人员**: AI Assistant  
**状态**: 🔄 进行中

