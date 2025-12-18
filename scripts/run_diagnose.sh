#!/bin/bash
# 使用虚拟环境运行诊断脚本

set -e

APP_DIR="/srv/EmbodiedPulse2026"

cd "$APP_DIR"

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "✅ 使用虚拟环境运行诊断脚本..."
    venv/bin/python3 scripts/diagnose_data_issues.py
elif [ -d ".venv" ]; then
    echo "✅ 使用虚拟环境运行诊断脚本..."
    .venv/bin/python3 scripts/diagnose_data_issues.py
else
    echo "⚠️  未发现虚拟环境，使用系统Python运行..."
    python3 scripts/diagnose_data_issues.py
fi

