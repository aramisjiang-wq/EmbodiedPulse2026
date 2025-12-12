# Docker 部署指南

## 服务器信息
- IP: 115.190.77.57
- 用户: root
- 密码: ash@2025

## 部署方式

### 方式一：在服务器上直接部署（推荐）

1. SSH连接到服务器：
```bash
ssh root@115.190.77.57
# 密码: ash@2025
```

2. 在服务器上运行部署脚本：
```bash
# 下载部署脚本
curl -o deploy_server.sh https://raw.githubusercontent.com/aramisjiang-wq/EmbodiedPulse2026/main/deploy_server.sh
# 或者直接创建并运行
bash <(curl -s https://raw.githubusercontent.com/aramisjiang-wq/EmbodiedPulse2026/main/deploy_server.sh)
```

或者手动执行：
```bash
# 1. 安装Docker和Docker Compose（如果未安装）
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl start docker
systemctl enable docker

# 安装Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 2. 克隆项目
mkdir -p /opt/EmbodiedPulse
cd /opt/EmbodiedPulse
git clone https://github.com/aramisjiang-wq/EmbodiedPulse2026.git .

# 3. 启动服务
docker-compose up -d --build

# 4. 初始化数据库
docker-compose exec web python3 init_database.py

# 5. 查看服务状态
docker-compose ps
```

### 方式二：从本地机器远程部署

**注意**：需要安装 `sshpass` 工具

```bash
# macOS安装sshpass
brew install hudochenkov/sshpass/sshpass

# 运行部署脚本
./deploy_remote.sh
```

## 访问服务

部署成功后，访问：
- **服务地址**: http://115.190.77.57:5001

## 常用命令

```bash
# 进入项目目录
cd /opt/EmbodiedPulse

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 查看web服务日志
docker-compose logs -f web

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新代码并重启
cd /opt/EmbodiedPulse
git pull origin main
docker-compose up -d --build
docker-compose restart web
```

## 防火墙配置

如果无法访问，需要开放5001端口：

```bash
# CentOS/RHEL
firewall-cmd --permanent --add-port=5001/tcp
firewall-cmd --reload

# Ubuntu/Debian
ufw allow 5001/tcp
ufw reload
```

## 故障排查

1. **查看容器日志**：
```bash
docker-compose logs web
```

2. **检查容器状态**：
```bash
docker-compose ps
docker ps -a
```

3. **重启服务**：
```bash
docker-compose restart
```

4. **完全重建**：
```bash
docker-compose down
docker-compose up -d --build
```

## 环境变量配置

如果需要修改配置，编辑 `docker-compose.yml` 文件中的环境变量部分。

主要配置项：
- `AUTO_FETCH_ENABLED`: 是否启用自动抓取（默认: true）
- `AUTO_FETCH_SCHEDULE`: 论文抓取时间（默认: 每小时整点）
- `AUTO_FETCH_MAX_RESULTS`: 每次抓取数量（默认: 100）

修改后需要重启服务：
```bash
docker-compose restart web
```

