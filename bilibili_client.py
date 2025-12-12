#!/usr/bin/env python3
"""
Bilibili API客户端
使用 bilibili-api-python 库获取UP主信息和视频列表
"""
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

try:
    from bilibili_api import user
    BILIBILI_API_AVAILABLE = True
except ImportError as e:
    BILIBILI_API_AVAILABLE = False
    logging.warning(f"bilibili-api-python 未安装或导入失败: {e}")
    logging.warning("请运行: pip install bilibili-api-python aiohttp")

logger = logging.getLogger(__name__)

class BilibiliClient:
    """Bilibili API客户端（使用 bilibili-api-python 库）"""
    
    def __init__(self, timeout=10):
        """
        初始化Bilibili客户端
        
        Args:
            timeout: 请求超时时间（秒）
        """
        self.timeout = timeout
        if not BILIBILI_API_AVAILABLE:
            raise ImportError("bilibili-api-python 未安装，请运行: pip install bilibili-api-python aiohttp")
    
    async def _get_user_info_async(self, mid: int) -> Optional[Dict]:
        """
        异步获取UP主基本信息
        
        Args:
            mid: UP主的UID（用户ID）
            
        Returns:
            UP主信息字典
        """
        try:
            u = user.User(uid=mid)
            info = await u.get_user_info()
            
            return {
                'mid': info.get('mid'),
                'name': info.get('name', ''),
                'face': info.get('face', ''),
                'sign': info.get('sign', ''),
                'level': info.get('level_info', {}).get('current_level', 0),
                'fans': info.get('fans', 0),
                'friend': info.get('friend', 0),  # 关注数
            }
        except Exception as e:
            logger.error(f"获取UP主信息失败: {e}")
            return None
    
    async def _get_user_videos_async(self, mid: int, page: int = 1, page_size: int = 10) -> Optional[List[Dict]]:
        """
        异步获取UP主的视频列表
        
        Args:
            mid: UP主的UID
            page: 页码（从1开始）
            page_size: 每页数量
            
        Returns:
            视频列表
        """
        try:
            u = user.User(uid=mid)
            result = await u.get_videos(pn=page, ps=page_size)
            
            videos = []
            # bilibili-api 返回格式：{'list': {'vlist': [...]}}
            vlist = result.get('list', {}).get('vlist', [])
            
            for video in vlist:
                # 适配 bilibili-api 返回的字段格式
                # 播放数可能在 play 或 stat.view 中
                play_count = video.get('play', 0)
                if not play_count:
                    stat = video.get('stat', {})
                    play_count = stat.get('view', 0) if isinstance(stat, dict) else 0
                
                # 评论数可能在 video_review 或 stat.reply 中
                review_count = video.get('video_review', 0)
                if not review_count:
                    stat = video.get('stat', {})
                    review_count = stat.get('reply', 0) if isinstance(stat, dict) else 0
                
                # 收藏数可能在 favorites 或 stat.favorite 中
                favorites_count = video.get('favorites', 0)
                if not favorites_count:
                    stat = video.get('stat', {})
                    favorites_count = stat.get('favorite', 0) if isinstance(stat, dict) else 0
                
                # 发布时间可能在 created 或 pubdate 中
                # 注意：bilibili-api 返回的 created 可能是秒级时间戳
                pubdate = video.get('created', 0) or video.get('pubdate', 0)
                # 如果时间戳看起来像毫秒（大于当前时间戳的10倍），则除以1000
                import time
                current_timestamp = int(time.time())
                if pubdate > current_timestamp * 10:
                    pubdate = pubdate // 1000
                
                videos.append({
                    'bvid': video.get('bvid', ''),
                    'aid': video.get('aid', 0),
                    'title': video.get('title', ''),
                    'pic': video.get('pic', ''),
                    'play': play_count,
                    'video_review': review_count,
                    'favorites': favorites_count,
                    'pubdate': pubdate,
                    'description': video.get('description', ''),
                    'length': video.get('length', ''),  # 时长格式如 "10:30"
                })
            
            return videos
        except Exception as e:
            logger.error(f"获取视频列表失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    async def _get_user_stat_async(self, mid: int) -> Optional[Dict]:
        """
        异步获取UP主统计数据
        
        Args:
            mid: UP主的UID
            
        Returns:
            统计数据字典
        """
        try:
            u = user.User(uid=mid)
            # 获取用户信息
            info = await u.get_user_info()
            
            # 尝试获取用户统计信息
            # bilibili-api 的 user.User 类可能有 get_user_stat 方法
            likes = 0
            total_views = 0
            
            try:
                # 尝试使用 get_user_stat 方法（如果存在）
                if hasattr(u, 'get_user_stat'):
                    stat_info = await u.get_user_stat()
                    if isinstance(stat_info, dict):
                        archive = stat_info.get('archive', {})
                        total_views = archive.get('view', 0) if isinstance(archive, dict) else 0
                        likes = stat_info.get('likes', 0)
            except Exception as stat_error:
                logger.debug(f"get_user_stat 方法不可用: {stat_error}")
            
            # 如果统计信息获取失败，尝试从用户信息中获取
            if not likes:
                likes = info.get('likes', 0)
            
            # 如果总播放数为0，尝试从视频列表计算（仅作为备选）
            if not total_views:
                try:
                    videos_result = await u.get_videos(pn=1, ps=50)
                    vlist = videos_result.get('list', {}).get('vlist', [])
                    total_views = sum(
                        v.get('play', 0) or (v.get('stat', {}).get('view', 0) if isinstance(v.get('stat'), dict) else 0)
                        for v in vlist
                    )
                except Exception as video_error:
                    logger.debug(f"从视频列表计算播放数失败: {video_error}")
                    total_views = 0
            
            return {
                'videos': total_views,  # 总播放数（从视频列表计算）
                'likes': likes,  # 获赞数
                'views': total_views,  # 总播放数
            }
        except Exception as e:
            logger.error(f"获取统计数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 如果获取统计失败，返回空字典而不是None
            return {
                'videos': 0,
                'likes': 0,
                'views': 0,
            }
    
    def get_user_info(self, mid: int, retry: int = 2) -> Optional[Dict]:
        """
        获取UP主基本信息（同步接口）
        
        Args:
            mid: UP主的UID
            retry: 重试次数
            
        Returns:
            UP主信息字典
        """
        for attempt in range(retry + 1):
            try:
                result = asyncio.run(self._get_user_info_async(mid))
                if result:
                    return result
                if attempt < retry:
                    import time
                    time.sleep(2 ** attempt)  # 指数退避
            except Exception as e:
                logger.error(f"获取UP主信息失败 (尝试 {attempt + 1}/{retry + 1}): {e}")
                if attempt < retry:
                    import time
                    time.sleep(2 ** attempt)
        return None
    
    def get_user_videos(self, mid: int, pn: int = 1, ps: int = 10, retry: int = 2) -> Optional[List[Dict]]:
        """
        获取UP主的视频列表（同步接口）
        
        Args:
            mid: UP主的UID
            pn: 页码
            ps: 每页数量
            retry: 重试次数
            
        Returns:
            视频列表
        """
        for attempt in range(retry + 1):
            try:
                result = asyncio.run(self._get_user_videos_async(mid, pn, ps))
                if result:
                    return result
                if attempt < retry:
                    import time
                    time.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"获取视频列表失败 (尝试 {attempt + 1}/{retry + 1}): {e}")
                if attempt < retry:
                    import time
                    time.sleep(2 ** attempt)
        return None
    
    def get_user_stat(self, mid: int, retry: int = 2) -> Optional[Dict]:
        """
        获取UP主统计数据（同步接口）
        
        Args:
            mid: UP主的UID
            retry: 重试次数
            
        Returns:
            统计数据字典
        """
        for attempt in range(retry + 1):
            try:
                result = asyncio.run(self._get_user_stat_async(mid))
                if result:
                    return result
                if attempt < retry:
                    import time
                    time.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"获取统计数据失败 (尝试 {attempt + 1}/{retry + 1}): {e}")
                if attempt < retry:
                    import time
                    time.sleep(2 ** attempt)
        return None
    
    def get_all_data(self, mid: int, video_count: int = 10) -> Optional[Dict]:
        """
        获取UP主的完整数据（信息+统计+视频列表）
        
        Args:
            mid: UP主的UID
            video_count: 获取的视频数量
            
        Returns:
            完整数据字典
        """
        try:
            # 使用异步方式一次性获取所有数据
            async def fetch_all():
                user_info_task = self._get_user_info_async(mid)
                user_stat_task = self._get_user_stat_async(mid)
                videos_task = self._get_user_videos_async(mid, page=1, page_size=video_count)
                
                # 并发获取所有数据
                user_info, user_stat, videos = await asyncio.gather(
                    user_info_task,
                    user_stat_task,
                    videos_task,
                    return_exceptions=True
                )
                
                # 处理异常
                if isinstance(user_info, Exception):
                    logger.error(f"获取用户信息异常: {user_info}")
                    user_info = None
                if isinstance(user_stat, Exception):
                    logger.error(f"获取统计数据异常: {user_stat}")
                    user_stat = None
                if isinstance(videos, Exception):
                    logger.error(f"获取视频列表异常: {videos}")
                    videos = None
                
                return user_info, user_stat, videos
            
            user_info, user_stat, videos = asyncio.run(fetch_all())
            
            if not user_info:
                return None
            
            return {
                'user_info': user_info,
                'user_stat': user_stat or {},
                'videos': videos or [],
                'updated_at': datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"获取完整数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None


def format_number(num: int) -> str:
    """
    格式化数字（万、亿）
    
    Args:
        num: 数字
        
    Returns:
        格式化后的字符串
    """
    if num >= 100000000:
        return f"{num / 100000000:.1f}亿"
    elif num >= 10000:
        return f"{num / 10000:.1f}万"
    else:
        return str(num)


def format_timestamp(timestamp: int) -> str:
    """
    格式化时间戳为可读时间（中国时区）
    
    Args:
        timestamp: Unix时间戳（秒）
        
    Returns:
        格式化后的时间字符串
    """
    try:
        from datetime import timezone, timedelta
        # 中国时区 UTC+8
        tz = timezone(timedelta(hours=8))
        dt = datetime.fromtimestamp(timestamp, tz=tz)
        return dt.strftime('%Y-%m-%d %H:%M')
    except Exception as e:
        # 如果时区转换失败，使用本地时间
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return ''




