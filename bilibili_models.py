"""
B站视频数据数据库模型定义
使用独立的数据库，存储UP主信息和视频数据
"""
from sqlalchemy import create_engine, Column, String, Text, DateTime, Index, Integer, BigInteger, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import json

Base = declarative_base()

class BilibiliUp(Base):
    """B站UP主信息模型"""
    __tablename__ = 'bilibili_ups'
    
    uid = Column(BigInteger, primary_key=True)  # UP主UID
    name = Column(String, nullable=False)  # UP主名称
    face = Column(Text)  # 头像URL
    sign = Column(Text)  # 签名
    level = Column(Integer, default=0)  # 等级
    fans = Column(BigInteger, default=0)  # 粉丝数（原始数值）
    fans_formatted = Column(String)  # 粉丝数（格式化字符串，如"1.2万"）
    friend = Column(Integer, default=0)  # 关注数
    space_url = Column(Text)  # 空间链接
    # 统计数据（最新）
    videos_count = Column(Integer, default=0)  # 视频总数
    views_count = Column(BigInteger, default=0)  # 总播放量
    views_formatted = Column(String)  # 总播放量（格式化）
    likes_count = Column(BigInteger, default=0)  # 获赞数
    likes_formatted = Column(String)  # 获赞数（格式化）
    # 状态
    is_active = Column(Boolean, default=True)  # 是否活跃（是否在监控列表中）
    last_fetch_at = Column(DateTime)  # 最后抓取时间
    fetch_error = Column(Text)  # 抓取错误信息（如果有）
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 索引
    __table_args__ = (
        Index('idx_name', 'name'),
        Index('idx_is_active', 'is_active'),
        Index('idx_last_fetch_at', 'last_fetch_at'),
    )
    
    def to_dict(self):
        """转换为字典"""
        # 导入格式化函数（如果views_formatted为空，使用views_count格式化）
        from bilibili_client import format_number
        
        # ✅ 修复：如果数据库值为0，尝试从视频表计算
        videos_count = self.videos_count or 0
        views_count = self.views_count or 0
        
        # 如果统计数据为0，尝试从视频表计算（需要数据库会话）
        if videos_count == 0 or views_count == 0:
            try:
                # 避免循环导入，直接使用当前模块的函数
                session = get_bilibili_session()
                try:
                    from sqlalchemy import func
                    if videos_count == 0:
                        video_count = session.query(func.count(BilibiliVideo.bvid)).filter_by(
                            uid=self.uid, is_deleted=False
                        ).scalar()
                        if video_count and video_count > 0:
                            videos_count = video_count
                    
                    if views_count == 0:
                        total_views = session.query(func.sum(BilibiliVideo.play)).filter_by(
                            uid=self.uid, is_deleted=False
                        ).scalar() or 0
                        if total_views > 0:
                            views_count = total_views
                finally:
                    session.close()
            except Exception:
                # 如果计算失败，使用原值
                pass
        
        return {
            'uid': self.uid,
            'name': self.name,
            'face': self.face or '',
            'sign': self.sign or '',
            'level': self.level,
            'fans': self.fans_formatted or (format_number(self.fans) if self.fans else '0'),
            'fans_raw': self.fans,
            'fans_formatted': self.fans_formatted or (format_number(self.fans) if self.fans else '0'),  # 添加格式化字段，供前端使用
            'friend': str(self.friend) if self.friend else '0',
            'space_url': self.space_url or f"https://space.bilibili.com/{self.uid}",
            'videos_count': videos_count,  # ✅ 修复：使用计算后的值
            'views': format_number(views_count) if views_count > 0 else (self.views_formatted or '0'),  # ✅ 修复：使用计算后的值
            'views_formatted': format_number(views_count) if views_count > 0 else (self.views_formatted or '0'),  # ✅ 修复：使用计算后的值
            'views_raw': views_count,  # ✅ 修复：使用计算后的值
            'views_count': views_count,  # ✅ 修复：使用计算后的值
            'likes': self.likes_formatted or (format_number(self.likes_count) if self.likes_count else '0'),
            'likes_formatted': self.likes_formatted or (format_number(self.likes_count) if self.likes_count else '0'),  # 添加格式化字段
            'likes_raw': self.likes_count,
            'likes_count': self.likes_count or 0,  # 添加原始字段
            'last_fetch_at': self.last_fetch_at.isoformat() if self.last_fetch_at else None,
            'fetch_error': self.fetch_error,
        }


class BilibiliVideo(Base):
    """B站视频信息模型"""
    __tablename__ = 'bilibili_videos'
    
    bvid = Column(String, primary_key=True)  # 视频BV号
    aid = Column(BigInteger)  # 视频AID
    uid = Column(BigInteger, nullable=False, index=True)  # UP主UID（外键）
    title = Column(Text, nullable=False)  # 视频标题
    pic = Column(Text)  # 封面图URL
    description = Column(Text)  # 视频描述
    length = Column(String)  # 视频时长（如"10:30"）
    # 统计数据
    play = Column(BigInteger, default=0)  # 播放量（原始数值）
    play_formatted = Column(String)  # 播放量（格式化字符串）
    video_review = Column(Integer, default=0)  # 评论数
    video_review_formatted = Column(String)  # 评论数（格式化）
    favorites = Column(Integer, default=0)  # 收藏数
    favorites_formatted = Column(String)  # 收藏数（格式化）
    # 时间
    pubdate = Column(DateTime, nullable=False, index=True)  # 发布时间
    pubdate_raw = Column(BigInteger)  # 发布时间戳（秒）
    # URL
    url = Column(Text)  # 视频链接
    # 状态
    is_deleted = Column(Boolean, default=False)  # 是否已删除
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 索引
    __table_args__ = (
        Index('idx_uid', 'uid'),
        Index('idx_pubdate', 'pubdate'),
        Index('idx_pubdate_raw', 'pubdate_raw'),
        Index('idx_play', 'play'),
        Index('idx_uid_pubdate', 'uid', 'pubdate'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'bvid': self.bvid,
            'aid': self.aid,
            'title': self.title or '',
            'pic': self.pic or '',
            'description': self.description or '',
            'length': self.length or '',
            'play': self.play_formatted or '0',
            'play_raw': self.play,
            'video_review': self.video_review_formatted or '0',
            'favorites': self.favorites_formatted or '0',
            'pubdate': self.pubdate.strftime('%Y-%m-%d %H:%M:%S') if self.pubdate else '',
            'pubdate_raw': self.pubdate_raw,
            'url': self.url or f"https://www.bilibili.com/video/{self.bvid}",
        }


# 数据库配置
# 使用独立的数据库文件
BILIBILI_DATABASE_URL = os.getenv('BILIBILI_DATABASE_URL', 'sqlite:///./bilibili.db')

def get_bilibili_engine():
    """获取B站数据库引擎"""
    if BILIBILI_DATABASE_URL.startswith('postgresql://') or BILIBILI_DATABASE_URL.startswith('postgres://'):
        return create_engine(
            BILIBILI_DATABASE_URL,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )
    else:
        # SQLite配置
        return create_engine(BILIBILI_DATABASE_URL, echo=False)

def get_bilibili_session():
    """获取B站数据库会话"""
    engine = get_bilibili_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def init_bilibili_db():
    """初始化B站数据库（创建表）"""
    engine = get_bilibili_engine()
    try:
        Base.metadata.create_all(engine, checkfirst=True)
        print("B站数据库表创建成功！")
    except Exception as e:
        # 如果索引已存在，忽略错误（PostgreSQL中索引可能已存在）
        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
            print(f"⚠️  部分索引已存在，跳过创建: {e}")
        else:
            raise
