#!/bin/bash
# 部署论文数据更新功能到服务器
# 使用方法: ./scripts/deploy_paper_update_feature.sh

set -e

APP_DIR="/srv/EmbodiedPulse2026"
SERVICE_NAME="embodiedpulse"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "部署论文数据更新功能"
echo "=========================================="
echo ""

# 检查是否在服务器上
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}错误: 应用目录不存在: $APP_DIR${NC}"
    echo "请确保在服务器上运行此脚本，或修改 APP_DIR 变量"
    exit 1
fi

cd "$APP_DIR"

# ==================== 1. 检查Git状态 ====================
echo -e "${BLUE}1. 检查Git状态...${NC}"
if [ -d ".git" ]; then
    # 检查是否有未提交的更改
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}警告: 有未提交的更改${NC}"
        git status --short
        read -p "是否继续部署? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # 拉取最新代码
    echo "拉取最新代码..."
    git fetch origin
    CURRENT_BRANCH=$(git branch --show-current)
    echo "当前分支: $CURRENT_BRANCH"
    
    if [ "$CURRENT_BRANCH" != "main" ]; then
        echo -e "${YELLOW}警告: 当前不在main分支，切换到main分支${NC}"
        git checkout main
    fi
    
    git pull origin main
    echo -e "${GREEN}✓ 代码已更新${NC}"
else
    echo -e "${RED}错误: 不是Git仓库${NC}"
    exit 1
fi

# ==================== 2. 检查修改的文件 ====================
echo ""
echo -e "${BLUE}2. 检查修改的文件...${NC}"
MODIFIED_FILES=(
    "app.py"
    "auth_routes.py"
    "update_semantic_scholar_data.py"
    "templates/admin_papers.html"
    "static/js/admin_papers.js"
)

for file in "${MODIFIED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file 存在"
    else
        echo -e "${RED}✗${NC} $file 不存在"
    fi
done

# ==================== 3. 检查Python语法 ====================
echo ""
echo -e "${BLUE}3. 检查Python语法...${NC}"
PYTHON_FILES=(
    "app.py"
    "auth_routes.py"
    "update_semantic_scholar_data.py"
)

for file in "${PYTHON_FILES[@]}"; do
    if python3 -m py_compile "$file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $file 语法正确"
    else
        echo -e "${RED}✗${NC} $file 语法错误"
        exit 1
    fi
done

# ==================== 4. 检查依赖 ====================
echo ""
echo -e "${BLUE}4. 检查依赖...${NC}"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "虚拟环境已激活"
    
    # 检查关键依赖
    REQUIRED_PACKAGES=("flask" "sqlalchemy" "arxiv" "requests")
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if python3 -c "import $package" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $package 已安装"
        else
            echo -e "${YELLOW}⚠${NC} $package 未安装"
        fi
    done
else
    echo -e "${YELLOW}警告: 虚拟环境不存在${NC}"
fi

# ==================== 5. 备份当前版本 ====================
echo ""
echo -e "${BLUE}5. 创建备份...${NC}"
BACKUP_DIR="$APP_DIR/backups/deploy_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 备份关键文件
for file in "${MODIFIED_FILES[@]}"; do
    if [ -f "$file" ]; then
        mkdir -p "$BACKUP_DIR/$(dirname "$file")"
        cp "$file" "$BACKUP_DIR/$file"
    fi
done

echo -e "${GREEN}✓${NC} 备份已创建: $BACKUP_DIR"

# ==================== 6. 重启服务 ====================
echo ""
echo -e "${BLUE}6. 重启服务...${NC}"
if command -v systemctl >/dev/null 2>&1; then
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "停止服务..."
        systemctl stop "$SERVICE_NAME"
        sleep 2
    fi
    
    echo "启动服务..."
    systemctl start "$SERVICE_NAME"
    sleep 3
    
    # 检查服务状态
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "${GREEN}✓${NC} 服务已启动"
        systemctl status "$SERVICE_NAME" --no-pager -l | head -10
    else
        echo -e "${RED}✗${NC} 服务启动失败"
        echo "查看日志: journalctl -u $SERVICE_NAME -n 50"
        exit 1
    fi
else
    echo -e "${YELLOW}警告: systemctl 不可用，请手动重启服务${NC}"
fi

# ==================== 7. 验证部署 ====================
echo ""
echo -e "${BLUE}7. 验证部署...${NC}"

# 检查服务是否响应
sleep 2
if curl -s -f http://localhost:5001/api/admin/papers/stats > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} API接口可访问"
else
    echo -e "${YELLOW}⚠${NC} API接口可能不可访问（需要认证）"
fi

# 检查新API端点是否存在（通过检查代码）
if grep -q "papers/fetch-arxiv" "$APP_DIR/auth_routes.py"; then
    echo -e "${GREEN}✓${NC} ArXiv抓取API已部署"
else
    echo -e "${RED}✗${NC} ArXiv抓取API未找到"
fi

if grep -q "papers/update-semantic" "$APP_DIR/auth_routes.py"; then
    echo -e "${GREEN}✓${NC} Semantic Scholar更新API已部署"
else
    echo -e "${RED}✗${NC} Semantic Scholar更新API未找到"
fi

# ==================== 8. 完成 ====================
echo ""
echo "=========================================="
echo -e "${GREEN}部署完成！${NC}"
echo "=========================================="
echo ""
echo "修改的文件:"
for file in "${MODIFIED_FILES[@]}"; do
    echo "  - $file"
done
echo ""
echo "下一步:"
echo "  1. 访问管理端: https://your-domain.com/admin/papers"
echo "  2. 测试'从ArXiv拉取新论文'按钮"
echo "  3. 测试'更新Semantic Scholar数据'按钮"
echo ""
echo "如果遇到问题:"
echo "  查看日志: journalctl -u $SERVICE_NAME -f"
echo "  回滚备份: cp -r $BACKUP_DIR/* $APP_DIR/"
echo ""

