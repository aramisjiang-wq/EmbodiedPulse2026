"""
新闻信息数据库模型定义
使用独立的数据库，不与论文数据库混在一起
"""
from sqlalchemy import create_engine, Column, String, Text, DateTime, Index, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class News(Base):
    """新闻信息模型"""
    __tablename__ = 'news'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)  # 新闻标题
    description = Column(Text)  # 新闻描述/摘要
    link = Column(String)  # 新闻链接
    source = Column(String)  # 新闻来源（如：github, hackernews等）
    platform = Column(String)  # 平台名称
    published_at = Column(DateTime)  # 发布时间
    image_url = Column(String)  # 图片URL（如果有）
    author = Column(String)  # 作者（如果有）
    tags = Column(Text)  # 标签（JSON字符串）
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 索引
    __table_args__ = (
        Index('idx_source', 'source'),
        Index('idx_platform', 'platform'),
        Index('idx_published_at', 'published_at'),
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
            'title': self.title,
            'description': self.description,
            'link': self.link,
            'source': self.source,
            'platform': self.platform,
            'published_at': self.published_at.strftime('%Y-%m-%d %H:%M:%S') if self.published_at else '',
            'image_url': self.image_url,
            'author': self.author,
            'tags': tags,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else ''
        }

# 新闻数据库配置（独立数据库）
# 支持PostgreSQL和SQLite
# 如果使用PostgreSQL，可以通过NEWS_DATABASE_URL指定独立数据库
# 或者使用主数据库URL + schema/database名称
NEWS_DATABASE_URL = os.getenv('NEWS_DATABASE_URL', os.getenv('DATABASE_URL', 'sqlite:///./news.db'))

def get_news_engine():
    """获取新闻数据库引擎"""
    # PostgreSQL需要连接池配置
    if NEWS_DATABASE_URL.startswith('postgresql://') or NEWS_DATABASE_URL.startswith('postgres://'):
        return create_engine(
            NEWS_DATABASE_URL,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True  # 自动重连
        )
    else:
        # SQLite配置
        return create_engine(NEWS_DATABASE_URL, echo=False)

def get_news_session():
    """获取新闻数据库会话"""
    engine = get_news_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def init_news_db():
    """初始化新闻数据库（创建表）"""
    engine = get_news_engine()
    try:
        Base.metadata.create_all(engine, checkfirst=True)
        print("新闻数据库表创建成功！")
    except Exception as e:
        # 如果索引已存在，忽略错误（PostgreSQL中索引可能已存在）
        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
            print(f"⚠️  部分索引已存在，跳过创建: {e}")
        else:
            raise







