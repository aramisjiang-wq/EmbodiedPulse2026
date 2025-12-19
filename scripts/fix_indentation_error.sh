#!/bin/bash
# 修复bilibili_models.py的缩进错误

cd /srv/EmbodiedPulse2026 || exit 1

echo "============================================================"
echo "修复缩进错误"
echo "============================================================"
echo ""

# 备份
cp bilibili_models.py bilibili_models.py.backup.$(date +%Y%m%d_%H%M%S)

# 查看问题行
echo "【检查问题行】"
echo "----------------------------------------"
sed -n '58,70p' bilibili_models.py

# 使用Python修复
python3 << 'PYEOF'
import re

# 读取文件
with open('bilibili_models.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 修复缩进问题
new_lines = []
i = 0
in_to_dict = False
to_dict_count = 0

while i < len(lines):
    line = lines[i]
    
    # 检测to_dict方法
    if 'def to_dict(self):' in line:
        in_to_dict = True
        to_dict_count += 1
        new_lines.append(line)
        i += 1
        continue
    
    # 在to_dict方法中
    if in_to_dict:
        # 如果遇到try但没有正确缩进的import
        if 'try:' in line and i + 1 < len(lines):
            new_lines.append(line)
            i += 1
            # 检查下一行
            if i < len(lines):
                next_line = lines[i]
                # 如果下一行是import但没有正确缩进
                if 'from bilibili_client import format_number' in next_line:
                    # 修复缩进
                    indent = len(line) - len(line.lstrip())
                    new_lines.append(' ' * (indent + 4) + 'from bilibili_client import format_number\n')
                    new_lines.append(' ' * indent + 'except ImportError:\n')
                    new_lines.append(' ' * (indent + 4) + '# 如果导入失败，定义本地format_number函数\n')
                    new_lines.append(' ' * (indent + 4) + 'def format_number(num: int) -> str:\n')
                    new_lines.append(' ' * (indent + 8) + '"""格式化数字（万、亿）"""\n')
                    new_lines.append(' ' * (indent + 8) + 'if num >= 100000000:\n')
                    new_lines.append(' ' * (indent + 12) + 'return f"{num / 100000000:.1f}亿"\n')
                    new_lines.append(' ' * (indent + 8) + 'elif num >= 10000:\n')
                    new_lines.append(' ' * (indent + 12) + 'return f"{num / 10000:.1f}万"\n')
                    new_lines.append(' ' * (indent + 8) + 'else:\n')
                    new_lines.append(' ' * (indent + 12) + 'return str(num)\n')
                    new_lines.append(' ' * indent + '\n')
                    i += 1
                    continue
                else:
                    new_lines.append(next_line)
                    i += 1
                    continue
        
        # 如果遇到简单的import（没有try/except）
        if 'from bilibili_client import format_number' in line and 'try:' not in ''.join(new_lines[-5:]):
            # 检查是否在to_dict方法中
            indent = len(line) - len(line.lstrip())
            # 替换为带try/except的版本
            new_lines.append(' ' * indent + 'try:\n')
            new_lines.append(' ' * (indent + 4) + 'from bilibili_client import format_number\n')
            new_lines.append(' ' * indent + 'except ImportError:\n')
            new_lines.append(' ' * (indent + 4) + '# 如果导入失败，定义本地format_number函数\n')
            new_lines.append(' ' * (indent + 4) + 'def format_number(num: int) -> str:\n')
            new_lines.append(' ' * (indent + 8) + '"""格式化数字（万、亿）"""\n')
            new_lines.append(' ' * (indent + 8) + 'if num >= 100000000:\n')
            new_lines.append(' ' * (indent + 12) + 'return f"{num / 100000000:.1f}亿"\n')
            new_lines.append(' ' * (indent + 8) + 'elif num >= 10000:\n')
            new_lines.append(' ' * (indent + 12) + 'return f"{num / 10000:.1f}万"\n')
            new_lines.append(' ' * (indent + 8) + 'else:\n')
            new_lines.append(' ' * (indent + 12) + 'return str(num)\n')
            new_lines.append(' ' * indent + '\n')
            i += 1
            continue
        
        # 如果遇到return，说明to_dict方法结束
        if line.strip().startswith('return {') or (line.strip().startswith('return') and '{' in line):
            in_to_dict = False
    
    new_lines.append(line)
    i += 1

# 写回文件
with open('bilibili_models.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ 修复完成")
PYEOF

# 验证语法
echo ""
echo "【验证语法】"
echo "----------------------------------------"
python3 -m py_compile bilibili_models.py 2>&1 && echo "✅ 语法正确" || {
    echo "❌ 语法错误，查看详细错误:"
    python3 -m py_compile bilibili_models.py 2>&1
    echo ""
    echo "查看问题行:"
    sed -n '58,75p' bilibili_models.py
}

