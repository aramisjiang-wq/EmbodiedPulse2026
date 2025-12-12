# 部署前验收测试

**目的**：每次部署前进行全局稳定性和可用性测试，确保系统正常运行

**使用方法**：
```bash
# 运行所有测试
python3 tests/run_all_tests.py

# 运行特定测试
python3 tests/test_api_endpoints.py
python3 tests/test_database_connections.py
python3 tests/test_functionality.py
```

---

## 📋 测试清单

### 1. API端点测试 (`test_api_endpoints.py`)
- 测试所有API端点的可用性
- 验证API响应格式
- 检查错误处理

### 2. 数据库连接测试 (`test_database_connections.py`)
- 测试所有数据库连接
- 验证数据完整性
- 检查数据库操作

### 3. 功能测试 (`test_functionality.py`)
- 测试核心功能
- 验证业务逻辑
- 检查数据流

### 4. 集成测试 (`test_integration.py`)
- 测试系统集成
- 验证端到端流程
- 检查外部API集成

### 5. 性能测试 (`test_performance.py`)
- 测试API响应时间
- 验证数据库查询性能
- 检查缓存机制

---

## 🚀 快速开始

1. **确保服务器运行**
   ```bash
   python3 app.py
   # 或
   gunicorn -c gunicorn_config.py app:app
   ```

2. **运行测试**
   ```bash
   python3 tests/run_all_tests.py
   ```

3. **查看测试报告**
   - 测试结果会输出到控制台
   - 详细报告保存在 `tests/reports/` 目录

---

## 📝 测试报告

测试报告保存在 `tests/reports/` 目录，包含：
- 测试时间戳
- 测试结果摘要
- 详细测试日志
- 失败测试详情

---

## ⚠️ 注意事项

- 运行测试前确保服务器已启动
- 测试会使用实际数据库，请确保数据库可访问
- 某些测试可能需要外部API访问，确保网络连接正常




