"""
针对不足100篇的标签，精准补充论文
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import arxiv
import logging
from datetime import datetime
from models import get_session, Paper
from taxonomy import normalize_category
from scripts.reclassify_all_papers import classify_paper_by_keywords
import time

logging.basicConfig(
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

# 为每个不足100篇的标签定义精准查询
# 格式: (标签key, 目标论文数, 查询列表)
TARGETED_QUERIES = [
    # 0篇标签 - 优先级最高
    ("Operation/Teleoperation", 150, [
        "ti:teleoperation robot",
        "ti:remote robot operation",
        "ti:telerobotics",
        "ti:human-robot interaction manipulation",
        "ti:remote control robot",
    ]),
    ("Motion Control/Whole-Body Control", 150, [
        "ti:whole-body control humanoid",
        "ti:full-body motion robot",
        "ti:coordinated control robot",
        "ti:whole body motion planning",
    ]),
    ("Decision/Historical Modeling", 150, [
        "ti:memory robot learning",
        "ti:temporal modeling robot",
        "ti:episodic memory agent",
        "ti:history robot navigation",
        "ti:experience replay robot",
    ]),
    
    # <50篇标签
    ("Perception/3D Perception", 150, [
        "ti:3d perception robot",
        "ti:depth estimation robot",
        "ti:rgb-d robot",
        "ti:stereo vision robot",
        "ti:3d sensing manipulation",
    ]),
    ("Perception/Voxel Representation", 150, [
        "ti:voxel robot",
        "ti:volumetric representation robot",
        "ti:occupancy grid robot",
        "ti:3d voxel planning",
    ]),
    ("Perception/3D Scene Understanding", 150, [
        "ti:3d scene understanding robot",
        "ti:scene reconstruction robot",
        "ti:gaussian splatting robot",
        "ti:nerf robot",
        "ti:world model robot",
        "ti:spatial understanding embodied",
    ]),
    ("Perception/Affordance Generation", 150, [
        "ti:affordance robot",
        "ti:affordance detection manipulation",
        "ti:affordance learning",
    ]),
    ("Perception/Semantic Understanding", 150, [
        "ti:semantic understanding robot",
        "ti:semantic perception robot",
        "ti:semantic robot navigation",
    ]),
    ("Perception/Generative Models", 150, [
        "ti:generative model robot",
        "ti:diffusion robot",
        "ti:VAE robot manipulation",
        "ti:GAN robot",
    ]),
    ("Decision/Chain of Thought", 150, [
        "ti:chain-of-thought robot",
        "ti:reasoning robot planning",
        "ti:step-by-step robot",
    ]),
    ("Motion Control/Motion Retargeting", 150, [
        "ti:motion retargeting",
        "ti:retarget human motion robot",
        "ti:motion transfer robot",
    ]),
    ("Motion Control/Quadruped Robot", 150, [
        "ti:quadruped robot",
        "ti:four-legged robot",
        "ti:quadrupedal locomotion",
    ]),
    ("Motion Control/Mobile Manipulation", 150, [
        "ti:mobile manipulation",
        "ti:mobile robot manipulation",
        "ti:mobile manipulator",
    ]),
    ("Operation/Bimanual Manipulation", 150, [
        "ti:bimanual manipulation",
        "ti:dual-arm robot",
        "ti:two-arm manipulation",
    ]),
    
    # 50-99篇标签
    ("Perception/Image Captioning", 150, [
        "ti:image captioning robot",
        "ti:visual description generation",
        "ti:image caption embodied",
    ]),
    ("Perception/Point Cloud", 150, [
        "ti:point cloud robot",
        "ti:lidar robot",
        "ti:pointnet robot manipulation",
    ]),
    ("Motion Control/Locomotion Control", 150, [
        "ti:locomotion robot",
        "ti:bipedal robot",
        "ti:legged robot control",
    ]),
    ("Operation/Grasp", 200, [  # 需要200篇
        "ti:grasp robot",
        "ti:grasping manipulation",
        "ti:robotic grasp",
        "ti:6-dof grasp",
        "ti:grasp planning",
    ]),
    ("Learning/Lightweight Model", 150, [
        "ti:efficient robot",
        "ti:lightweight model robot",
        "ti:model compression robot",
        "ti:mobile robot efficient",
    ]),
]


def fetch_and_classify_for_tag(tag_key, target_count, queries):
    """
    为特定标签抓取并分类论文
    """
    session = get_session()
    
    # 检查当前数量
    from sqlalchemy import func
    current_count = session.query(func.count(Paper.id)).filter(Paper.category == tag_key).scalar()
    
    logging.info(f"{'='*60}")
    logging.info(f"标签: {tag_key}")
    logging.info(f"当前: {current_count}篇 | 目标: {target_count}篇")
    
    if current_count >= target_count:
        logging.info(f"✅ 已达到目标，跳过")
        session.close()
        return 0
    
    need_count = target_count - current_count
    logging.info(f"需要: {need_count}篇")
    logging.info(f"{'='*60}")
    
    all_papers = {}
    new_classified = 0
    
    for query in queries:
        logging.info(f"\n查询: {query}")
        
        try:
            search = arxiv.Search(
                query=query,
                max_results=300,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            fetched = 0
            for result in search.results():
                arxiv_id = result.entry_id.split('/abs/')[-1].split('v')[0]
                
                # 检查是否已存在
                existing = session.query(Paper).filter_by(id=arxiv_id).first()
                
                if existing:
                    # 如果未分类，重新分类
                    if existing.category == 'Uncategorized':
                        tags = classify_paper_by_keywords(existing)
                        if tag_key in tags:
                            existing.category = tag_key
                            new_classified += 1
                            logging.info(f"  重新分类: {arxiv_id} -> {tag_key}")
                else:
                    # 新论文
                    if arxiv_id not in all_papers:
                        all_papers[arxiv_id] = result
                        fetched += 1
                
                if fetched >= 50:  # 每个查询最多50篇新论文
                    break
            
            logging.info(f"  找到: {fetched}篇新论文")
            time.sleep(3)  # API限流
            
        except Exception as e:
            logging.error(f"  查询失败: {e}")
            continue
    
    logging.info(f"\n总共找到 {len(all_papers)} 篇新论文")
    
    # 保存新论文
    saved_to_tag = 0
    for arxiv_id, result in all_papers.items():
        try:
            # 创建临时Paper对象用于分类
            temp_paper = Paper(
                id=arxiv_id,
                title=result.title,
                abstract=result.summary,
                publish_date=result.published.date()
            )
            
            # 分类
            tags = classify_paper_by_keywords(temp_paper)
            category = tags[0] if tags else 'Uncategorized'
            
            # 保存
            paper = Paper(
                id=arxiv_id,
                title=result.title,
                authors=', '.join([author.name for author in result.authors]),
                abstract=result.summary,
                publish_date=result.published.date(),
                pdf_url=result.pdf_url,
                category=category,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(paper)
            
            if category == tag_key:
                saved_to_tag += 1
            
            # 每50条提交一次
            if (saved_to_tag + new_classified) % 50 == 0:
                session.commit()
                
        except Exception as e:
            logging.error(f"  保存失败 {arxiv_id}: {e}")
            continue
    
    session.commit()
    
    # 最终统计
    final_count = session.query(func.count(Paper.id)).filter(Paper.category == tag_key).scalar()
    total_added = new_classified + saved_to_tag
    
    logging.info(f"\n{'='*60}")
    logging.info(f"✅ 完成: {tag_key}")
    logging.info(f"  最终: {final_count}篇 (新增: {total_added}篇)")
    logging.info(f"  - 重新分类: {new_classified}篇")
    logging.info(f"  - 新抓取: {saved_to_tag}篇")
    logging.info(f"{'='*60}\n")
    
    session.close()
    return total_added


def main():
    """
    主函数
    """
    logging.info("="*60)
    logging.info("开始补充不足100篇的标签")
    logging.info("="*60)
    
    total_added = 0
    
    for tag_key, target_count, queries in TARGETED_QUERIES:
        added = fetch_and_classify_for_tag(tag_key, target_count, queries)
        total_added += added
        time.sleep(5)  # 标签之间间隔
    
    logging.info("\n" + "="*60)
    logging.info(f"✅ 全部完成！共补充 {total_added} 篇论文")
    logging.info("="*60)


if __name__ == "__main__":
    main()
