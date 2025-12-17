#!/usr/bin/env python3
"""
专门抓取12月16日的论文（手动抓取）
"""
import sys
import os
from datetime import datetime, date
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import arxiv
from models import get_session, Paper
# 临时禁用reclassify导入，避免语法错误
import sys
original_path = sys.path.copy()
try:
    from save_paper_to_db import save_paper_to_db
except IndentationError:
    # 如果导入失败，直接定义简化版的保存函数
    def save_paper_to_db(paper_data, category, enable_title_dedup=True, fetch_semantic_scholar=False):
        from models import get_session, Paper
        from datetime import datetime
        session = get_session()
        try:
            paper_id = paper_data.get('id')
            if not paper_id:
                return False, 'error'
            
            # 检查是否已存在
            existing = session.query(Paper).filter_by(id=paper_id).first()
            if existing:
                return True, 'skipped'
            
            # 创建新记录
            paper = Paper(
                id=paper_id,
                title=paper_data.get('title', ''),
                authors=paper_data.get('authors', ''),
                abstract=paper_data.get('abstract', ''),
                pdf_url=paper_data.get('pdf_url', ''),
                code_url=paper_data.get('code_url'),
                category=category,
                publish_date=paper_data.get('publish_date'),
                update_date=paper_data.get('update_date')
            )
            session.add(paper)
            session.commit()
            return True, 'created'
        except Exception as e:
            session.rollback()
            print(f"保存失败: {e}")
            return False, 'error'
        finally:
            session.close()
from taxonomy import normalize_category
from sqlalchemy import func

def fetch_and_save_dec16_papers():
    """抓取并保存12月16日首次发布的论文"""
    print("=" * 60)
    print("开始抓取12月16日首次发布的论文...")
    print("=" * 60)
    
    target_date = date(2025, 12, 16)
    start_date_str = target_date.strftime('%Y%m%d')
    end_date_str = target_date.strftime('%Y%m%d')
    
    # 查询12月16日首次发布的所有论文
    query = f'submittedDate:[{start_date_str}0000 TO {end_date_str}2359]'
    
    print(f"查询: {query}")
    print(f"目标日期: {target_date}")
    print()
    
    client = arxiv.Client(
        page_size=100,
        delay_seconds=1.5,
        num_retries=3
    )
    
    search = arxiv.Search(
        query=query,
        max_results=200,  # 12月16日大约有50-100篇论文
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    
    session = get_session()
    saved_count = 0
    skipped_count = 0
    error_count = 0
    
    print("开始抓取论文...")
    print()
    
    try:
        results = list(client.results(search))
        print(f"从ArXiv API获取到 {len(results)} 篇论文")
        print()
        
        for i, result in enumerate(results, 1):
            try:
                paper_id = result.get_short_id()
                published_date = result.published.date()
                updated_date = result.updated.date()
                
                # 只处理12月16日首次发布的论文
                if published_date != target_date:
                    continue
                
                # 检查是否已存在
                existing = session.query(Paper).filter_by(id=paper_id).first()
                if existing:
                    print(f"[{i}/{len(results)}] 跳过已存在: {paper_id} - {result.title[:50]}...")
                    skipped_count += 1
                    continue
                
                # 构建论文数据
                paper_data = {
                    'id': paper_id,
                    'title': result.title,
                    'authors': ', '.join([author.name for author in result.authors]),
                    'abstract': result.summary.replace('\n', ' '),
                    'pdf_url': result.pdf_url,
                    'code_url': None,  # 稍后可以从comments中提取
                    'date': published_date.strftime('%Y-%m-%d'),
                    'publish_date': published_date,
                    'update_date': updated_date
                }
                
                # 尝试从comments中提取代码链接
                if result.comment:
                    import re
                    urls = re.findall(r'(https?://[^\s,;]+)', result.comment)
                    if urls:
                        paper_data['code_url'] = urls[0]
                
                # 尝试自动分类（基于标题和摘要）
                category = 'Uncategorized'
                title_lower = result.title.lower()
                abstract_lower = result.summary.lower()
                text = title_lower + ' ' + abstract_lower
                
                # 简单的关键词匹配分类
                if any(kw in text for kw in ['perception', 'vision', 'visual', 'image', '2d', '3d']):
                    if '3d' in text or 'depth' in text or 'point cloud' in text:
                        category = 'Perception/3D Perception'
                    else:
                        category = 'Perception/2D Perception'
                elif any(kw in text for kw in ['robot', 'robotic', 'robotics']):
                    if any(kw in text for kw in ['humanoid', 'bipedal']):
                        category = 'Motion/Humanoid'
                    elif any(kw in text for kw in ['quadruped', 'legged']):
                        category = 'Motion/Quadruped'
                    elif any(kw in text for kw in ['manipulation', 'grasp', 'grasping']):
                        category = 'Operation/Grasp'
                    else:
                        category = 'General-Robot'
                elif any(kw in text for kw in ['vla', 'vision language action', 'embodied agent']):
                    category = 'Operation/VLA'
                elif any(kw in text for kw in ['reinforcement learning', 'rl', 'ppo', 'sac']):
                    category = 'Learning/RL'
                elif any(kw in text for kw in ['planning', 'navigation', 'path']):
                    category = 'Decision/Planning'
                
                # 规范化类别
                category = normalize_category(category)
                
                paper_data['category'] = category
                
                # 保存到数据库
                success, action = save_paper_to_db(
                    paper_data,
                    category,
                    enable_title_dedup=True,
                    fetch_semantic_scholar=False  # 暂时不获取Semantic Scholar数据，加快速度
                )
                
                if success:
                    if action == 'created':
                        saved_count += 1
                        print(f"[{i}/{len(results)}] ✅ 新增: {paper_id} - {result.title[:50]}...")
                        print(f"     类别: {category}, 发布日期: {published_date}")
                    else:
                        skipped_count += 1
                        print(f"[{i}/{len(results)}] ⏭️  更新: {paper_id} - {result.title[:50]}...")
                else:
                    error_count += 1
                    print(f"[{i}/{len(results)}] ❌ 保存失败: {paper_id} - {result.title[:50]}...")
                
            except Exception as e:
                error_count += 1
                print(f"[{i}/{len(results)}] ❌ 处理失败: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        session.commit()
        
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
    
    print()
    print("=" * 60)
    print("抓取完成！")
    print("=" * 60)
    print(f"✅ 新增: {saved_count} 篇")
    print(f"⏭️  跳过: {skipped_count} 篇")
    print(f"❌ 错误: {error_count} 篇")
    print()
    
    # 验证结果
    session = get_session()
    dec16_count = session.query(func.count(Paper.id)).filter(
        func.date(Paper.publish_date) == target_date
    ).scalar()
    session.close()
    
    print(f"📊 数据库中12月16日的论文总数: {dec16_count} 篇")
    
    if dec16_count > 0:
        print("✅ 成功抓取到12月16日的论文！")
    else:
        print("⚠️  数据库中仍然没有12月16日的论文")

if __name__ == '__main__':
    fetch_and_save_dec16_papers()

