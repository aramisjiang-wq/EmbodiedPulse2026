"""
数据集信息数据库模型定义
使用独立的数据库，不与论文数据库混在一起
"""
from sqlalchemy import create_engine, Column, String, Text, DateTime, Index, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Dataset(Base):
    """数据集信息模型"""
    __tablename__ = 'datasets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)  # 数据集名称
    description = Column(Text)  # 数据集描述/简介
    category = Column(String)  # 数据集类别（如：视觉、语言、多模态等）
    publisher = Column(String)  # 发布方（如：Stanford University, UC Berkeley等）
    publish_date = Column(String)  # 发布时间（如：2024.03）
    project_link = Column(String)  # 项目链接
    paper_link = Column(String)  # 论文链接
    dataset_link = Column(String)  # 数据集链接
    scale = Column(Text)  # 规模（如：1.7TB，76,000个轨迹等）
    link = Column(String)  # 通用链接（兼容旧数据）
    source = Column(String)  # 数据来源（如：juejin文章）
    source_url = Column(String)  # 来源URL
    tags = Column(Text)  # 标签（JSON字符串）
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 索引
    __table_args__ = (
        Index('idx_category', 'category'),
        Index('idx_name', 'name'),
        Index('idx_source', 'source'),
        Index('idx_created_at', 'created_at'),
    )
    
    def to_dict(self):
        """转换为字典"""
        import json
        tags = []
        if self.tags:
            try:
                tags = json.loads(self.tags)
            except:
                tags = [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'publisher': self.publisher or '',
            'publish_date': self.publish_date or '',
            'project_link': self.project_link or '',
            'paper_link': self.paper_link or '',
            'dataset_link': self.dataset_link or self.link or '',
            'scale': self.scale or '',
            'link': self.link or self.dataset_link or '',  # 兼容旧数据
            'source': self.source,
            'source_url': self.source_url,
            'tags': tags,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else ''
        }

# 数据集数据库配置（独立数据库）
DATASETS_DATABASE_URL = os.getenv('DATASETS_DATABASE_URL', 'sqlite:///./datasets.db')

def get_datasets_engine():
    """获取数据集数据库引擎"""
    return create_engine(DATASETS_DATABASE_URL, echo=False)

def get_datasets_session():
    """获取数据集数据库会话"""
    engine = get_datasets_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def init_datasets_db():
    """初始化数据集数据库（创建表）"""
    engine = get_datasets_engine()
    Base.metadata.create_all(engine)
    print("数据集数据库表创建成功！")

