#!/usr/bin/env python3
"""
检查数据库中的重复论文
核心原则：确保没有重复论文（基于ID和标题相似度）
"""
from models import get_session, Paper
from sqlalchemy import func
from collections import Counter
from utils import calculate_title_similarity
import sys

def check_duplicate_ids():
    """检查重复的论文ID（理论上不应该有，因为id是主键）"""
    print("=" * 60)
    print("检查1: 重复论文ID")
    print("=" * 60)
    
    session = get_session()
    try:
        total = session.query(func.count(Paper.id)).scalar()
        unique_ids = session.query(func.count(func.distinct(Paper.id))).scalar()
        
        print(f"总记录数: {total}")
        print(f"唯一ID数: {unique_ids}")
        
        if total != unique_ids:
            print("⚠️  发现重复ID！")
            # 查找重复的ID
            duplicates = session.query(
                Paper.id, 
                func.count(Paper.id).label('count')
            ).group_by(Paper.id).having(func.count(Paper.id) > 1).all()
            
            for paper_id, count in duplicates:
                print(f"  重复ID: {paper_id}, 出现次数: {count}")
            return False
        else:
            print("✅ 没有重复ID（数据库主键约束正常）")
            return True
    finally:
        session.close()

def check_duplicate_titles():
    """检查完全相同的标题"""
    print("\n" + "=" * 60)
    print("检查2: 完全相同的标题")
    print("=" * 60)
    
    session = get_session()
    try:
        titles = [p.title for p in session.query(Paper.title).all() if p.title]
        title_counter = Counter(titles)
        duplicate_titles = {title: count for title, count in title_counter.items() if count > 1}
        
        if duplicate_titles:
            print(f"⚠️  发现 {len(duplicate_titles)} 个完全相同的标题:")
            for title, count in list(duplicate_titles.items())[:10]:
                print(f"  \"{title[:60]}...\" 出现 {count} 次")
            return False
        else:
            print("✅ 没有完全相同的标题")
            return True
    finally:
        session.close()

def check_similar_titles(threshold=0.85):
    """检查相似度高的标题（可能重复）"""
    print("\n" + "=" * 60)
    print(f"检查3: 相似标题（相似度 >= {threshold}）")
    print("=" * 60)
    
    session = get_session()
    try:
        papers = session.query(Paper).all()
        similar_pairs = []
        
        print(f"正在检查 {len(papers)} 篇论文...")
        
        for i, paper1 in enumerate(papers):
            if not paper1.title:
                continue
                
            for paper2 in papers[i+1:]:
                if not paper2.title:
                    continue
                
                # 跳过相同ID的论文（它们可能是同一篇论文的不同版本）
                if paper1.id == paper2.id:
                    continue
                
                similarity = calculate_title_similarity(paper1.title, paper2.title)
                if similarity >= threshold:
                    similar_pairs.append({
                        'id1': paper1.id,
                        'title1': paper1.title,
                        'id2': paper2.id,
                        'title2': paper2.title,
                        'similarity': similarity
                    })
        
        if similar_pairs:
            print(f"⚠️  发现 {len(similar_pairs)} 对相似标题:")
            for pair in similar_pairs[:20]:  # 只显示前20对
                print(f"\n  相似度: {pair['similarity']:.2%}")
                print(f"  ID1: {pair['id1']}")
                print(f"  标题1: {pair['title1'][:60]}...")
                print(f"  ID2: {pair['id2']}")
                print(f"  标题2: {pair['title2'][:60]}...")
            return False
        else:
            print("✅ 没有发现高度相似的标题")
            return True
    finally:
        session.close()

def check_same_id_different_categories():
    """检查是否有相同ID但不同类别的论文（这种情况应该更新类别，不应该重复）"""
    print("\n" + "=" * 60)
    print("检查4: 相同ID的论文（数据库主键约束，理论上不应该有）")
    print("=" * 60)
    
    session = get_session()
    try:
        # 由于id是主键，理论上不应该有重复
        # 这个检查主要是验证数据库约束是否正常工作
        total = session.query(func.count(Paper.id)).scalar()
        unique_ids = session.query(func.count(func.distinct(Paper.id))).scalar()
        
        if total == unique_ids:
            print("✅ 数据库主键约束正常，没有重复ID")
            return True
        else:
            print("⚠️  发现重复ID，数据库约束可能有问题")
            return False
    finally:
        session.close()

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("论文去重检查工具")
    print("核心原则：确保没有重复论文（基于ID和标题相似度）")
    print("=" * 60)
    
    results = []
    
    # 执行所有检查
    results.append(("重复ID检查", check_duplicate_ids()))
    results.append(("相同标题检查", check_duplicate_titles()))
    results.append(("相似标题检查", check_similar_titles()))
    results.append(("数据库约束检查", check_same_id_different_categories()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ 通过" if passed else "⚠️  发现问题"
        print(f"{check_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有检查通过，没有发现重复论文")
        return 0
    else:
        print("⚠️  发现问题，请检查上述结果")
        return 1

if __name__ == '__main__':
    sys.exit(main())

