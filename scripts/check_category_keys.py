#!/usr/bin/env python3
"""检查数据库中的分类键"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import get_session, Paper
from collections import Counter

session = get_session()
papers = session.query(Paper).all()

cats = []
for p in papers:
    if p.category:
        if '/' in p.category:
            cats.append(p.category.split('/')[0])
        else:
            cats.append(p.category)

cat_counts = Counter(cats)
print('数据库中的分类键统计:')
for cat, count in cat_counts.most_common(15):
    print(f'  {cat}: {count} 篇')

session.close()

