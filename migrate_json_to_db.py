"""
将 JSON 文件数据迁移到数据库
"""
import json
import os
from datetime import datetime
from models import init_db, get_session, Paper
from daily_arxiv import parse_paper_entry_from_string

def migrate_json_to_database(json_path='./docs/cv-arxiv-daily.json'):
    """迁移 JSON 数据到数据库"""
    print(f"开始迁移数据从 {json_path} 到数据库...")
    
    # 初始化数据库
    init_db()
    session = get_session()
    
    try:
        # 读取 JSON 文件
        if not os.path.exists(json_path):
            print(f"JSON 文件不存在: {json_path}")
            return
        
        with open(json_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content:
                print("JSON 文件为空")
                return
            
            data = json.loads(content)
        
        total_papers = 0
        added_papers = 0
        skipped_papers = 0
        
        # 遍历所有类别
        for category, papers in data.items():
            print(f"\n处理类别: {category} ({len(papers)} 篇论文)")
            
            for paper_id, paper_entry in papers.items():
                total_papers += 1
                
                # 解析论文条目
                parsed = parse_paper_entry_from_string(paper_entry)
                if not parsed:
                    skipped_papers += 1
                    continue
                
                # 检查是否已存在
                existing = session.query(Paper).filter_by(id=paper_id).first()
                if existing:
                    # 更新现有记录
                    existing.title = parsed['title']
                    existing.authors = parsed['authors']
                    existing.pdf_url = parsed['pdf_url']
                    existing.code_url = parsed.get('code_url')
                    if parsed['date']:
                        try:
                            existing.publish_date = datetime.strptime(parsed['date'], '%Y-%m-%d').date()
                        except:
                            pass
                    existing.category = category
                    existing.updated_at = datetime.now()
                    skipped_papers += 1
                else:
                    # 创建新记录
                    paper = Paper(
                        id=paper_id,
                        title=parsed['title'],
                        authors=parsed['authors'],
                        pdf_url=parsed['pdf_url'],
                        code_url=parsed.get('code_url'),
                        category=category
                    )
                    if parsed['date']:
                        try:
                            paper.publish_date = datetime.strptime(parsed['date'], '%Y-%m-%d').date()
                        except:
                            pass
                    session.add(paper)
                    added_papers += 1
                
                # 每100条提交一次
                if total_papers % 100 == 0:
                    session.commit()
                    print(f"  已处理 {total_papers} 篇论文...")
        
        # 最终提交
        session.commit()
        
        print(f"\n迁移完成！")
        print(f"  总论文数: {total_papers}")
        print(f"  新增: {added_papers}")
        print(f"  更新/跳过: {skipped_papers}")
        
    except Exception as e:
        session.rollback()
        print(f"迁移失败: {e}")
        raise
    finally:
        session.close()

if __name__ == '__main__':
    migrate_json_to_database()

