#!/usr/bin/env python3
"""
抓取指定日期范围的论文（12月6-8日）
"""
import arxiv
import re
import logging
from datetime import date, datetime
from models import get_session, Paper
from daily_arxiv import load_config, get_authors
from save_paper_to_db import save_paper_to_db

logging.basicConfig(format='[%(asctime)s %(levelname)s] %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)

arxiv_url = "http://arxiv.org/"

def fetch_papers_by_date_range(start_date, end_date, keywords):
    """
    抓取指定日期范围内的论文
    
    Args:
        start_date: 开始日期 (date对象)
        end_date: 结束日期 (date对象)
        keywords: 关键词字典 {category: query}
    """
    client = arxiv.Client(
        page_size=100,
        delay_seconds=1.0,
        num_retries=3
    )
    
    total_saved = 0
    total_skipped = 0
    
    for category, query in keywords.items():
        logging.info(f"\n{'='*60}")
        logging.info(f"抓取类别: {category}")
        logging.info(f"查询: {query}")
        logging.info(f"日期范围: {start_date} 至 {end_date}")
        logging.info(f"{'='*60}")
        
        try:
            # 搜索论文（扩大范围，然后过滤日期）
            search = arxiv.Search(
                query=query,
                max_results=500,  # 扩大范围以确保覆盖
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            category_saved = 0
            category_skipped = 0
            
            for result in client.results(search):
                paper_date = result.published.date()
                
                # 只处理目标日期范围内的论文
                if paper_date < start_date:
                    # 如果日期早于开始日期，可以提前结束（因为是倒序）
                    break
                
                if paper_date > end_date:
                    # 如果日期晚于结束日期，跳过
                    continue
                
                try:
                    paper_id = result.get_short_id()
                    ver_pos = paper_id.find('v')
                    if ver_pos == -1:
                        paper_key = paper_id
                    else:
                        paper_key = paper_id[0:ver_pos]
                    
                    # 检查是否已存在
                    session = get_session()
                    existing = session.query(Paper).filter_by(id=paper_key).first()
                    session.close()
                    
                    if existing:
                        logging.debug(f"  跳过已存在: {paper_key}")
                        category_skipped += 1
                        continue
                    
                    # 提取代码链接
                    repo_url = None
                    comments = result.comment
                    if comments:
                        urls = re.findall(r'(https?://[^\s,;]+)', comments)
                        if urls:
                            repo_url = urls[0]
                    
                    # 构建论文数据
                    paper_data = {
                        'id': paper_key,
                        'title': result.title,
                        'authors': get_authors(result.authors),
                        'date': paper_date.strftime('%Y-%m-%d'),
                        'pdf_url': arxiv_url + 'abs/' + paper_key,
                        'code_url': repo_url
                    }
                    
                    # 保存到数据库
                    success, action = save_paper_to_db(paper_data, category, enable_title_dedup=True)
                    if success:
                        category_saved += 1
                        logging.info(f"  ✓ {paper_date} - {paper_key}: {result.title[:60]}...")
                    else:
                        category_skipped += 1
                        logging.debug(f"  ✗ 跳过: {paper_key}")
                
                except Exception as e:
                    logging.warning(f"  处理论文失败: {e}")
                    continue
            
            total_saved += category_saved
            total_skipped += category_skipped
            logging.info(f"{category}: 保存{category_saved}篇, 跳过{category_skipped}篇")
        
        except Exception as e:
            logging.error(f"{category} 抓取失败: {e}")
            continue
    
    return total_saved, total_skipped

def main():
    """主函数"""
    print("=" * 60)
    print("抓取指定日期范围的论文（12月6-8日）")
    print("=" * 60)
    
    # 加载配置
    config = load_config('config.yaml')
    keywords = config.get('kv', {})
    
    # 目标日期范围
    start_date = date(2025, 12, 6)
    end_date = date(2025, 12, 8)
    
    print(f"\n日期范围: {start_date} 至 {end_date}")
    print(f"类别数量: {len(keywords)}")
    print(f"\n开始抓取...")
    print("=" * 60)
    
    # 抓取论文
    saved, skipped = fetch_papers_by_date_range(start_date, end_date, keywords)
    
    # 显示结果
    print("\n" + "=" * 60)
    print("抓取完成！")
    print("=" * 60)
    print(f"保存: {saved}篇")
    print(f"跳过: {skipped}篇（已存在或重复）")
    
    # 验证结果
    print("\n验证数据库中的论文...")
    session = get_session()
    for d in [date(2025, 12, 6), date(2025, 12, 7), date(2025, 12, 8)]:
        count = session.query(Paper).filter(Paper.publish_date == d).count()
        print(f"  {d}: {count}篇")
    session.close()

if __name__ == '__main__':
    main()


