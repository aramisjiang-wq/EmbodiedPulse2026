# 清除B站缓存说明

## 问题

B站视频页面一直加载中，错误信息显示：
```
TypeError: result.data.map is not a function
```

**原因**: 缓存中存储的是旧数据格式（单个对象），而不是新格式（数组）

## 解决方案

### 方法1: 使用 force=1 参数（推荐）

在浏览器中访问：
```
http://localhost:5001/bilibili?force=1
```

或者在API调用时添加参数：
```javascript
fetch('/api/bilibili/all?force=1')
```

### 方法2: 重启Flask服务器

重启服务器会清除内存中的缓存：

```bash
# 如果使用 python3 app.py
# 按 Ctrl+C 停止，然后重新启动

# 如果使用 gunicorn
# 重启gunicorn进程
```

### 方法3: 等待缓存过期

缓存会在10分钟后自动过期，然后会自动获取新数据。

## 已修复的问题

1. ✅ 添加了数据格式验证
   - 如果缓存数据格式不正确（不是数组），会自动清除缓存并重新获取

2. ✅ 修复了缓存逻辑
   - 使用 `all_data` 缓存存储所有UP主数据
   - 不再使用 `data` 缓存（单个UP主数据）

## 验证修复

访问以下URL测试：
```
http://localhost:5001/api/bilibili/all?force=1
```

应该返回：
```json
{
  "success": true,
  "data": [...],  // 数组，包含12个UP主
  "total": 12
}
```

而不是：
```json
{
  "success": true,
  "data": {...}  // 单个对象（错误格式）
}
```

