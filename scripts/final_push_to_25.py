"""
最后冲刺：让达标标签从19个增加到25个
专注于最接近100篇的6个标签
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import arxiv
import logging
from datetime import datetime
from models import get_session, Paper
from scripts.reclassify_all_papers import classify_paper_by_keywords
from sqlalchemy import func
import time

logging.basicConfig(
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

# 最接近100篇的标签 - 优先级最高
FINAL_PUSH_QUERIES = [
    # 点云表示: 75篇 (差25篇)
    ("Perception/Point Cloud", 110, [
        "ti:point cloud robot",
        "ti:lidar robot",
        "ti:pointnet robot",
        "ti:3d point manipulation",
    ]),
    
    # 遥操作: 64篇 (差36篇)
    ("Operation/Teleoperation", 110, [
        "ti:teleoperation",
        "ti:shared autonomy robot",
        "ti:haptic manipulation",
        "ti:virtual reality robot",
    ]),
    
    # 生成模型: 61篇 (差39篇)
    ("Perception/Generative Models", 110, [
        "ti:diffusion robot",
        "ti:VAE robot",
        "ti:generative model robot",
    ]),
    
    # 思维链: 54篇 (差46篇)
    ("Decision/Chain of Thought", 110, [
        "ti:chain-of-thought",
        "ti:reasoning robot",
        "ti:step-by-step reasoning",
    ]),
    
    # 四足机器人: 49篇 (差51篇)
    ("Motion Control/Quadruped Robot", 110, [
        "ti:quadruped",
        "ti:four-legged robot",
    ]),
    
    # 双手操作: 49篇 (差51篇)
    ("Operation/Bimanual Manipulation", 110, [
        "ti:bimanual",
        "ti:dual-arm manipulation",
        "ti:two-arm robot",
    ]),
]


def quick_fetch(tag_key, target, queries):
    """快速抓取 - 只从未分类论文中重新分类"""
    session = get_session()
    
    current = session.query(func.count(Paper.id)).filter(
        Paper.category == tag_key
    ).scalar()
    
    logging.info(f"{'='*60}")
    logging.info(f"{tag_key}: {current}篇 -> 目标{target}篇")
    
    if current >= target:
        logging.info(f"✅ 已达标")
        session.close()
        return 0
    
    # 从未分类中重新分类
    uncategorized = session.query(Paper).filter(
        Paper.category == 'Uncategorized'
    ).limit(2000).all()
    
    reclassified = 0
    for paper in uncategorized:
        tags = classify_paper_by_keywords(paper)
        if tag_key in tags:
            paper.category = tag_key
            paper.updated_at = datetime.now()
            reclassified += 1
            
            if reclassified % 10 == 0:
                session.commit()
                current_new = session.query(func.count(Paper.id)).filter(
                    Paper.category == tag_key
                ).scalar()
                if current_new >= target:
                    break
    
    session.commit()
    
    final = session.query(func.count(Paper.id)).filter(
        Paper.category == tag_key
    ).scalar()
    
    status = "✅" if final >= 100 else "⚠️"
    logging.info(f"{status} 完成: {final}篇 (新增{final-current}篇)")
    logging.info(f"{'='*60}\n")
    
    session.close()
    return final - current


def main():
    logging.info("="*60)
    logging.info("🚀 最后冲刺：19个 -> 25个达标标签！")
    logging.info("="*60 + "\n")
    
    total_added = 0
    
    for tag_key, target, queries in FINAL_PUSH_QUERIES:
        added = quick_fetch(tag_key, target, queries)
        total_added += added
    
    # 最终统计
    from taxonomy import NEW_TAXONOMY
    session = get_session()
    stats = session.query(Paper.category, func.count(Paper.id)).group_by(
        Paper.category
    ).all()
    stats_dict = dict(stats)
    
    达标数 = sum(1 for tag_key in NEW_TAXONOMY.keys() 
                if stats_dict.get(tag_key, 0) >= 100)
    
    logging.info("\n" + "="*60)
    logging.info(f"✅ 冲刺完成！")
    logging.info(f"   新增: {total_added}篇")
    logging.info(f"   达标标签: {达标数}/33")
    
    if 达标数 >= 25:
        logging.info(f"🎉 目标达成！")
    else:
        logging.info(f"   还差: {25-达标数}个")
    logging.info("="*60)
    
    session.close()


if __name__ == "__main__":
    main()
