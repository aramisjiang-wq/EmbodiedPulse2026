"""
激进策略重新分类未分类论文
降低匹配门槛，确保所有论文都能分类
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import get_session, Paper
from taxonomy import NEW_TAXONOMY
from datetime import datetime
import re
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%H:%M:%S')

def aggressive_classify(paper):
    """
    激进分类策略：降低门槛，任何部分匹配都计分
    检索词需要在标题或摘要中出现（分别检查）
    """
    title = (paper.title or '').lower()
    abstract = (paper.abstract or '').lower()
    
    # 移除特殊字符
    title = re.sub(r'[^\w\s]', ' ', title)
    abstract = re.sub(r'[^\w\s]', ' ', abstract)
    
    tag_scores = {}
    
    for tag_key, (chinese, english, keywords) in NEW_TAXONOMY.items():
        score = 0
        
        # 1. 检查关键词（分别检查标题和摘要）
        for keyword in keywords:
            kw_lower = keyword.lower()
            title_match = False
            abstract_match = False
            
            # 检查标题
            if title:
                if f' {kw_lower} ' in f' {title} ':
                    title_match = True
                    score += 3
                elif kw_lower in title:
                    title_match = True
                    score += 1
            
            # 检查摘要
            if abstract:
                if f' {kw_lower} ' in f' {abstract} ':
                    abstract_match = True
                score += 3
                elif kw_lower in abstract:
                    abstract_match = True
                score += 1
            
            # 如果标题和摘要都匹配，额外加分
            if title_match and abstract_match:
                score += 2
        
        # 2. 检查英文标签名（分别检查标题和摘要）
        eng_lower = english.lower()
        if title and eng_lower in title:
            score += 2
        if abstract and eng_lower in abstract:
            score += 2
        
        # 3. 检查中文标签名的拼音或常见英文对应
        # （这里可以添加更多映射）
        
        if score > 0:
            tag_scores[tag_key] = score
    
    # 如果有匹配，返回得分最高的标签
    if tag_scores:
        sorted_tags = sorted(tag_scores.items(), key=lambda x: -x[1])
        return sorted_tags[0][0]
    
    # 如果完全没匹配，做最后的兜底分类
    # 检查是否包含robot相关词
    robot_words = ['robot', 'robotic', 'manipulation', 'grasp', 'navigation', 
                   'autonomous', 'agent', 'embodied', 'control']
    
    for word in robot_words:
        if word in text:
            # 根据最频繁的词选择合适的标签
            if 'vision' in text or 'visual' in text or 'image' in text:
                return 'Perception/Vision-Language Model'
            elif 'learn' in text or 'train' in text:
                return 'Learning/Reinforcement Learning'
            elif 'plan' in text or 'navigation' in text:
                return 'Decision/Task Planning'
            elif 'grasp' in text or 'manipulat' in text:
                return 'Operation/Grasp'
            else:
                return 'Operation/Policy'  # 通用操作标签
    
    # 实在没办法，返回未分类
    return 'Uncategorized'


def main():
    session = get_session()
    
    # 获取所有未分类论文
    uncategorized = session.query(Paper).filter(
        Paper.category == 'Uncategorized'
    ).all()
    
    logging.info(f"开始激进重新分类 {len(uncategorized)} 篇未分类论文...")
    logging.info(f"策略：降低匹配门槛，使用兜底分类")
    logging.info("="*60)
    
    updated = 0
    still_uncategorized = 0
    
    for i, paper in enumerate(uncategorized):
        new_category = aggressive_classify(paper)
        
        if new_category != 'Uncategorized':
            paper.category = new_category
            paper.updated_at = datetime.now()
            updated += 1
        else:
            still_uncategorized += 1
        
        if (i + 1) % 500 == 0:
            session.commit()
            logging.info(f"  进度: {i+1}/{len(uncategorized)} | 已更新: {updated} | 仍未分类: {still_uncategorized}")
    
    session.commit()
    
    # 最终统计
    from taxonomy import NEW_TAXONOMY
    from sqlalchemy import func
    
    stats = session.query(Paper.category, func.count(Paper.id)).group_by(
        Paper.category
    ).all()
    stats_dict = dict(stats)
    
    total = sum(stats_dict.values())
    final_unc = stats_dict.get('Uncategorized', 0)
    
    logging.info("\n" + "="*60)
    logging.info("✅ 激进重新分类完成！")
    logging.info(f"  已更新: {updated} 篇")
    logging.info(f"  仍未分类: {final_unc} 篇 ({final_unc*100/total:.1f}%)")
    
    # 统计达标标签
    达标 = sum(1 for tag in NEW_TAXONOMY.keys() 
              if stats_dict.get(tag, 0) >= 100)
    
    logging.info(f"\n📊 达标标签: {达标}/33")
    logging.info("="*60)
    
    session.close()


if __name__ == "__main__":
    main()
