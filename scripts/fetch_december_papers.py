"""
抓取12月所有论文的脚本
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import arxiv
import logging
from datetime import datetime, timedelta
from models import get_session, Paper
from taxonomy import normalize_category
import time

logging.basicConfig(
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

# 所有检索词（基于config.yaml）
# 修改为同时搜索标题和摘要：(ti:keyword OR abs:keyword)
SEARCH_QUERIES = [
    # 感知
    "(ti:perception OR abs:perception) OR (ti:detection OR abs:detection) OR (ti:segmentation OR abs:segmentation) OR (ti:vision OR abs:vision) OR (ti:visual OR abs:visual)",
    "(ti:3d OR abs:3d) OR (ti:point cloud OR abs:point cloud) OR (ti:scene understanding OR abs:scene understanding) OR (ti:nerf OR abs:nerf) OR (ti:gaussian splatting OR abs:gaussian splatting)",
    "(ti:VLM OR abs:VLM) OR (ti:vision language OR abs:vision language) OR (ti:multimodal OR abs:multimodal) OR (ti:CLIP OR abs:CLIP) OR (ti:visual grounding OR abs:visual grounding)",
    "(ti:generation OR abs:generation) OR (ti:diffusion OR abs:diffusion) OR (ti:GAN OR abs:GAN) OR (ti:image synthesis OR abs:image synthesis)",
    
    # 决策
    "(ti:planning OR abs:planning) OR (ti:task planning OR abs:task planning) OR (ti:navigation OR abs:navigation) OR (ti:reasoning OR abs:reasoning)",
    "(ti:graph OR abs:graph) OR (ti:memory OR abs:memory) OR (ti:chain of thought OR abs:chain of thought)",
    
    # 运动
    "(ti:locomotion OR abs:locomotion) OR (ti:humanoid OR abs:humanoid) OR (ti:quadruped OR abs:quadruped) OR (ti:bipedal OR abs:bipedal) OR (ti:legged robot OR abs:legged robot)",
    "(ti:whole body OR abs:whole body) OR (ti:mobile manipulation OR abs:mobile manipulation) OR (ti:retargeting OR abs:retargeting)",
    
    # 操作
    "(ti:manipulation OR abs:manipulation) OR (ti:grasp OR abs:grasp) OR (ti:grasping OR abs:grasping) OR (ti:pick and place OR abs:pick and place)",
    "(ti:teleoperation OR abs:teleoperation) OR (ti:bimanual OR abs:bimanual) OR (ti:dexterous OR abs:dexterous) OR (ti:hand manipulation OR abs:hand manipulation)",
    "(ti:VLA OR abs:VLA) OR (ti:vision language action OR abs:vision language action) OR (ti:embodied agent OR abs:embodied agent)",
    "(ti:policy OR abs:policy) OR (ti:visuomotor OR abs:visuomotor) OR (ti:control OR abs:control)",
    
    # 学习
    "(ti:reinforcement learning OR abs:reinforcement learning) OR (ti:RL OR abs:RL) OR (ti:imitation learning OR abs:imitation learning) OR (ti:IL OR abs:IL)",
    "(ti:learning from demonstration OR abs:learning from demonstration) OR (ti:behavior cloning OR abs:behavior cloning)",
    
    # 基准
    "(ti:embodied benchmark OR abs:embodied benchmark)",
    
    # 通用机器人关键词
    "(ti:robot OR abs:robot) OR (ti:robotic OR abs:robotic) OR (ti:robotics OR abs:robotics)",
    "(ti:embodied OR abs:embodied) OR (ti:autonomous agent OR abs:autonomous agent) OR (ti:physical robot OR abs:physical robot)",
]

def fetch_papers_for_date_range(start_date, end_date, search_query):
    """
    抓取指定日期范围和查询条件的论文
    """
    # 构建完整查询
    date_filter = f"submittedDate:[{start_date.strftime('%Y%m%d')}0000 TO {end_date.strftime('%Y%m%d')}2359]"
    full_query = f"({search_query}) AND {date_filter}"
    
    logging.info(f"查询: {full_query[:100]}...")
    
    try:
        search = arxiv.Search(
            query=full_query,
            max_results=500,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        papers = []
        for result in search.results():
            papers.append(result)
            
        logging.info(f"  找到 {len(papers)} 篇论文")
        return papers
        
    except Exception as e:
        logging.error(f"  查询失败: {e}")
        return []


def save_papers_to_db(arxiv_papers):
    """
    保存论文到数据库
    """
    session = get_session()
    new_count = 0
    updated_count = 0
    
    for result in arxiv_papers:
        try:
            arxiv_id = result.entry_id.split('/abs/')[-1].split('v')[0]
            
            # 检查是否已存在
            existing = session.query(Paper).filter_by(id=arxiv_id).first()
            
            if existing:
                # 更新
                existing.title = result.title
                existing.authors = ', '.join([author.name for author in result.authors])
                existing.abstract = result.summary
                existing.publish_date = result.published.date()
                existing.pdf_url = result.pdf_url
                existing.updated_at = datetime.now()
                updated_count += 1
            else:
                # 新增
                paper = Paper(
                    id=arxiv_id,
                    title=result.title,
                    authors=', '.join([author.name for author in result.authors]),
                    abstract=result.summary,
                    publish_date=result.published.date(),
                    pdf_url=result.pdf_url,
                    category='Uncategorized',  # 初始为未分类
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(paper)
                new_count += 1
                
            # 每100条提交一次
            if (new_count + updated_count) % 100 == 0:
                session.commit()
                logging.info(f"  已处理 {new_count + updated_count} 篇论文")
                
        except Exception as e:
            logging.error(f"  保存论文失败 {arxiv_id}: {e}")
            continue
    
    session.commit()
    session.close()
    
    return new_count, updated_count


def main():
    """
    主函数：抓取12月所有论文
    """
    logging.info("="*60)
    logging.info("开始抓取12月论文")
    logging.info("="*60)
    
    # 日期范围：2024-12-01 到 2024-12-15
    start_date = datetime(2024, 12, 1)
    end_date = datetime(2024, 12, 15)
    
    all_papers = {}  # 使用dict去重
    
    for query in SEARCH_QUERIES:
        logging.info(f"\n执行查询: {query[:60]}...")
        
        papers = fetch_papers_for_date_range(start_date, end_date, query)
        
        # 去重
        for paper in papers:
            arxiv_id = paper.entry_id.split('/abs/')[-1].split('v')[0]
            all_papers[arxiv_id] = paper
        
        # API限流
        time.sleep(3)
    
    logging.info(f"\n总共找到 {len(all_papers)} 篇唯一论文")
    
    # 保存到数据库
    logging.info("\n开始保存到数据库...")
    new_count, updated_count = save_papers_to_db(list(all_papers.values()))
    
    logging.info("="*60)
    logging.info(f"✅ 完成!")
    logging.info(f"  新增: {new_count} 篇")
    logging.info(f"  更新: {updated_count} 篇")
    logging.info("="*60)


if __name__ == "__main__":
    main()
