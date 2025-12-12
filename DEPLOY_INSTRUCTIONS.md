# 快速部署说明

## 服务器信息
- IP: 115.190.77.57
- 用户: root
- 密码: ash@2025

## 部署步骤

### 步骤1: SSH连接到服务器
```bash
ssh root@115.190.77.57
# 输入密码: ash@2025
```

### 步骤2: 在服务器上执行以下命令

```bash
# 创建项目目录
mkdir -p /opt/EmbodiedPulse
cd /opt/EmbodiedPulse

# 安装Docker（如果未安装）
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl start docker
systemctl enable docker
rm get-docker.sh

# 安装Docker Compose（如果未安装）
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 克隆项目
git clone https://github.com/aramisjiang-wq/EmbodiedPulse2026.git .

# 启动服务
docker-compose up -d --build

# 等待服务启动
sleep 15

# 初始化数据库
docker-compose exec -T web python3 init_database.py

# 查看服务状态
docker-compose ps
```

### 步骤3: 访问服务
打开浏览器访问: http://115.190.77.57:5001

## 或者使用一键部署脚本

在服务器上执行：
```bash
curl -o- https://raw.githubusercontent.com/aramisjiang-wq/EmbodiedPulse2026/main/quick_deploy.sh | bash
```

## 常用管理命令

```bash
cd /opt/EmbodiedPulse

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新代码
git pull origin main
docker-compose up -d --build
docker-compose restart web
```

## 防火墙配置

如果无法访问，开放5001端口：

```bash
# CentOS/RHEL
firewall-cmd --permanent --add-port=5001/tcp
firewall-cmd --reload

# Ubuntu/Debian
ufw allow 5001/tcp
ufw reload
```

