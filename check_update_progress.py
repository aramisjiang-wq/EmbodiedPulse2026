#!/usr/bin/env python3
"""
检查Semantic Scholar数据更新进度
"""
from models import get_session, Paper

session = get_session()

total = session.query(Paper).count()
has_data = session.query(Paper).filter(
    (Paper.citation_count != None) | 
    (Paper.venue != None) |
    (Paper.publication_year != None)
).count()
has_citations = session.query(Paper).filter(
    (Paper.citation_count != None) & (Paper.citation_count > 0)
).count()

print('=' * 60)
print('Semantic Scholar数据更新进度')
print('=' * 60)
print(f'总论文数: {total}')
print(f'已有数据: {has_data} ({has_data/total*100:.1f}%)')
print(f'有引用数据: {has_citations} ({has_citations/total*100:.1f}%)')
print(f'待更新: {total - has_data} ({(total-has_data)/total*100:.1f}%)')
print()

# 按类别统计
from sqlalchemy import func
stats = session.query(
    Paper.category,
    func.count(Paper.id).label('total')
).group_by(Paper.category).all()

print('按类别统计:')
for cat, total_cat in stats:
    # 单独查询有引用的数量
    with_cit = session.query(Paper).filter(
        Paper.category == cat,
        Paper.citation_count > 0
    ).count()
    print(f'  {cat}: {total_cat}篇 (有引用: {with_cit}篇)')

session.close()

