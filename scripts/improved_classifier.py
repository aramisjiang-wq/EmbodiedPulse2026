#!/usr/bin/env python3
"""
改进的分类算法
- 提高匹配阈值
- 添加负面关键词过滤
- 改进评分机制
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models import Paper
from taxonomy import NEW_TAXONOMY, UNCATEGORIZED_KEY
from collections import defaultdict
import re
from typing import List

# 负面关键词列表：如果论文包含这些关键词，降低相关类别得分
NEGATIVE_KEYWORDS = {
    # 物理/天文类（明显不属于具身智能）
    'physics': ['quantum', 'particle', 'cosmic', 'astronomy', 'astrophysics', 'galaxy', 
                'neutron', 'electron', 'photon', 'gravitational wave', 'black hole',
                'nucleus', 'nuclear', 'plasma', 'magnetic field', 'electromagnetic',
                'relativity', 'einstein', 'hawking', 'schwarzschild'],
    
    # 数学类
    'mathematics': ['topology', 'algebra', 'geometry', 'calculus', 'differential equation',
                    'manifold', 'tensor', 'matrix theory', 'number theory'],
    
    # 化学/材料类
    'chemistry': ['molecule', 'chemical', 'reaction', 'catalyst', 'polymer', 'crystal'],
    
    # 生物/医学类（除非明确与机器人相关）
    'biology': ['protein', 'dna', 'rna', 'gene', 'cell', 'tissue', 'organ', 'disease',
                'cancer', 'therapy', 'drug', 'clinical trial'],
    
    # 经济学/金融类
    'economics': ['market', 'trading', 'stock', 'portfolio', 'investment', 'financial',
                  'economy', 'gdp', 'inflation', 'monetary'],
    
    # 社会科学类
    'social': ['society', 'culture', 'politics', 'government', 'policy', 'law'],
}

def has_negative_keywords(text: str) -> bool:
    """
    检查文本是否包含负面关键词（明显不属于具身智能领域）
    
    Args:
        text: 要检查的文本（标题+摘要）
    
    Returns:
        如果包含负面关键词，返回True
    """
    text_lower = text.lower()
    
    for category, keywords in NEGATIVE_KEYWORDS.items():
        for keyword in keywords:
            # 使用单词边界匹配，避免误判
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text_lower):
                return True
    
    return False

def classify_paper_by_keywords_improved(paper: Paper) -> List[str]:
    """
    改进的分类算法
    - 提高匹配阈值（至少2个关键词匹配，或1个精确匹配）
    - 添加负面关键词过滤
    - 改进评分机制
    
    Args:
        paper: 论文对象
    
    Returns:
        匹配的标签列表（可能多个）
    """
    title = (paper.title or '').lower()
    abstract = (paper.abstract or '').lower()
    
    if not title and not abstract:
        return [UNCATEGORIZED_KEY]
    
    text = title + ' ' + abstract
    
    # 负面关键词过滤：如果包含明显的非相关关键词，直接返回Uncategorized
    if has_negative_keywords(text):
        # 但需要排除一些特殊情况，比如"quantum computing"在机器人中的应用
        # 这里先简单处理，后续可以优化
        if not any(kw in text for kw in ['robot', 'robotic', 'embodied', 'manipulation', 'grasp']):
            return [UNCATEGORIZED_KEY]
    
    matched_tags = []
    tag_scores = defaultdict(int)
    
    # 遍历所有标签，计算匹配分数
    for tag_key, (chinese, english, keywords) in NEW_TAXONOMY.items():
        score = 0
        keyword_matches = 0  # 匹配的关键词数量
        
        # 检查关键词匹配（分别检查标题和摘要）
        for keyword in keywords:
            keyword_lower = keyword.lower()
            title_match = False
            abstract_match = False
            
            # 特殊处理：对于"embodied benchmark"
            if keyword_lower == "embodied benchmark":
                if title and 'embodied benchmark' in title:
                    title_match = True
                    score += 5
                    keyword_matches += 1
                elif title and 'embodied' in title and 'benchmark' in title:
                    # 检查是否在较近位置
                    emb_positions = [m.start() for m in re.finditer(r'\bembodied\b', title)]
                    bench_positions = [m.start() for m in re.finditer(r'\bbenchmark\b', title)]
                    for emb_pos in emb_positions:
                        for bench_pos in bench_positions:
                            if abs(emb_pos - bench_pos) <= 50:
                                title_match = True
                                score += 4
                                keyword_matches += 1
                                break
                        if title_match:
                            break
                
                if abstract and 'embodied benchmark' in abstract:
                    abstract_match = True
                    score += 5
                    keyword_matches += 1
                elif abstract and 'embodied' in abstract and 'benchmark' in abstract:
                    emb_positions = [m.start() for m in re.finditer(r'\bembodied\b', abstract)]
                    bench_positions = [m.start() for m in re.finditer(r'\bbenchmark\b', abstract)]
                    for emb_pos in emb_positions:
                        for bench_pos in bench_positions:
                            if abs(emb_pos - bench_pos) <= 50:
                                abstract_match = True
                                score += 4
                                keyword_matches += 1
                                break
                        if abstract_match:
                            break
            else:
                # 其他关键词的常规匹配逻辑
                # 检查标题
                if title:
                    # 1. 精确匹配（单词边界）- 权重最高
                    pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                    if re.search(pattern, title):
                        title_match = True
                        score += 5  # 标题精确匹配权重高
                        keyword_matches += 1
                    # 2. 部分匹配
                    elif keyword_lower in title:
                        title_match = True
                        score += 2
                        keyword_matches += 1
                
                # 检查摘要
                if abstract:
                    # 1. 精确匹配（单词边界）- 权重最高
                    pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                    if re.search(pattern, abstract):
                        abstract_match = True
                        score += 3  # 摘要精确匹配权重中等
                        keyword_matches += 1
                    # 2. 部分匹配
                    elif keyword_lower in abstract:
                        abstract_match = True
                        score += 1
                        keyword_matches += 1
            
            # 如果标题和摘要都匹配，额外加分
            if title_match and abstract_match:
                score += 2
        
        # 检查英文标签名
        eng_lower = english.lower()
        if title:
            pattern = r'\b' + re.escape(eng_lower) + r'\b'
            if re.search(pattern, title):
                score += 3
            elif eng_lower in title:
                score += 1.5
        
        if abstract:
            pattern = r'\b' + re.escape(eng_lower) + r'\b'
            if re.search(pattern, abstract):
                score += 2
            elif eng_lower in abstract:
                score += 1
        
        # 提高匹配阈值：至少2个关键词匹配，或得分>=5
        if keyword_matches >= 2 or score >= 5:
            tag_scores[tag_key] = score
    
    # 按分数排序，取最高分的标签
    if tag_scores:
        sorted_tags = sorted(
            tag_scores.items(),
            key=lambda x: (-x[1], x[0])  # 先按分数降序，再按标签键排序
        )
        # 只取分数最高的1个标签
        matched_tags.append(sorted_tags[0][0])
    
    # 如果没有匹配，使用兜底分类逻辑
    if not matched_tags:
        # 兜底分类：根据标题和摘要中的常见词汇进行模糊匹配
        # 但要求更严格，避免误分类
        robot_words = [
            'robot', 'robotic', 'robotics', 'embodied', 'agent', 'autonomous',
            'human-robot', 'robot learning', 'robotic system', 'manipulator',
            'manipulation', 'grasp', 'grasping'
        ]
        has_robot_context = any(word in text for word in robot_words)
        
        if has_robot_context:
            # 根据关键词进行兜底分类（优先级从高到低）
            if 'vla' in text or 'vision language action' in text or 'embodied agent' in text:
                matched_tags.append('Operation/Vision-Language-Action Models')
            elif 'vlm' in text or 'vision language' in text or 'multimodal' in text:
                matched_tags.append('Perception/Vision-Language Model')
            elif '3d' in text or 'point cloud' in text or 'depth' in text or 'lidar' in text:
                matched_tags.append('Perception/3D Perception')
            elif 'detect' in text or 'detection' in text:
                matched_tags.append('Perception/Object Detection')
            elif 'segment' in text or 'segmentation' in text:
                matched_tags.append('Perception/Instance Segmentation')
            elif 'grasp' in text or 'grasping' in text or 'manipulation' in text:
                matched_tags.append('Operation/Grasp')
            elif 'reinforcement learning' in text or 'rl' in text:
                matched_tags.append('Learning/Reinforcement Learning')
            elif 'imitation learning' in text or 'behavioral cloning' in text:
                matched_tags.append('Learning/Imitation Learning')
            elif 'planning' in text or 'navigation' in text:
                matched_tags.append('Decision/Task Planning')
            elif 'perception' in text or 'vision' in text:
                matched_tags.append('Perception/2D Perception')
            else:
                matched_tags.append('General-Robot')
        else:
            # 没有机器人相关关键词，返回未分类
            matched_tags.append(UNCATEGORIZED_KEY)
    
    return matched_tags

