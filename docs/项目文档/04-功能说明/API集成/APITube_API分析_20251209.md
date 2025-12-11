# APITube API 功能分析

**文档创建时间**: 2025-12-09  
**最后更新时间**: 2025-12-09  
**API文档**: https://docs.apitube.io

---

## 📋 API概述

**APITube** 是一个强大的新闻API服务，提供来自**50万+验证新闻源**的数据访问。

### 主要特点

- ✅ **数据源丰富**: 50万+验证新闻源
- ✅ **免费开发版**: 开发阶段免费使用
- ✅ **RESTful API**: 易于集成
- ✅ **多语言支持**: 支持多种语言
- ✅ **灵活过滤**: 支持多种过滤参数

---

## 🔑 API配置

### API Key
```
api_live_ZHYtQHN5TrwshXBtkya8hTxhBf1UKeoRh1pv6Z4W0Hpb0FF5J9wY
```

### 认证方式
使用HTTP Header进行认证：
```http
X-API-Key: api_live_ZHYtQHN5TrwshXBtkya8hTxhBf1UKeoRh1pv6Z4W0Hpb0FF5J9wY
```

### 基础URL
```
https://api.apitube.io/v1
```

---

## 🎯 主要功能

### 1. 获取新闻（Everything端点）

**端点**: `/news/everything`

**功能**：
- 获取所有新闻源的最新文章
- 支持多种过滤参数
- 支持分页

**示例请求**：
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "https://api.apitube.io/v1/news/everything?per_page=10"
```

### 2. 支持的过滤参数

根据文档，APITube支持以下过滤方式：

- **按标题**: `title=关键词`
- **按语言**: `language.code=en`
- **按类别**: `category=technology`
- **按主题**: `topic=artificial-intelligence`
- **按实体**: `entity=公司名/人名`
- **按情感**: `sentiment=positive/negative`
- **按来源**: `source=来源名称`
- **按日期**: `published_at.from=2025-12-09&published_at.to=2025-12-09`
- **按作者**: `author=作者名`
- **按位置**: `location=国家/城市`
- **按媒体类型**: `media=video/article`
- **按行业**: `industry=technology`

### 3. 排序选项

- `published_at`: 按发布时间排序
- `relevance`: 按相关性排序
- `popularity`: 按受欢迎程度排序

### 4. 分页

- `per_page`: 每页结果数
- `page`: 页码

---

## 🤖 机器人具身智能相关新闻获取

### 关键词策略

**英文关键词**：
```
robot OR robotics OR "embodied AI" OR "embodied intelligence" 
OR "robot manipulation" OR "robot locomotion" OR "humanoid robot"
OR "reinforcement learning robot" OR "robot learning"
```

**中文关键词**：
```
机器人 OR 具身智能 OR 机器人学习 OR 机器人操作 
OR 机器人运动 OR 人形机器人
```

### 查询示例

```python
# 获取今天的机器人相关新闻
params = {
    "title": "robot OR robotics OR embodied AI",
    "language.code": "en",
    "published_at.from": "2025-12-09",
    "published_at.to": "2025-12-09",
    "per_page": 100,
    "sort": "published_at"
}
```

---

## 📊 API响应结构

根据文档，API返回JSON格式数据：

```json
{
  "data": [
    {
      "title": "新闻标题",
      "description": "新闻描述",
      "url": "新闻URL",
      "source": {
        "name": "来源名称"
      },
      "published_at": "2025-12-09T10:30:00Z",
      "author": "作者",
      "content": "新闻内容",
      "image_url": "图片URL",
      "language": {
        "code": "en"
      }
    }
  ],
  "meta": {
    "total": 1000,
    "per_page": 10,
    "page": 1
  }
}
```

---

## ⚙️ 使用场景

### 1. 每日新闻抓取
- 每天定时获取最新新闻
- 过滤机器人具身智能相关内容
- 保存到数据库

### 2. 实时监控
- 监控特定关键词的新闻
- 设置告警通知

### 3. 数据分析
- 分析新闻趋势
- 情感分析
- 来源分析

---

## 🔧 实现建议

### 1. 创建APITube客户端

```python
import requests

class APITubeClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.apitube.io/v1"
        self.headers = {"X-API-Key": api_key}
    
    def get_news(self, **params):
        url = f"{self.base_url}/news/everything"
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
```

### 2. 定时抓取

- 每天执行1-2次
- 获取最近24小时的新闻
- 自动去重和保存

### 3. 数据存储

- 存储标题、描述、URL、来源、发布时间等
- 基于URL去重
- 支持按日期、来源查询

---

## ⚠️ 注意事项

1. **速率限制**
   - 免费版有请求限制
   - 需要合理控制请求频率

2. **数据去重**
   - 基于URL去重
   - 避免重复保存

3. **错误处理**
   - API密钥失效
   - 网络超时
   - 速率限制

4. **数据质量**
   - 过滤无关新闻
   - 验证URL有效性

---

## 📚 参考资源

- [APITube官方文档](https://docs.apitube.io)
- [认证指南](https://docs.apitube.io/guides/news-api/authentication)
- [端点文档](https://docs.apitube.io/guides/news-api/endpoints)
- [参数文档](https://docs.apitube.io/guides/news-api/parameters)

---

**操作时间**: 2025-12-09  
**操作人员**: AI Assistant

