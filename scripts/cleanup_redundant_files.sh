#!/bin/bash
# 清理冗余文件和脚本
# 用于清理不再需要的测试文件、旧脚本、临时文件等

set -e

PROJECT_DIR="/Users/dong/Documents/Cursor/Embodied Pulse"
cd "$PROJECT_DIR"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "清理冗余文件和脚本"
echo "=========================================="
echo ""

# 创建备份目录
BACKUP_DIR="backups/cleanup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 统计变量
moved_count=0
deleted_count=0

# 函数：移动文件到备份目录
move_to_backup() {
    local file=$1
    local reason=$2
    
    if [ -f "$file" ] || [ -d "$file" ]; then
        echo -e "${YELLOW}⚠${NC}  移动: $file"
        echo "    原因: $reason"
        mv "$file" "$BACKUP_DIR/"
        moved_count=$((moved_count + 1))
    fi
}

# 函数：删除文件
delete_file() {
    local file=$1
    local reason=$2
    
    if [ -f "$file" ] || [ -d "$file" ]; then
        echo -e "${RED}✗${NC}  删除: $file"
        echo "    原因: $reason"
        rm -rf "$file"
        deleted_count=$((deleted_count + 1))
    fi
}

echo "1. 清理冗余数据库文件..."
echo ""

# 测试/临时数据库文件（移动到备份）
move_to_backup "hf_dataset_papers.db" "测试数据库，不再需要"
move_to_backup "humanoid_companies.db" "测试数据库，不再需要"

# 可选数据库文件（如果不需要，可以删除或移动）
# move_to_backup "news.db" "可选数据库"
# move_to_backup "jobs.db" "可选数据库"
# move_to_backup "datasets.db" "可选数据库"

echo ""
echo "2. 清理冗余部署脚本..."
echo ""

# 保留的部署脚本（实际使用的）
KEEP_DEPLOY_SCRIPTS=(
    "scripts/deploy_server.sh"           # GitHub Actions使用
    "scripts/create_systemd_service.sh" # 创建服务
    "scripts/nginx_config_fix.sh"        # Nginx配置
    "scripts/setup_https.sh"            # HTTPS配置
    "scripts/fix_port_and_service.sh"   # 修复端口和服务
    "scripts/backup_databases.sh"       # 数据库备份
    "scripts/monitor_system.sh"         # 系统监控
    "scripts/disaster_recovery.sh"      # 故障恢复
    "scripts/setup_backup_and_monitor.sh" # 设置备份和监控
    "scripts/migrate_database_to_server.sh" # 数据库迁移
    "scripts/check_deployment_status.sh" # 部署检查
    "scripts/verify_deployment.sh"      # 部署验证
    "scripts/check_and_fix_scheduler.sh" # 修复调度器
)

# 冗余部署脚本（移动到备份）
REDUNDANT_DEPLOY_SCRIPTS=(
    "scripts/deploy.sh"                 # 旧部署脚本
    "scripts/deploy_auto.sh"            # 旧自动部署
    "scripts/deploy_now.sh"             # 旧部署脚本
    "scripts/deploy_on_server.sh"       # Docker部署（未使用）
    "scripts/deploy_remote.sh"          # 旧远程部署
    "scripts/quick_deploy.sh"           # 快速部署（Docker）
    "scripts/server_auto_deploy.sh"     # 旧自动部署
    "scripts/check_deploy_status.sh"    # 旧检查脚本
    "scripts/check_server_sync.sh"      # 旧同步检查
    "scripts/restart_server.sh"         # 简单重启（可用disaster_recovery.sh替代）
    "scripts/fix_server_502.sh"        # 旧502修复
    "scripts/start_server_with_scheduler.sh" # 旧启动脚本
    "scripts/start_web.sh"              # 旧启动脚本
    "scripts/start_with_auto_fetch.sh"  # 旧启动脚本
    "scripts/服务器初始化部署.sh"      # 中文脚本名
    "scripts/服务器完整修复.sh"        # 中文脚本名
    "scripts/服务器自动部署设置.sh"    # 中文脚本名
    "scripts/修复服务器环境.sh"        # 中文脚本名
    "scripts/修复权限和部署.sh"        # 中文脚本名
    "scripts/完整修复服务器.sh"        # 中文脚本名
    "scripts/检查服务器状态.sh"        # 中文脚本名
    "scripts/立即修复502.sh"            # 中文脚本名
    "scripts/紧急修复服务.sh"           # 中文脚本名
)

