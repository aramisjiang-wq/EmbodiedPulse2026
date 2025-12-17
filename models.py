"""
数据库模型定义
使用 SQLAlchemy ORM
"""
from sqlalchemy import create_engine, Column, String, Date, Text, DateTime, Index, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Paper(Base):
    """论文模型"""
    __tablename__ = 'papers'
    
    id = Column(String, primary_key=True)  # ArXiv ID
    title = Column(Text, nullable=False)
    authors = Column(Text)  # 作者列表（逗号分隔）
    publish_date = Column(Date)
    update_date = Column(Date)
    pdf_url = Column(Text)
    code_url = Column(Text, nullable=True)
    abstract = Column(Text, nullable=True)
    category = Column(String)  # 类别：Manipulation, VLM, VLA等
    # Semantic Scholar补充数据
    citation_count = Column(Integer, default=0, nullable=True)  # 被引用数量
    influential_citation_count = Column(Integer, default=0, nullable=True)  # 高影响力引用数
    author_affiliations = Column(Text, nullable=True)  # 作者机构信息（JSON字符串）
    venue = Column(String, nullable=True)  # 发表期刊/会议
    publication_year = Column(Integer, nullable=True)  # 发表年份
    semantic_scholar_updated_at = Column(DateTime, nullable=True)  # Semantic Scholar数据更新时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 索引
    __table_args__ = (
        Index('idx_category', 'category'),
        Index('idx_publish_date', 'publish_date'),
        Index('idx_title', 'title'),
    )
    
    def to_dict(self):
        """转换为字典"""
        import json
        # 解析机构信息（如果是JSON字符串）
        affiliations = []
        if self.author_affiliations:
            try:
                affiliations = json.loads(self.author_affiliations)
            except:
                # 如果不是JSON，尝试按逗号分割
                affiliations = [aff.strip() for aff in self.author_affiliations.split(',') if aff.strip()]
        
        return {
            'id': self.id,
            'title': self.title,
            'authors': self.authors,
            'date': self.publish_date.strftime('%Y-%m-%d') if self.publish_date else '',
            'pdf_id': self.id,
            'pdf_url': self.pdf_url,
            'code_url': self.code_url,
            'category': self.category,
            'abstract': self.abstract or '',
            'citation_count': self.citation_count or 0,
            'influential_citation_count': self.influential_citation_count or 0,
            'author_affiliations': affiliations,
            'venue': self.venue or '',
            'publication_year': self.publication_year
        }

# 数据库配置
# 支持PostgreSQL和SQLite
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./papers.db')

def get_engine():
    """获取数据库引擎"""
    # PostgreSQL需要连接池配置
    if DATABASE_URL.startswith('postgresql://') or DATABASE_URL.startswith('postgres://'):
        return create_engine(
            DATABASE_URL,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True  # 自动重连
        )
    else:
        # SQLite配置
        return create_engine(DATABASE_URL, echo=False)

def get_session():
    """获取数据库会话"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def init_db():
    """初始化数据库（创建表）"""
    engine = get_engine()
    try:
        Base.metadata.create_all(engine, checkfirst=True)
        print("数据库表创建成功！")
    except Exception as e:
        # 如果索引已存在，忽略错误（PostgreSQL中索引可能已存在）
        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
            print(f"⚠️  部分索引已存在，跳过创建: {e}")
        else:
            raise

