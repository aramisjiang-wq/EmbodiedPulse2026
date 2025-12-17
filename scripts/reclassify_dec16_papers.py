#!/usr/bin/env python3
"""
重新分类12月16日的未分类论文
使用更智能的分类算法
"""
import sys
import os
from datetime import date
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models import get_session, Paper
from sqlalchemy import func
from taxonomy import NEW_TAXONOMY, normalize_category, UNCATEGORIZED_KEY
from collections import defaultdict
import re
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

def classify_paper_by_keywords(paper: Paper) -> str:
    """
    根据关键词匹配对论文进行分类
    使用更宽松的匹配策略
    """
    title = (paper.title or '').lower()
    abstract = (paper.abstract or '').lower()
    
    if not title and not abstract:
        return UNCATEGORIZED_KEY
    
    text = title + ' ' + abstract
    tag_scores = defaultdict(int)
    
    # 遍历所有标签，计算匹配分数
    for tag_key, (chinese, english, keywords) in NEW_TAXONOMY.items():
        score = 0
        
        # 检查关键词匹配
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # 1. 精确匹配（单词边界）- 权重最高
            pattern = r'\b' + re.escape(keyword_lower) + r'\b'
            if re.search(pattern, title):
                score += 5  # 标题精确匹配权重高
            elif re.search(pattern, abstract):
                score += 3  # 摘要精确匹配权重中等
            
            # 2. 部分匹配
            if keyword_lower in title:
                score += 2
            if keyword_lower in abstract:
                score += 1
        
        # 3. 检查英文标签名
        eng_lower = english.lower()
        if eng_lower in title:
            score += 3
        if eng_lower in abstract:
            score += 2
        
        # 4. 检查中文标签名（如果可能）
        chinese_lower = chinese.lower()
        if chinese_lower in title or chinese_lower in abstract:
            score += 2
        
        if score > 0:
            tag_scores[tag_key] = score
    
    # 如果有匹配，返回得分最高的标签
    if tag_scores:
        sorted_tags = sorted(tag_scores.items(), key=lambda x: -x[1])
        best_tag = sorted_tags[0][0]
        best_score = sorted_tags[0][1]
        
        # 如果得分太低，可能需要更宽松的策略
        if best_score < 3:
            # 尝试更宽松的匹配
            return classify_with_fallback(paper, tag_scores)
        
        return best_tag
    
    # 如果完全没匹配，使用兜底分类
    return classify_with_fallback(paper, {})

def classify_with_fallback(paper: Paper, tag_scores: dict) -> str:
    """
    兜底分类策略：基于常见关键词的简单匹配
    """
    title = (paper.title or '').lower()
    abstract = (paper.abstract or '').lower()
    text = title + ' ' + abstract
    
    # 机器人相关
    if any(kw in text for kw in ['robot', 'robotic', 'robotics', 'autonomous']):
        if any(kw in text for kw in ['humanoid', 'bipedal']):
            return 'Motion/Humanoid'
        elif any(kw in text for kw in ['quadruped', 'legged']):
            return 'Motion/Quadruped'
        elif any(kw in text for kw in ['manipulation', 'grasp', 'grasping']):
            return 'Operation/Grasp'
        elif any(kw in text for kw in ['navigation', 'locomotion', 'walking']):
            return 'Motion/Locomotion'
        else:
            return 'General-Robot'
    
    # 感知相关
    if any(kw in text for kw in ['perception', 'vision', 'visual', 'image', 'camera']):
        if any(kw in text for kw in ['3d', 'depth', 'point cloud', 'lidar', 'stereo']):
            return 'Perception/3D Perception'
        elif any(kw in text for kw in ['detection', 'detect', 'object detection']):
            return 'Perception/Object Detection'
        elif any(kw in text for kw in ['segmentation', 'segment', 'mask']):
            return 'Perception/Instance Segmentation'
        elif any(kw in text for kw in ['vlm', 'vision language', 'multimodal', 'clip']):
            return 'Perception/Vision-Language Model'
        else:
            return 'Perception/2D Perception'
    
    # VLA相关
    if any(kw in text for kw in ['vla', 'vision language action', 'embodied agent', 'embodied ai']):
        return 'Operation/VLA'
    
    # 学习相关
    if any(kw in text for kw in ['reinforcement learning', 'rl', 'ppo', 'sac', 'actor-critic']):
        return 'Learning/RL'
    elif any(kw in text for kw in ['imitation learning', 'behavioral cloning', 'demonstration']):
        return 'Learning/IL'
    
    # 规划相关
    if any(kw in text for kw in ['planning', 'navigation', 'path planning', 'task planning']):
        return 'Decision/Task Planning'
    
    # 操作相关
    if any(kw in text for kw in ['grasp', 'grasping', 'manipulation', 'pick and place']):
        return 'Operation/Grasp'
    elif any(kw in text for kw in ['dexterous', 'fine manipulation', 'in-hand']):
        return 'Operation/Dexterous'
    elif any(kw in text for kw in ['bimanual', 'dual arm', 'two-arm']):
        return 'Operation/Bimanual'
    
    # 如果tag_scores中有低分匹配，返回得分最高的
    if tag_scores:
        sorted_tags = sorted(tag_scores.items(), key=lambda x: -x[1])
        return sorted_tags[0][0]
    
    return UNCATEGORIZED_KEY

def reclassify_dec16_papers():
    """重新分类12月16日的未分类论文"""
    session = get_session()
    target_date = date(2025, 12, 16)
    
    # 获取12月16日的未分类论文
    uncategorized = session.query(Paper).filter(
        func.date(Paper.publish_date) == target_date,
        Paper.category == UNCATEGORIZED_KEY
    ).all()
    
    logger.info(f"找到 {len(uncategorized)} 篇12月16日的未分类论文")
    logger.info("开始重新分类...")
    logger.info("=" * 60)
    
    reclassified = 0
    still_uncategorized = 0
    
    for i, paper in enumerate(uncategorized, 1):
        try:
            # 尝试分类
            new_category = classify_paper_by_keywords(paper)
            
            if new_category != UNCATEGORIZED_KEY:
                # 规范化类别
                normalized_category = normalize_category(new_category)
                paper.category = normalized_category
                paper.updated_at = datetime.now()
                reclassified += 1
                logger.info(f"[{i}/{len(uncategorized)}] ✅ {paper.title[:50]}...")
                logger.info(f"     -> {normalized_category}")
            else:
                still_uncategorized += 1
                logger.info(f"[{i}/{len(uncategorized)}] ⚠️  无法分类: {paper.title[:50]}...")
            
            # 每10篇提交一次
            if i % 10 == 0:
                session.commit()
                logger.info(f"已处理 {i}/{len(uncategorized)} 篇...")
        
        except Exception as e:
            logger.error(f"处理论文失败 {paper.id}: {e}")
            continue
    
    session.commit()
    session.close()
    
    logger.info("=" * 60)
    logger.info(f"重新分类完成！")
    logger.info(f"✅ 成功分类: {reclassified} 篇")
    logger.info(f"⚠️  仍为未分类: {still_uncategorized} 篇")
    
    # 验证结果
    session = get_session()
    final_uncategorized = session.query(func.count(Paper.id)).filter(
        func.date(Paper.publish_date) == target_date,
        Paper.category == UNCATEGORIZED_KEY
    ).scalar()
    session.close()
    
    logger.info(f"📊 最终未分类数量: {final_uncategorized} 篇")

if __name__ == '__main__':
    reclassify_dec16_papers()

