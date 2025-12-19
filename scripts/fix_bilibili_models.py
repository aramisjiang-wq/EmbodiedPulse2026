#!/usr/bin/env python3
"""
修复bilibili_models.py的缩进和format_number导入问题
"""
import re
import sys

def fix_bilibili_models():
    file_path = '/srv/EmbodiedPulse2026/bilibili_models.py'
    
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 修复后的行
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # 检查是否是to_dict方法
        if 'def to_dict(self):' in line:
            new_lines.append(line)
            i += 1
            
            # 跳过文档字符串和注释
            while i < len(lines) and (lines[i].strip().startswith('"""') or 
                                      lines[i].strip().startswith('#') or 
                                      lines[i].strip() == ''):
                new_lines.append(lines[i])
                i += 1
            
            # 现在应该遇到try或import语句
            if i < len(lines):
                if 'try:' in lines[i]:
                    # 已经有try，检查下一行
                    new_lines.append(lines[i])
                    i += 1
                    
                    # 如果下一行是import但没有正确缩进，或者下一行是空的
                    if i < len(lines):
                        next_line = lines[i]
                        if 'from bilibili_client import format_number' in next_line:
                            # import行存在，检查是否有except
                            new_lines.append(next_line)
                            i += 1
                            
                            # 检查是否有except
                            if i < len(lines) and 'except ImportError:' not in lines[i]:
                                # 没有except，添加
                                indent = len(next_line) - len(next_line.lstrip())
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
                        elif next_line.strip() == '' or next_line.strip().startswith('#'):
                            # try后面是空行或注释，需要添加import
                            indent = len(lines[i-1]) - len(lines[i-1].lstrip())
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
                elif 'from bilibili_client import format_number' in line:
                    # 没有try，直接是import，需要添加try/except
                    indent = len(line) - len(line.lstrip())
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
        
        new_lines.append(line)
        i += 1
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ 修复完成")

if __name__ == '__main__':
    try:
        fix_bilibili_models()
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

