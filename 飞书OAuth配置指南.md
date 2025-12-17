# 飞书OAuth配置完整指南

## ⚠️ 问题说明

**错误码**: 20029  
**错误信息**: redirect_uri 请求不合法  
**原因**: 飞书开放平台未配置或配置错误的回调URL

---

## ✅ 完整配置步骤

### 步骤1: 登录飞书开放平台

1. 访问飞书开放平台
   ```
   https://open.feishu.cn
   ```

2. 使用**管理员账号**登录（必须是应用创建者或管理员）

---

### 步骤2: 找到应用

1. 登录后进入"**开发者后台**"

2. 在左侧菜单找到"**应用管理**" 或 "**凭证与基础信息**"

3. 找到你的应用:
   - **App ID**: `cli_a6727c4ffc71d00b`
   - **应用名称**: 你创建时设置的名称

4. 点击进入**应用详情**

---

### 步骤3: 配置重定向URL

1. 在应用详情页面，找到以下任一配置项:
   - "**安全设置**"
   - "**网页**" Tab
   - "**重定向URL**"
   - "**Redirect URI**"

2. **添加以下URL**（两个都添加，防止遗漏）:

   ```
   http://localhost:5001/api/auth/feishu/callback
   http://127.0.0.1:5001/api/auth/feishu/callback
   ```

3. **重要提示**:
   - URL必须**完全一致**（包括协议、域名、端口、路径）
   - 不要有多余的空格或换行
   - 协议是 `http://`（本地开发）
   - 路径是 `/api/auth/feishu/callback`

4. 点击"**保存**"或"**添加**"按钮

---

### 步骤4: 等待生效

- 配置保存后，通常需要等待 **1-5分钟** 生效
- 可以在配置页面确认是否已添加成功

---

### 步骤5: 重新测试

1. 访问登录页面:
   ```
   http://localhost:5001/login
   ```
   或
   ```
   http://127.0.0.1:5001/login
   ```

2. 点击"**飞书登录**"按钮

3. 如果配置正确，应该:
   - 跳转到飞书授权页面（不再显示错误20029）
   - 显示扫码界面
   - 扫码后回调成功

---

## 🔍 配置验证清单

### ✅ 必须完成的配置

- [ ] 已登录飞书开放平台
- [ ] 找到了App ID为 `cli_a6727c4ffc71d00b` 的应用
- [ ] 进入了应用的"安全设置"或"重定向URL"配置
- [ ] 添加了 `http://localhost:5001/api/auth/feishu/callback`
- [ ] 添加了 `http://127.0.0.1:5001/api/auth/feishu/callback`
- [ ] 保存了配置
- [ ] 等待了1-5分钟让配置生效

---

## 🛠️ 常见问题

### Q1: 找不到"重定向URL"配置在哪里？

**可能的位置**:
1. 应用详情 → **网页** Tab → 重定向URL
2. 应用详情 → **安全设置** → 回调地址
3. 应用详情 → **权限管理** → 网页授权
4. 应用详情 → **凭证与基础信息** → 回调地址

**如果还是找不到**:
- 确认你是应用的管理员
- 确认应用类型是"网页应用"或"自建应用"
- 联系飞书技术支持

---

### Q2: 配置了但还是显示20029错误？

**检查项**:
1. **URL是否完全一致**
   - 检查是否有多余的空格
   - 检查协议是否是 `http://`（不是https）
   - 检查端口号是否是 `5001`
   - 检查路径是否是 `/api/auth/feishu/callback`

2. **是否保存了配置**
   - 确认点击了"保存"按钮
   - 刷新页面查看是否显示在列表中

3. **是否等待生效**
   - 等待5分钟
   - 清除浏览器缓存
   - 使用无痕模式重试

4. **App ID和Secret是否正确**
   - 检查.env文件中的配置
   - 确认与飞书开放平台一致

---

### Q3: 本地测试必须用localhost或127.0.0.1吗？

**是的**，飞书OAuth对本地开发有特殊支持:
- ✅ `http://localhost:端口/路径`
- ✅ `http://127.0.0.1:端口/路径`
- ❌ `http://192.168.x.x:端口/路径` (内网IP不支持)
- ❌ `http://自定义域名` (必须是公网域名或localhost)

---

### Q4: 生产环境如何配置？

**生产环境要求**:
1. 必须使用 **HTTPS** 协议
2. 必须是**公网可访问**的域名
3. 必须在飞书开放平台添加生产环境的回调URL

**示例**:
```
https://your-domain.com/api/auth/feishu/callback
```

**配置步骤**:
1. 在飞书开放平台添加生产环境回调URL
2. 修改.env文件:
   ```bash
   FEISHU_REDIRECT_URI=https://your-domain.com/api/auth/feishu/callback
   ```
3. 重启应用

---

### Q5: 可以用内网穿透工具吗？

**可以**，如果你想在本地测试但使用公网地址:

**推荐工具**:
1. **ngrok** (https://ngrok.com)
2. **frp** (https://github.com/fatedier/frp)
3. **花生壳** (https://hsk.oray.com)

**使用示例（ngrok）**:
```bash
# 1. 安装ngrok
brew install ngrok

# 2. 启动内网穿透
ngrok http 5001

# 3. 获取公网地址（如 https://xxx.ngrok.io）

# 4. 修改.env文件
FEISHU_REDIRECT_URI=https://xxx.ngrok.io/api/auth/feishu/callback

# 5. 在飞书开放平台添加这个URL
```

---

## 📋 配置模板

### 本地开发配置（.env）

```bash
# 使用localhost（推荐）
FEISHU_REDIRECT_URI=http://localhost:5001/api/auth/feishu/callback

# 或使用127.0.0.1
FEISHU_REDIRECT_URI=http://127.0.0.1:5001/api/auth/feishu/callback
```

### 生产环境配置（.env）

```bash
FEISHU_REDIRECT_URI=https://your-domain.com/api/auth/feishu/callback
```

---

## 🎯 测试地址

### 登录页面
```
http://localhost:5001/login
http://127.0.0.1:5001/login
```

### 回调地址（自动处理，无需手动访问）
```
http://localhost:5001/api/auth/feishu/callback
http://127.0.0.1:5001/api/auth/feishu/callback
```

### 成功页面
```
http://localhost:5001/auth/callback
```

---

## 📞 需要帮助？

### 提供以下信息以便诊断:

1. **飞书开放平台截图**:
   - 应用详情页面
   - 重定向URL配置页面
   - 已添加的URL列表

2. **错误信息**:
   - 错误码
   - log ID
   - 完整的错误提示

3. **配置信息**:
   - .env文件内容（隐藏Secret）
   - 使用的访问地址（localhost还是127.0.0.1）

4. **日志**:
   ```bash
   tail -50 app.log | grep -i feishu
   ```

---

## ✅ 配置成功标志

配置成功后，登录流程应该是:

1. 点击"飞书登录"
   ✅ 跳转到飞书授权页面（不再显示20029错误）

2. 显示扫码界面
   ✅ 显示二维码

3. 扫码确认
   ✅ 手机飞书收到授权请求

4. 授权成功
   ✅ 自动跳转回网站

5. 登录成功页面
   ✅ 显示"登录成功"和欢迎信息

6. 自动跳转
   ✅ 3秒后跳转到个人中心

---

**祝配置成功！** 🎉

如果按照上述步骤仍无法解决，请提供飞书开放平台的配置截图。

