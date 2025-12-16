"""
针对接近100篇的标签（50-99篇）进行精准补充
目标：快速让这些标签达到100篇以上
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
from sqlalchemy import func
import time

logging.basicConfig(
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

# 为接近达标的标签定义精准查询
# 目标：每个标签至少120篇（留有余地）
NEAR_TARGET_QUERIES = [
    # 99篇 - 只差1篇！
    ("Perception/Image Captioning", 120, [
        "ti:image captioning robot",
        "ti:visual captioning embodied",
        "ti:image description robot",
        "ti:visual description generation",
    ]),
    
    # 58篇 - 差42篇
    ("Perception/Point Cloud", 120, [
        "ti:point cloud robot",
        "ti:lidar robot perception",
        "ti:pointnet manipulation",
        "ti:3d point robot",
        "ti:point cloud segmentation robot",
    ]),
    
    ("Motion Control/Motion Retargeting", 120, [
        "ti:motion retargeting",
        "ti:retarget motion robot",
        "ti:human motion robot",
        "ti:motion transfer humanoid",
        "ti:motion mapping",
    ]),
    
    # 56篇 - 差44篇
    ("Perception/Generative Models", 120, [
        "ti:diffusion model robot",
        "ti:generative model manipulation",
        "ti:VAE robot",
        "ti:GAN robot",
        "ti:diffusion robot learning",
    ]),
    
    # 48篇 - 差52篇
    ("Motion Control/Quadruped Robot", 120, [
        "ti:quadruped robot",
        "ti:four-legged robot",
        "ti:quadrupedal locomotion",
        "ti:four-leg robot",
    ]),
    
    ("Decision/Chain of Thought", 120, [
        "ti:chain-of-thought reasoning",
        "ti:CoT robot",
        "ti:step-by-step reasoning robot",
        "ti:reasoning chain embodied",
        "ti:thought process robot",
    ]),
    
    # 44篇 - 差56篇
    ("Operation/Bimanual Manipulation", 120, [
        "ti:bimanual manipulation",
        "ti:dual-arm robot",
        "ti:two-arm manipulation",
        "ti:bi-manual robot",
        "ti:dual arm coordination",
    ]),
]

# 零论文标签 - 更激进的查询
ZERO_TAG_QUERIES = [
    ("Decision/Historical Modeling", 120, [
        "ti:memory robot",
        "ti:episodic memory robot",
        "ti:experience replay robot",
        "ti:temporal robot",
        "ti:recurrent robot learning",
        "ti:LSTM robot",
    ]),
    
    ("Motion Control/Whole-Body Control", 120, [
        "ti:humanoid motion control",
        "ti:humanoid robot control",
        "ti:full-body humanoid",
        "ti:coordination humanoid",
    ]),
    
    ("Operation/Teleoperation", 120, [
        "ti:shared autonomy",
        "ti:haptic robot",
        "ti:VR robot control",
        "ti:virtual reality manipulation",
        "ti:human-in-the-loop robot",
    ]),
]


def fetch_for_tag(tag_key, target_count, queries):
    """为指定标签抓取论文"""
    session = get_session()
    
    current_count = session.query(func.count(Paper.id)).filter(
        Paper.category == tag_key
    ).scalar()
    
    logging.info(f"{'='*70}")
    logging.info(f"📌 标签: {tag_key}")
    logging.info(f"   当前: {current_count}篇 | 目标: {target_count}篇 | 需要: {target_count - current_count}篇")
    logging.info(f"{'='*70}")
    
    if current_count >= target_count:
        logging.info(f"✅ 已达标，跳过")
        session.close()
        return 0
    
    all_papers = {}
    reclassified = 0
    
    for query in queries:
        logging.info(f"\n🔍 查询: {query}")
        
        try:
            search = arxiv.Search(
                query=query,
                max_results=200,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            fetched = 0
            for result in search.results():
                arxiv_id = result.entry_id.split('/abs/')[-1].split('v')[0]
                
                # 检查已存在
                existing = session.query(Paper).filter_by(id=arxiv_id).first()
                
                if existing:
                    # 重新分类未分类论文
                    if existing.category == 'Uncategorized':
                        tags = classify_paper_by_keywords(existing)
                        if tag_key in tags:
                            existing.category = tag_key
                            existing.updated_at = datetime.now()
                            reclassified += 1
                            logging.info(f"   ✓ 重新分类: {arxiv_id}")
                else:
                    if arxiv_id not in all_papers:
                        all_papers[arxiv_id] = result
                        fetched += 1
                
                if fetched >= 50:
                    break
            
            logging.info(f"   找到: {fetched}篇新论文")
            
            # 检查是否已达标
            current = session.query(func.count(Paper.id)).filter(
                Paper.category == tag_key
            ).scalar()
            if current >= target_count:
                logging.info(f"✅ 已达到目标 {target_count}篇，停止抓取")
                session.commit()
                session.close()
                return reclassified
            
            time.sleep(3)
            
        except Exception as e:
            logging.error(f"   ❌ 查询失败: {e}")
            continue
    
    logging.info(f"\n📦 新论文总数: {len(all_papers)}篇")
    
    # 保存新论文
    saved_count = 0
    for arxiv_id, result in all_papers.items():
        try:
            temp_paper = Paper(
                id=arxiv_id,
                title=result.title,
                abstract=result.summary,
                publish_date=result.published.date()
            )
            
            tags = classify_paper_by_keywords(temp_paper)
            category = tags[0] if tags else 'Uncategorized'
            
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
                saved_count += 1
            
            if saved_count % 50 == 0 and saved_count > 0:
                session.commit()
                
        except Exception as e:
            logging.error(f"   ❌ 保存失败 {arxiv_id}: {e}")
            continue
    
    session.commit()
    
    # 最终统计
    final_count = session.query(func.count(Paper.id)).filter(
        Paper.category == tag_key
    ).scalar()
    
    total_added = reclassified + saved_count
    status = "✅" if final_count >= 100 else "⚠️"
    
    logging.info(f"\n{'='*70}")
    logging.info(f"{status} 完成: {tag_key}")
    logging.info(f"   最终: {final_count}篇 (新增: {total_added}篇)")
    logging.info(f"   - 重新分类: {reclassified}篇")
    logging.info(f"   - 新抓取分类到此: {saved_count}篇")
    logging.info(f"{'='*70}\n")
    
    session.close()
    return total_added


def main():
    """主函数"""
    logging.info("="*70)
    logging.info("🚀 方案1: 快速达到25个标签达标")
    logging.info("="*70)
    logging.info("第一步: 处理7个接近达标的标签 (50-99篇)")
    logging.info("第二步: 处理3个零论文标签")
    logging.info("="*70 + "\n")
    
    total_added = 0
    
    # 第一步：接近达标的标签
    logging.info("\n" + "="*70)
    logging.info("📊 第一步: 补充接近达标的标签")
    logging.info("="*70)
    
    for tag_key, target, queries in NEAR_TARGET_QUERIES:
        added = fetch_for_tag(tag_key, target, queries)
        total_added += added
        time.sleep(5)
    
    # 第二步：零论文标签
    logging.info("\n" + "="*70)
    logging.info("📊 第二步: 补充零论文标签")
    logging.info("="*70)
    
    for tag_key, target, queries in ZERO_TAG_QUERIES:
        added = fetch_for_tag(tag_key, target, queries)
        total_added += added
        time.sleep(5)
    
    # 最终统计
    logging.info("\n" + "="*70)
    logging.info("✅ 补充完成！")
    logging.info(f"   总共新增: {total_added}篇论文")
    logging.info("="*70)
    
    # 统计达标情况
    from taxonomy import NEW_TAXONOMY
    session = get_session()
    stats = session.query(Paper.category, func.count(Paper.id)).group_by(
        Paper.category
    ).all()
    stats_dict = dict(stats)
    
    达标数 = sum(1 for tag_key in NEW_TAXONOMY.keys() 
                if stats_dict.get(tag_key, 0) >= 100)
    
    logging.info(f"\n📈 当前达标标签数: {达标数}/33")
    logging.info("="*70)
    
    session.close()


if __name__ == "__main__":
    main()
