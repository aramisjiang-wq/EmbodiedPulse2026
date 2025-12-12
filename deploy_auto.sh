#!/bin/bash
# 自动化部署脚本（使用expect处理SSH密码）

SERVER_IP="115.190.77.57"
SERVER_USER="root"
SERVER_PASSWORD="ash@2025"
PROJECT_DIR="/opt/EmbodiedPulse"
REPO_URL="https://github.com/aramisjiang-wq/EmbodiedPulse2026.git"

echo "=========================================="
echo "开始部署到服务器: ${SERVER_IP}"
echo "=========================================="

# 检查expect是否安装
if ! command -v expect &> /dev/null; then
    echo "安装expect..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install expect
    else
        echo "请先安装expect: sudo apt-get install expect 或 sudo yum install expect"
        exit 1
    fi
fi

# 创建expect脚本
cat > /tmp/deploy_expect.sh << 'EXPECT_SCRIPT'
#!/usr/bin/expect -f
set timeout 300
set SERVER_IP [lindex $argv 0]
set SERVER_USER [lindex $argv 1]
set SERVER_PASSWORD [lindex $argv 2]
set PROJECT_DIR [lindex $argv 3]
set REPO_URL [lindex $argv 4]

spawn ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP}

expect {
    "password:" {
        send "${SERVER_PASSWORD}\r"
        exp_continue
    }
    "# " {
        send "cd ${PROJECT_DIR} || mkdir -p ${PROJECT_DIR} && cd ${PROJECT_DIR}\r"
        expect "# "
        
        send "if [ ! -d .git ]; then git clone ${REPO_URL} .; else git pull origin main; fi\r"
        expect "# "
        
        send "if ! command -v docker &> /dev/null; then curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh && systemctl start docker && systemctl enable docker && rm get-docker.sh; fi\r"
        expect "# "
        
        send "if ! command -v docker-compose &> /dev/null; then curl -L \"https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose; fi\r"
        expect "# "
        
        send "docker-compose down || true\r"
        expect "# "
        
        send "docker-compose up -d --build\r"
        expect "# "
        
        send "sleep 10\r"
        expect "# "
        
        send "docker-compose exec -T web python3 init_database.py || true\r"
        expect "# "
        
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
}

expect eof
EXPECT_SCRIPT

chmod +x /tmp/deploy_expect.sh

# 执行expect脚本
expect /tmp/deploy_expect.sh ${SERVER_IP} ${SERVER_USER} ${SERVER_PASSWORD} ${PROJECT_DIR} ${REPO_URL}

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo "服务地址: http://${SERVER_IP}:5001"
echo ""

