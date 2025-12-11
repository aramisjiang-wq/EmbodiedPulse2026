"""
招聘信息数据库模型定义
使用独立的数据库，不与论文数据库混在一起
"""
from sqlalchemy import create_engine, Column, String, Text, DateTime, Index, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Job(Base):
    """招聘信息模型"""
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)  # 招聘标题（公司/机构 - 职位描述）
    description = Column(Text)  # 详细描述
    link = Column(String)  # 链接URL
    update_date = Column(String)  # 更新日期（从GitHub提取，如2025.12.7）
    source_date = Column(String)  # 数据源中的日期字符串
    company = Column(String)  # 公司/机构名称
    location = Column(String)  # 地点
    job_type = Column(String)  # 职位类型（PhD/PostDoc/Intern/FullTime等）
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 索引
    __table_args__ = (
        Index('idx_update_date', 'update_date'),
        Index('idx_company', 'company'),
        Index('idx_job_type', 'job_type'),
        Index('idx_link', 'link'),
        Index('idx_created_at', 'created_at'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'link': self.link,
            'update_date': self.update_date,
            'source_date': self.source_date,
            'company': self.company,
            'location': self.location,
            'job_type': self.job_type,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else ''
        }

# 招聘信息数据库配置（独立数据库）
JOBS_DATABASE_URL = os.getenv('JOBS_DATABASE_URL', 'sqlite:///./jobs.db')

def get_jobs_engine():
    """获取招聘信息数据库引擎"""
    return create_engine(JOBS_DATABASE_URL, echo=False)

def get_jobs_session():
    """获取招聘信息数据库会话"""
    engine = get_jobs_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def init_jobs_db():
    """初始化招聘信息数据库（创建表）"""
    engine = get_jobs_engine()
    Base.metadata.create_all(engine)
    print("招聘信息数据库表创建成功！")


