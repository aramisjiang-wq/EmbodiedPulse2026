#!/usr/bin/env python3
"""
检查基准分类下的论文是否匹配 "embodied benchmark" 检索词
"""
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import get_session, Paper
from taxonomy import normalize_category

def check_embodied_benchmark_match(text):
    """
    检查文本中是否包含 "embodied benchmark" 相关的关键词
    
    匹配规则：
    1. 包含 "embodied benchmark" 或 "embodied-benchmark"
    2. 包含 "embodied" 和 "benchmark"（在较近的位置）
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # 1. 精确匹配 "embodied benchmark" 或变体
    patterns = [
        r'\bembodied\s+benchmark\b',
        r'\bembodied-benchmark\b',
        r'\bembodiedbenchmark\b',
    ]
    
    for pattern in patterns:
        if re.search(pattern, text_lower):
            return True
    
    # 2. 检查是否同时包含 "embodied" 和 "benchmark"（在较近的位置，比如50个字符内）
    embodied_positions = [m.start() for m in re.finditer(r'\bembodied\b', text_lower)]
    benchmark_positions = [m.start() for m in re.finditer(r'\bbenchmark\b', text_lower)]
    
    if embodied_positions and benchmark_positions:
        # 检查是否有任何 embodied 和 benchmark 在50个字符内
        for emb_pos in embodied_positions:
            for bench_pos in benchmark_positions:
                if abs(emb_pos - bench_pos) <= 50:
                    return True
    
    return False

def main():
    session = get_session()
    
    try:
        # 获取所有基准分类的论文（直接使用分类键，因为 normalize_category 可能有问题）
        all_papers = session.query(Paper).all()
        benchmark_papers = []
        
        for paper in all_papers:
            if paper.category:
                # 直接检查分类键
                cat_key = paper.category.split('/')[0] if '/' in paper.category else paper.category
                if cat_key == 'Benchmark':
                    benchmark_papers.append(paper)
        
        print(f"📊 基准分类下的论文总数: {len(benchmark_papers)} 篇\n")
        print("=" * 80)
        print("检查论文是否匹配 'embodied benchmark' 检索词...")
        print("=" * 80)
        
        matched_papers = []
        unmatched_papers = []
        
        for paper in benchmark_papers:
            # 检查标题和摘要
            title = paper.title or ''
            abstract = paper.abstract or ''
            full_text = f"{title} {abstract}"
            
            if check_embodied_benchmark_match(full_text):
                matched_papers.append(paper)
            else:
                unmatched_papers.append(paper)
        
        print(f"\n✅ 匹配的论文: {len(matched_papers)} 篇")
        if matched_papers:
            print("\n匹配的论文列表:")
            for i, paper in enumerate(matched_papers, 1):
                title = paper.title or '无标题'
                print(f"  {i}. [{paper.id}] {title}")
        
        print(f"\n❌ 不匹配的论文: {len(unmatched_papers)} 篇\n")
        
        if unmatched_papers:
            print("=" * 80)
            print("不匹配的论文列表（前50篇）:")
            print("=" * 80)
            
            for i, paper in enumerate(unmatched_papers[:50], 1):
                title = paper.title or '无标题'
                abstract = (paper.abstract or '')[:100] + '...' if paper.abstract and len(paper.abstract) > 100 else (paper.abstract or '无摘要')
                print(f"\n{i}. ID: {paper.id}")
                print(f"   标题: {title}")
                print(f"   摘要: {abstract}")
                print(f"   发布日期: {paper.publish_date}")
            
            if len(unmatched_papers) > 50:
                print(f"\n... 还有 {len(unmatched_papers) - 50} 篇不匹配的论文未显示")
            
            print("\n" + "=" * 80)
            print(f"总计不匹配论文: {len(unmatched_papers)} 篇")
            print("=" * 80)
            
            # 保存不匹配的论文ID到文件
            output_file = 'unmatched_benchmark_papers.txt'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"不匹配 'embodied benchmark' 的基准论文列表\n")
                f.write(f"总计: {len(unmatched_papers)} 篇\n")
                f.write("=" * 80 + "\n\n")
                for paper in unmatched_papers:
                    f.write(f"ID: {paper.id}\n")
                    f.write(f"标题: {paper.title or '无标题'}\n")
                    f.write(f"摘要: {(paper.abstract or '无摘要')[:200]}\n")
                    f.write(f"发布日期: {paper.publish_date}\n")
                    f.write("-" * 80 + "\n")
            
            print(f"\n📝 不匹配论文列表已保存到: {output_file}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    main()

