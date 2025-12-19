#!/bin/bash
# 清理并修复bilibili_models.py

cd /srv/EmbodiedPulse2026 || exit 1

echo "============================================================"
echo "清理并修复bilibili_models.py"
echo "============================================================"
echo ""

# 1. 备份当前文件
cp bilibili_models.py bilibili_models.py.broken.$(date +%Y%m%d_%H%M%S)

# 2. 尝试从git恢复
echo "【1. 尝试从git恢复】"
echo "----------------------------------------"
if git checkout HEAD -- bilibili_models.py 2>/dev/null; then
    echo "✅ 从git恢复成功"
else
    echo "⚠️  git恢复失败，使用手动修复"
fi

# 3. 检查恢复后的文件
echo ""
echo "【2. 检查文件状态】"
echo "----------------------------------------"
python3 -m py_compile bilibili_models.py 2>&1 && echo "✅ 语法正确" || {
    echo "❌ 仍有语法错误，需要手动修复"
    echo ""
    echo "查看问题区域:"
    sed -n '58,75p' bilibili_models.py
}

# 4. 如果还有问题，使用Python脚本修复
if ! python3 -m py_compile bilibili_models.py 2>&1 > /dev/null; then
    echo ""
    echo "【3. 使用Python脚本修复】"
    echo "----------------------------------------"
    python3 << 'PYEOF'
import re

file_path = 'bilibili_models.py'

# 读取文件
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复：清理重复的try语句
# 模式：多个连续的try:行
content = re.sub(r'(\s+try:\s*\n)+', r'\1', content)

# 修复：确保每个to_dict方法中的try/except结构正确
# 查找所有to_dict方法
def fix_to_dict(match):
    method_body = match.group(0)
    
    # 如果已经有正确的try/except结构，直接返回
    if 'try:' in method_body and 'except ImportError:' in method_body:
        # 检查是否有重复
        if method_body.count('try:') > 1:
            # 清理重复的try
            lines = method_body.split('\n')
            new_lines = []
            in_try_block = False
            for line in lines:
                if 'try:' in line and not in_try_block:
                    in_try_block = True
                    new_lines.append(line)
                elif 'try:' in line and in_try_block:
                    # 跳过重复的try
                    continue
                elif 'except ImportError:' in line:
                    in_try_block = False
                    new_lines.append(line)
                else:
                    new_lines.append(line)
            return '\n'.join(new_lines)
        return method_body
    
    # 如果没有try/except，添加
    if 'from bilibili_client import format_number' in method_body and 'try:' not in method_body:
        indent = ' ' * 8  # 假设8个空格缩进
        replacement = f'''{indent}try:
{indent}    from bilibili_client import format_number
{indent}except ImportError:
{indent}    # 如果导入失败，定义本地format_number函数
{indent}    def format_number(num: int) -> str:
{indent}        """格式化数字（万、亿）"""
{indent}        if num >= 100000000:
{indent}            return f"{{num / 100000000:.1f}}亿"
{indent}        elif num >= 10000:
{indent}            return f"{{num / 10000:.1f}}万"
{indent}        else:
{indent}            return str(num)
{indent}
'''
        method_body = method_body.replace('        from bilibili_client import format_number', replacement.strip())
    
    return method_body

# 匹配to_dict方法
pattern = r'(    def to_dict\(self\):.*?)(?=\n    def |\nclass |\Z)'
content = re.sub(pattern, fix_to_dict, content, flags=re.DOTALL)

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 修复完成")
PYEOF
fi

# 5. 最终验证
echo ""
echo "【4. 最终验证】"
echo "----------------------------------------"
python3 -m py_compile bilibili_models.py && echo "✅ 语法正确" || {
    echo "❌ 仍有语法错误"
    echo ""
    echo "查看问题区域:"
    sed -n '58,90p' bilibili_models.py
    exit 1
}

echo ""
echo "✅ 修复完成，文件已就绪"

