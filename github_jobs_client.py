#!/usr/bin/env python3
"""
GitHub API客户端 - 获取招聘信息
从Awesome-Embodied-AI-Job仓库获取"Rolling Recruitment | 滚动招聘"部分
"""
import requests
import base64
import re
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# GitHub仓库配置
GITHUB_REPO = "StarCycle/Awesome-Embodied-AI-Job"
GITHUB_API_BASE = "https://api.github.com"


def fetch_readme_from_github(max_retries: int = 3) -> Optional[str]:
    """
    从GitHub API获取README.md内容（带重试机制）
    
    Args:
        max_retries: 最大重试次数
    
    Returns:
        Markdown内容字符串，如果失败返回None
    """
    url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/readme"
    
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Embodied-AI-Daily/1.0'
    }
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"正在从GitHub获取README: {GITHUB_REPO} (尝试 {attempt}/{max_retries})")
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # GitHub API返回的是Base64编码的内容
                content = base64.b64decode(data.get('content', '')).decode('utf-8')
                logger.info(f"成功获取README，大小: {len(content)} 字符")
                return content
            elif response.status_code == 404:
                logger.error(f"仓库不存在: {GITHUB_REPO}")
                return None  # 404不需要重试
            elif response.status_code == 403:
                logger.warning(f"GitHub API速率限制，尝试 {attempt}/{max_retries}")
                if attempt < max_retries:
                    import time
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    logger.error("GitHub API速率限制，已达到最大重试次数")
                    return None
            else:
                logger.warning(f"获取README失败: HTTP {response.status_code} (尝试 {attempt}/{max_retries})")
                if attempt < max_retries:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"获取README失败: HTTP {response.status_code}, {response.text[:200]}")
                    return None
        
        except requests.exceptions.Timeout:
            logger.warning(f"请求超时 (尝试 {attempt}/{max_retries})")
            if attempt < max_retries:
                import time
                time.sleep(2 ** attempt)
                continue
            else:
                logger.error("请求超时，已达到最大重试次数")
                return None
        except requests.exceptions.SSLError as e:
            logger.warning(f"SSL错误 (尝试 {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                import time
                time.sleep(2 ** attempt)
                continue
            else:
                logger.error("SSL错误，已达到最大重试次数")
                return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"请求异常 (尝试 {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                import time
                time.sleep(2 ** attempt)
                continue
            else:
                logger.error(f"请求异常，已达到最大重试次数: {e}")
                return None
    
    return None


def extract_rolling_recruitment_section(markdown_content: str) -> Optional[str]:
    """
    从Markdown内容中提取"Rolling Recruitment | 滚动招聘"部分
    
    Args:
        markdown_content: 完整的Markdown内容
    
    Returns:
        滚动招聘部分的Markdown内容，如果未找到返回None
    """
    if not markdown_content:
        return None
    
    # 查找"Rolling Recruitment"或"滚动招聘"部分
    # 实际格式：## 2. Rolling Recruitment | 滚动招聘
    # 下一个主要部分应该是 ## 3. 或 ## 4. 等
    patterns = [
        r'##+\s*\d+\.\s*Rolling\s+Recruitment[^\n]*滚动招聘[^\n]*\n(.*?)(?=##+\s+\d+\.\s+[^R]|$)',
        r'##+\s*\d+\.\s*滚动招聘[^\n]*Rolling\s+Recruitment[^\n]*\n(.*?)(?=##+\s+\d+\.\s+[^滚]|$)',
        r'##+\s*Rolling\s+Recruitment[^\n]*滚动招聘[^\n]*\n(.*?)(?=##+\s+\d+\.\s+|##+\s+[^R]|$)',
        r'##+\s*滚动招聘[^\n]*Rolling\s+Recruitment[^\n]*\n(.*?)(?=##+\s+\d+\.\s+|##+\s+[^滚]|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, markdown_content, re.DOTALL | re.IGNORECASE)
        if match:
            section = match.group(1).strip()
            logger.info(f"找到Rolling Recruitment部分，长度: {len(section)} 字符")
            return section
    
    logger.warning("未找到Rolling Recruitment部分")
    return None


def parse_job_entry(line: str, prev_date: str = None) -> Optional[Dict]:
    """
    解析单个招聘条目
    
    格式示例：
    **[2025.12.7]**
    [蔚来(上海) - 多模态大模型/VLA/世界模型 - 全职](https://mp.weixin.qq.com/s/...)
    
    或：
    **[2025.12.7]**
    国家地方共建人形机器人创新中心 - 2025校招/社招集中招聘
    
    Args:
        line: 单行文本
        prev_date: 上一行的日期（如果当前行没有日期）
    
    Returns:
        解析后的招聘信息字典，如果解析失败返回None
    """
    if not line or not line.strip():
        return None
    
    line = line.strip()
    
    # 匹配日期格式：[2025.12.7] 或 [2025.3.10]
    date_pattern = r'\*\*\[(\d{4}\.\d{1,2}\.\d{1,2})\]\*\*'
    date_match = re.search(date_pattern, line)
    
    source_date = None
    if date_match:
        source_date = date_match.group(1)
        # 移除日期标记
        remaining = re.sub(date_pattern, '', line).strip()
    elif prev_date:
        source_date = prev_date
        remaining = line
    else:
        # 没有日期，跳过
        return None
    
    if not remaining:
        return None
    
    # 提取链接：[文本](URL)
    link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    link_match = re.search(link_pattern, remaining)
    
    title = ""
    link = ""
    
    if link_match:
        # 有链接的情况
        title = link_match.group(1).strip()
        link = link_match.group(2).strip()
    else:
        # 没有链接，整个remaining就是标题
        title = remaining
    
    # 清理标题中的多余标记
    title = re.sub(r'^\*\*', '', title).strip()
    title = re.sub(r'\*\*$', '', title).strip()
    
    if not title:
        return None
    
    # 尝试提取公司、职位类型等信息
    company = ""
    job_type = ""
    location = ""
    
    # 解析标题格式：公司(地点) - 职位描述 - 职位类型
    # 或：公司 - 职位描述 - 职位类型
    parts = [p.strip() for p in title.split(' - ')]
    
    if len(parts) >= 1:
        company_part = parts[0]
        # 提取地点（如果有括号）
        location_match = re.search(r'\(([^\)]+)\)', company_part)
        if location_match:
            location = location_match.group(1)
            company = re.sub(r'\([^\)]+\)', '', company_part).strip()
        else:
            company = company_part
    
    if len(parts) >= 2:
        description = ' - '.join(parts[1:-1]) if len(parts) > 2 else parts[1]
    else:
        description = ""
    
    if len(parts) >= 2:
        job_type = parts[-1]
    
    return {
        'title': title,
        'description': description,
        'link': link,
        'update_date': source_date,  # 使用源日期作为更新日期
        'source_date': source_date,
        'company': company,
        'location': location,
        'job_type': job_type
    }


def parse_jobs_from_section(section_content: str) -> List[Dict]:
    """
    从滚动招聘部分解析所有招聘信息
    
    Args:
        section_content: 滚动招聘部分的Markdown内容
    
    Returns:
        招聘信息列表
    """
    if not section_content:
        return []
    
    jobs = []
    lines = section_content.split('\n')
    current_date = None
    
    for line in lines:
        line = line.strip()
        # 跳过空行和注释
        if not line or line.startswith('<!--'):
            continue
        
        # 检查是否是日期行
        date_pattern = r'\*\*\[(\d{4}\.\d{1,2}\.\d{1,2})\]\*\*'
        date_match = re.search(date_pattern, line)
        if date_match:
            current_date = date_match.group(1)
            continue
        
        # 尝试解析招聘条目（使用当前日期）
        job = parse_job_entry(line, prev_date=current_date)
        if job:
            jobs.append(job)
    
    logger.info(f"解析到 {len(jobs)} 条招聘信息")
    return jobs


def fetch_all_jobs() -> List[Dict]:
    """
    从GitHub获取所有招聘信息
    
    Returns:
        招聘信息列表
    """
    # 1. 获取README内容
    markdown_content = fetch_readme_from_github()
    if not markdown_content:
        logger.error("无法获取README内容")
        return []
    
    # 2. 提取滚动招聘部分
    section = extract_rolling_recruitment_section(markdown_content)
    if not section:
        logger.error("无法提取Rolling Recruitment部分")
        return []
    
    # 3. 解析招聘信息
    jobs = parse_jobs_from_section(section)
    
    return jobs


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("测试GitHub招聘信息抓取")
    print("=" * 60)
    
    jobs = fetch_all_jobs()
    
    print(f"\n获取到 {len(jobs)} 条招聘信息:\n")
    for i, job in enumerate(jobs[:10], 1):
        print(f"{i}. [{job['update_date']}] {job['title']}")
        if job['link']:
            print(f"   链接: {job['link'][:60]}...")
        if job['company']:
            print(f"   公司: {job['company']}")
        if job['job_type']:
            print(f"   类型: {job['job_type']}")
        print()

