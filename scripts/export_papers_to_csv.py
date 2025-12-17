#!/usr/bin/env python3
"""
导出论文数据为CSV格式
"""
import sys
import os
import csv
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import get_session, Paper

def export_papers_to_csv(output_file='papers_export.csv'):
    """导出所有论文数据为CSV格式"""
    session = None
    try:
        print("=" * 60)
        print("开始导出论文数据...")
        print("=" * 60)
        
        # 获取数据库会话
        session = get_session()
        
        # 查询所有论文，按发布日期倒序
        papers = session.query(Paper).order_by(Paper.publish_date.desc()).all()
        
        total_count = len(papers)
        print(f"📊 查询到 {total_count} 篇论文")
        
        if total_count == 0:
            print("⚠️  数据库中没有论文数据")
            return
        
        # 定义CSV列
        fieldnames = [
            'id',                    # ArXiv ID
            'title',                 # 标题
            'authors',               # 作者
            'publish_date',          # 发布日期
            'update_date',           # 更新日期
            'category',              # 类别
            'pdf_url',               # PDF链接
            'code_url',              # 代码链接
            'abstract',              # 摘要
            'citation_count',        # 引用数
            'influential_citation_count',  # 高影响力引用数
            'venue',                 # 发表场所
            'publication_year',      # 发表年份
            'author_affiliations',   # 作者机构
            'semantic_scholar_updated_at',  # Semantic Scholar更新时间
            'created_at',            # 创建时间
            'updated_at'             # 更新时间
        ]
        
        # 写入CSV文件
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # 写入表头
            writer.writeheader()
            
            # 写入数据
            for i, paper in enumerate(papers, 1):
                # 处理日期格式
                publish_date_str = paper.publish_date.strftime('%Y-%m-%d') if paper.publish_date else ''
                update_date_str = paper.update_date.strftime('%Y-%m-%d') if paper.update_date else ''
                created_at_str = paper.created_at.strftime('%Y-%m-%d %H:%M:%S') if paper.created_at else ''
                updated_at_str = paper.updated_at.strftime('%Y-%m-%d %H:%M:%S') if paper.updated_at else ''
                semantic_updated_str = paper.semantic_scholar_updated_at.strftime('%Y-%m-%d %H:%M:%S') if paper.semantic_scholar_updated_at else ''
                
                # 处理作者机构（如果是JSON字符串，转换为可读格式）
                affiliations_str = ''
                if paper.author_affiliations:
                    try:
                        import json
                        affiliations = json.loads(paper.author_affiliations)
                        if isinstance(affiliations, list):
                            affiliations_str = '; '.join(affiliations)
                        else:
                            affiliations_str = str(affiliations)
                    except:
                        affiliations_str = paper.author_affiliations
                
                # 写入一行数据
                writer.writerow({
                    'id': paper.id or '',
                    'title': paper.title or '',
                    'authors': paper.authors or '',
                    'publish_date': publish_date_str,
                    'update_date': update_date_str,
                    'category': paper.category or '',
                    'pdf_url': paper.pdf_url or '',
                    'code_url': paper.code_url or '',
                    'abstract': (paper.abstract or '').replace('\n', ' ').replace('\r', ' '),  # 移除换行符
                    'citation_count': paper.citation_count or 0,
                    'influential_citation_count': paper.influential_citation_count or 0,
                    'venue': paper.venue or '',
                    'publication_year': paper.publication_year or '',
                    'author_affiliations': affiliations_str,
                    'semantic_scholar_updated_at': semantic_updated_str,
                    'created_at': created_at_str,
                    'updated_at': updated_at_str
                })
                
                # 显示进度
                if i % 100 == 0:
                    print(f"  已导出 {i}/{total_count} 篇论文...")
        
        print("=" * 60)
        print(f"✅ 导出完成！")
        print(f"📁 文件位置: {os.path.abspath(output_file)}")
        print(f"📊 总记录数: {total_count}")
        print("=" * 60)
        
    except Exception as e:
        print("=" * 60)
        print(f"❌ 导出失败: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
    finally:
        if session:
            session.close()

if __name__ == '__main__':
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'papers_export_{timestamp}.csv'
    
    # 如果提供了命令行参数，使用指定的文件名
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    
    export_papers_to_csv(output_file)

