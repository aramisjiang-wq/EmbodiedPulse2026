# 新闻API使用说明

## 🚀 快速开始

### 方案1: 使用 NewsAPI.org（推荐）

1. **注册获取API Key**
   - 访问：https://newsapi.org/
   - 注册账号（免费）
   - 获取API Key（免费版：500次请求/天）

2. **设置环境变量**
   ```bash
   export NEWSAPI_API_KEY="your_api_key_here"
   export NEWS_API_TYPE="newsapi"
   ```

3. **运行抓取脚本**
   ```bash
   python3 fetch_robotics_news.py --days 3 --yes --api newsapi
   ```

### 方案2: 使用 APITube（当前）

1. **等待限制解除**（可能需要1-24小时）

2. **运行抓取脚本**
   ```bash
   python3 fetch_robotics_news.py --days 3 --yes --api apitube
   ```

---

## 📋 API对比

| 特性 | NewsAPI.org | APITube |
|------|------------|---------|
| 免费额度 | 500次/天 | 未知 |
| 注册难度 | ⭐ 简单 | ⭐⭐ 中等 |
| 数据质量 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 中文支持 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 推荐度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 🔧 配置说明

### 环境变量

```bash
# 选择API类型
export NEWS_API_TYPE="newsapi"  # 或 "apitube"

# NewsAPI.org API Key（如果使用NewsAPI）
export NEWSAPI_API_KEY="your_api_key"

# APITube API Key（如果使用APITube，已在代码中配置）
# api_live_ZHYtQHN5TrwshXBtkya8hTxhBf1UKeoRh1pv6Z4W0Hpb0FF5J9wY
```

### 命令行参数

```bash
# 使用NewsAPI
python3 fetch_robotics_news.py --days 3 --yes --api newsapi

# 使用APITube
python3 fetch_robotics_news.py --days 3 --yes --api apitube

# 自动选择（从环境变量读取）
python3 fetch_robotics_news.py --days 3 --yes
```

---

## ⚠️ 注意事项

1. **API限制**
   - NewsAPI.org：500次/天，需要合理控制请求频率
   - APITube：限制未知，建议等待后重试

2. **API Key安全**
   - 不要将API Key提交到Git仓库
   - 使用环境变量或配置文件管理

3. **数据去重**
   - 系统会自动基于URL去重
   - 避免重复保存相同新闻

---

## 📚 相关文档

- `docs/项目文档/功能说明/新闻API替代方案_20251209.md` - 详细API对比和方案
- `newsapi_client.py` - NewsAPI.org客户端实现
- `apitube_client.py` - APITube客户端实现