for script in "${REDUNDANT_DEPLOY_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        move_to_backup "$script" "冗余部署脚本，已有更好的替代方案"
    fi
done

echo ""
echo "3. 清理测试和临时脚本..."
echo ""

# 测试脚本（移动到备份）
TEST_SCRIPTS=(
    "scripts/test_api_endpoints.py"
    "scripts/test_bilibili_dataflow.py"
    "scripts/test_dataflow_simple.py"
)

for script in "${TEST_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        move_to_backup "$script" "测试脚本，开发时使用"
    fi
done

# 临时抓取脚本（移动到备份）
TEMP_FETCH_SCRIPTS=(
    "scripts/fetch_dec16_papers.py"
    "scripts/fetch_dec_13_15_papers.py"
    "scripts/fetch_december_papers.py"
    "scripts/fetch_latest_december.py"
    "scripts/fetch_specific_date.py"
    "scripts/fetch_for_specific_tags.py"
    "scripts/fetch_benchmark_papers.py"
    "scripts/final_push_to_25.py"
)

for script in "${TEMP_FETCH_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        move_to_backup "$script" "临时抓取脚本，特定日期/用途"
    fi
done

# 临时分类脚本（移动到备份）
TEMP_CLASSIFY_SCRIPTS=(
    "scripts/reclassify_dec16_papers.py"
    "scripts/reclassify_categories.py"
    "scripts/aggressive_reclassify.py"
)

for script in "${TEMP_CLASSIFY_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        move_to_backup "$script" "临时分类脚本，一次性使用"
    fi
done

echo ""
echo "4. 清理其他冗余脚本..."
echo ""

# 其他冗余脚本
OTHER_REDUNDANT=(
    "scripts/monitor_update.sh"         # 旧监控脚本
    "scripts/run_semantic_update_background.sh" # 旧后台脚本
    "scripts/stop_semantic_update.sh"   # 旧停止脚本
    "scripts/check_semantic_progress.sh" # 旧检查脚本
    "scripts/supplement_insufficient_tags.py" # 旧补充脚本
    "scripts/supplement_near_target.py" # 旧补充脚本
    "scripts/delete_uncategorized_papers.py" # 旧删除脚本
    "scripts/check_and_clean_uncategorized.py" # 旧清理脚本
)

for script in "${OTHER_REDUNDANT[@]}"; do
    if [ -f "$script" ]; then
        move_to_backup "$script" "冗余脚本，功能已整合或不再需要"
    fi
done

echo ""
echo "5. 清理deploy目录（如果存在）..."
echo ""

if [ -d "scripts/deploy" ]; then
    move_to_backup "scripts/deploy" "旧部署目录"
fi

echo ""
echo "=========================================="
echo "清理完成"
echo "=========================================="
echo ""
echo "统计:"
echo "  移动文件: $moved_count 个"
echo "  删除文件: $deleted_count 个"
echo "  备份位置: $BACKUP_DIR"
echo ""
echo "⚠️  重要提示:"
echo "  1. 所有文件已移动到备份目录，未直接删除"
echo "  2. 如需恢复，可以从备份目录恢复"
echo "  3. 确认无误后，可以删除备份目录: rm -rf $BACKUP_DIR"
echo ""
echo "保留的核心脚本:"
for script in "${KEEP_DEPLOY_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        echo "  ✅ $script"
    fi
done

