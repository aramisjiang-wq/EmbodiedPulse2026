"""
数据库模型定义
使用 SQLAlchemy ORM
"""
from sqlalchemy import create_engine, Column, String, Date, Text, DateTime, Index
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
        return {
            'id': self.id,
            'title': self.title,
            'authors': self.authors,
            'date': self.publish_date.strftime('%Y-%m-%d') if self.publish_date else '',
            'pdf_id': self.id,
            'pdf_url': self.pdf_url,
            'code_url': self.code_url,
            'category': self.category
        }

# 数据库配置
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./papers.db')

def get_engine():
    """获取数据库引擎"""
    return create_engine(DATABASE_URL, echo=False)

def get_session():
    """获取数据库会话"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def init_db():
    """初始化数据库（创建表）"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("数据库表创建成功！")

