# 修复docker-compose Segmentation Fault

## 🚨 问题描述

执行 `docker-compose` 命令时出现 `Segmentation fault` 错误。

## 🔍 原因分析

Segmentation fault通常由以下原因引起：
1. docker-compose二进制文件损坏
2. 系统库不兼容
3. 内存不足
4. Docker版本不兼容

## 🔧 修复方案

### 方法一：重新安装docker-compose（推荐）

```bash
# 1. 删除旧版本
rm -f /usr/local/bin/docker-compose
rm -f /usr/bin/docker-compose

# 2. 安装最新版本
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 3. 设置权限
chmod +x /usr/local/bin/docker-compose

# 4. 验证安装
docker-compose --version
```

### 方法二：使用Docker Compose Plugin（替代方案）

```bash
# 1. 卸载旧版本
rm -f /usr/local/bin/docker-compose

# 2. 安装Docker Compose Plugin
apt update
apt install -y docker-compose-plugin

# 3. 使用新命令（注意是docker compose，不是docker-compose）
docker compose version
```

### 方法三：使用pip安装

```bash
# 1. 安装pip（如果没有）
apt update
apt install -y python3-pip

# 2. 使用pip安装docker-compose
pip3 install docker-compose

# 3. 验证
docker-compose --version
```

## 🛠️ 完整修复流程

### 步骤1：修复docker-compose

```bash
# 删除旧版本
rm -f /usr/local/bin/docker-compose /usr/bin/docker-compose

# 安装新版本
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 验证
docker-compose --version
```

### 步骤2：检查Docker服务

```bash
# 检查Docker状态
systemctl status docker

# 如果未运行，启动Docker
systemctl start docker
systemctl enable docker

# 测试Docker
docker ps
```

### 步骤3：清理Docker资源

```bash
# 停止所有容器（如果docker-compose还不行，直接用docker命令）
docker ps -a | awk '{print $1}' | xargs docker stop 2>/dev/null || true
docker ps -a | awk '{print $1}' | xargs docker rm 2>/dev/null || true

# 清理未使用的资源
docker system prune -f
```

### 步骤4：重新部署

```bash
cd /opt/EmbodiedPulse

# 如果使用新的docker compose命令
docker compose down -v
docker compose build --no-cache
docker compose up -d

# 或者如果docker-compose修复成功
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## 🔄 如果docker-compose还是不行

使用Docker原生命令替代：

```bash
cd /opt/EmbodiedPulse

# 1. 停止容器
docker stop embodied-pulse-web embodied-pulse-postgres 2>/dev/null || true
docker rm embodied-pulse-web embodied-pulse-postgres 2>/dev/null || true

# 2. 删除卷
docker volume rm embodiedpulse_postgres_data 2>/dev/null || true

# 3. 构建镜像
docker build -t embodied-pulse-web .

# 4. 启动PostgreSQL
docker run -d \
  --name embodied-pulse-postgres \
  -e POSTGRES_USER=robotics_user \
  -e POSTGRES_PASSWORD=robotics_password \
  -e POSTGRES_DB=robotics_arxiv \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  --restart always \
  postgres:15-alpine

# 5. 等待数据库启动
sleep 10

# 6. 启动Web服务
docker run -d \
  --name embodied-pulse-web \
  --link embodied-pulse-postgres:postgres \
  -e DATABASE_URL=postgresql://robotics_user:robotics_password@postgres:5432/robotics_arxiv \
  -v $(pwd)/docs:/app/docs \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -p 5001:5001 \
  --restart always \
  embodied-pulse-web

# 7. 检查状态
docker ps
docker logs embodied-pulse-web
```

## 📊 验证修复

```bash
# 1. 测试docker-compose
docker-compose --version
# 应该显示版本号，而不是Segmentation fault

# 2. 测试Docker
docker ps
# 应该正常显示容器列表

# 3. 检查服务
docker ps | grep embodied
# 应该看到两个容器在运行
```

## 🆘 如果还是不行

1. **检查系统资源**：
   ```bash
   free -h
   df -h
   ```

2. **检查系统日志**：
   ```bash
   dmesg | tail -20
   journalctl -xe | tail -50
   ```

3. **尝试重启服务器**：
   ```bash
   reboot
   ```

4. **使用Docker Compose Plugin替代**：
   ```bash
   apt install -y docker-compose-plugin
   docker compose version
   docker compose up -d
   ```

