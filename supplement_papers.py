#!/usr/bin/env python3
"""
补充论文脚本：将所有标签的论文数量补充到至少100篇
"""
import yaml
import logging
import arxiv
import re
from models import get_session, Paper
from sqlalchemy import func
from daily_arxiv import load_config, get_authors
from save_paper_to_db import save_paper_to_db

logging.basicConfig(format='[%(asctime)s %(levelname)s] %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)

MIN_PAPERS = 100  # 每个标签最少论文数
arxiv_url = "http://arxiv.org/"

def get_category_counts():
    """获取各标签的论文数量"""
    session = get_session()
    stats_query = session.query(
        Paper.category,
        func.count(Paper.id).label('count')
    ).group_by(Paper.category).all()
    
    counts = {category: count for category, count in stats_query}
    session.close()
    return counts

def fetch_and_save_papers(category, keyword, fetch_count):
    """抓取并保存论文到数据库"""
    saved_count = 0
    
    try:
        # 使用 ArXiv Client API
        client = arxiv.Client(
            page_size=100,
            delay_seconds=2.0,  # 减少延迟以加快速度
            num_retries=3
        )
        
        # 按提交日期倒序排序（优先最新，但也允许历史论文）
        # 增加抓取数量以确保有足够的新论文
        actual_fetch_count = min(fetch_count * 2, 500)  # 抓取更多以确保有足够新论文
        search = arxiv.Search(
            query=keyword,
            max_results=actual_fetch_count,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        results = client.results(search)
        for result in results:
            try:
                paper_id = result.get_short_id()
                # 提取版本号前的ID
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
                    # 如果已存在但类别不同，更新类别并计数
                    if existing.category != category:
                        session = get_session()
                        existing.category = category
                        session.commit()
                        session.close()
                        saved_count += 1
                        logging.info(f"  更新论文类别: {paper_key} -> {category}")
                    # 如果类别相同，跳过
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
                    'date': result.published.date().strftime('%Y-%m-%d'),
                    'pdf_url': arxiv_url + 'abs/' + paper_key,
                    'code_url': repo_url
                }
                
                # 保存到数据库
                if save_paper_to_db(paper_data, category):
                    saved_count += 1
                    logging.info(f"  ✓ 保存: {paper_key} - {result.title[:50]}...")
                
            except Exception as e:
                logging.warning(f"  处理论文失败: {e}")
                continue
        
        return saved_count
        
    except Exception as e:
        logging.error(f"抓取论文失败: {e}")
        return saved_count

def supplement_category(category, keyword, current_count, target_count):
    """为指定标签补充论文"""
    shortage = target_count - current_count
    if shortage <= 0:
        logging.info(f"{category}: 已有{current_count}篇，无需补充")
        return 0
    
    # 循环抓取直到达到目标数量
    total_saved = 0
    max_iterations = 5  # 最多尝试5次
    iteration = 0
    
    while current_count < target_count and iteration < max_iterations:
        iteration += 1
        # 计算需要抓取的数量（多抓取一些，因为可能有重复）
        remaining_shortage = target_count - current_count
        fetch_count = max(remaining_shortage * 2, 100)  # 至少抓取100篇，或短缺数的2倍
        
        logging.info(f"{category}: 第{iteration}轮 - 当前{current_count}篇，还需{remaining_shortage}篇，将抓取{fetch_count}篇")
        
        saved_count = fetch_and_save_papers(category, keyword, fetch_count)
        total_saved += saved_count
        
        # 更新当前数量
        session = get_session()
        current_count = session.query(func.count(Paper.id)).filter(Paper.category == category).scalar()
        session.close()
        
        logging.info(f"{category}: 本轮保存{saved_count}篇，累计{total_saved}篇，当前总数{current_count}篇")
        
        if saved_count == 0:
            logging.warning(f"{category}: 本轮未保存新论文，可能已无更多相关论文")
            break
        
        if current_count >= target_count:
            logging.info(f"{category}: 已达到目标数量{current_count}篇！")
            break
    
    return total_saved

def main(auto_confirm=False):
    """主函数"""
    print("=" * 60)
    print("补充论文脚本 - 将所有标签补充至至少100篇")
    print("=" * 60)
    
    # 加载配置
    config = load_config('config.yaml')
    keywords = config.get('kv', {})
    
    # 获取当前各标签的论文数量
    print("\n检查当前论文数量...")
    category_counts = get_category_counts()
    
    # 显示当前状态
    print("\n当前各标签论文数量:")
    for category, count in sorted(category_counts.items()):
        status = "✓" if count >= MIN_PAPERS else "✗"
        print(f"  {status} {category}: {count}篇")
    
    # 找出需要补充的标签
    need_supplement = []
    for category, count in category_counts.items():
        if count < MIN_PAPERS:
            need_supplement.append((category, count))
    
    if not need_supplement:
        print("\n✅ 所有标签的论文数量都已达到100篇以上！")
        return
    
    print(f"\n需要补充的标签 ({len(need_supplement)}个):")
    for category, count in need_supplement:
        print(f"  - {category}: {count}篇 → 需要补充至{MIN_PAPERS}篇")
    
    # 确认（如果未设置自动确认）
    if not auto_confirm:
        print("\n" + "=" * 60)
        try:
            response = input(f"是否开始补充抓取？(y/n): ")
            if response.lower() != 'y':
                print("已取消")
                return
        except EOFError:
            print("非交互式环境，自动开始补充...")
    
    # 开始补充
    print("\n开始补充抓取...")
    print("=" * 60)
    
    for category, current_count in need_supplement:
        if category not in keywords:
            logging.warning(f"{category}: 配置中未找到对应的关键词，跳过")
            continue
        
        keyword = keywords[category]
        supplement_category(category, keyword, current_count, MIN_PAPERS)
        print()  # 空行分隔
    
    # 显示最终结果
    print("\n" + "=" * 60)
    print("补充完成！最终统计:")
    print("=" * 60)
    
    final_counts = get_category_counts()
    for category, count in sorted(final_counts.items()):
        status = "✓" if count >= MIN_PAPERS else "✗"
        print(f"  {status} {category}: {count}篇")
    
    total = sum(final_counts.values())
    print(f"\n总论文数: {total}篇")

if __name__ == '__main__':
    import sys
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv
    main(auto_confirm=auto_confirm)

