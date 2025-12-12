#!/usr/bin/expect -f
set timeout 600
set SERVER_IP "115.190.77.57"
set SERVER_USER "root"
set SERVER_PASSWORD "ash@2025"
set PROJECT_DIR "/opt/EmbodiedPulse"
set REPO_URL "https://github.com/aramisjiang-wq/EmbodiedPulse2026.git"

spawn ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP}

expect {
    "password:" {
        send "${SERVER_PASSWORD}\r"
        exp_continue
    }
    "# " {
        send "echo '开始部署...'\r"
        expect "# "
        
        # 安装Docker
        send "if ! command -v docker &> /dev/null; then curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh && systemctl start docker && systemctl enable docker && rm get-docker.sh; fi\r"
        expect "# "
        
        # 安装Docker Compose
        send "if ! command -v docker-compose &> /dev/null; then curl -L \"https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose; fi\r"
        expect "# "
        
        # 准备项目目录
        send "mkdir -p ${PROJECT_DIR} && cd ${PROJECT_DIR}\r"
        expect "# "
        
        # 克隆或更新代码
        send "if [ -d \".git\" ]; then git pull origin main || true; else git clone ${REPO_URL} .; fi\r"
        expect "# "
        
        # 停止旧容器
        send "docker-compose down || true\r"
        expect "# "
        
        # 启动服务
        send "docker-compose up -d --build\r"
        expect "# "
        
        # 等待服务启动
        send "sleep 20\r"
        expect "# "
        
        # 初始化数据库
        send "docker-compose exec -T web python3 init_database.py || true\r"
        expect "# "
        
        # 查看状态
        send "docker-compose ps\r"
        expect "# "
        
        send "echo '部署完成！服务地址: http://${SERVER_IP}:5001'\r"
        expect "# "
        
        send "exit\r"
    }
    timeout {
        puts "连接超时"
        exit 1
    }
    "Permission denied" {
        puts "认证失败"
        exit 1
    }
}

expect eof

