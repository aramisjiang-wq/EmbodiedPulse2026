#!/bin/bash
# 安装 psycopg2 模块

set -e

APP_DIR="/srv/EmbodiedPulse2026"

echo "=========================================="
echo "安装 psycopg2 模块"
echo "=========================================="
echo ""

cd "$APP_DIR"

# 检查是否有虚拟环境
if [ -d "venv" ]; then
    echo "✅ 发现虚拟环境: venv"
    echo "   在虚拟环境中安装 psycopg2..."
    source venv/bin/activate
    pip install psycopg2-binary
    deactivate
    echo "✅ 安装完成"
elif [ -d ".venv" ]; then
    echo "✅ 发现虚拟环境: .venv"
    echo "   在虚拟环境中安装 psycopg2..."
    source .venv/bin/activate
    pip install psycopg2-binary
    deactivate
    echo "✅ 安装完成"
else
    echo "⚠️  未发现虚拟环境，在系统Python中安装..."
    echo "   注意：建议使用虚拟环境"
    
    # 检查是否在conda环境中
    if [ -n "$CONDA_DEFAULT_ENV" ]; then
        echo "   当前在conda环境: $CONDA_DEFAULT_ENV"
        pip install psycopg2-binary
    else
        # 尝试使用python3的pip
        python3 -m pip install psycopg2-binary
    fi
    echo "✅ 安装完成"
fi

echo ""
echo "=========================================="
echo "验证安装"
echo "=========================================="
echo ""

# 验证安装
if [ -d "venv" ]; then
    source venv/bin/activate
    python3 -c "import psycopg2; print('✅ psycopg2 安装成功')" || echo "❌ psycopg2 安装失败"
    deactivate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    python3 -c "import psycopg2; print('✅ psycopg2 安装成功')" || echo "❌ psycopg2 安装失败"
    deactivate
else
    python3 -c "import psycopg2; print('✅ psycopg2 安装成功')" || echo "❌ psycopg2 安装失败"
fi

echo ""
echo "=========================================="
echo "✅ 完成"
echo "=========================================="

