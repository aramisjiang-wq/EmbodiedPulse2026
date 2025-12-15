#!/usr/bin/env python3
"""
Bilibili API客户端
使用 bilibili-api-python 库获取UP主信息和视频列表
"""
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import os
import requests

# 尝试加载.env文件
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger = logging.getLogger(__name__)
        logger.debug(f"已加载 .env 文件: {env_path}")
except ImportError:
    pass  # python-dotenv未安装，跳过
except Exception as e:
    pass  # 加载失败，跳过

try:
    from bilibili_api import user, Credential
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
        # 读取 Cookie/SESSDATA，提高通过风控概率
        sessdata = os.getenv("BILI_SESSDATA")
        bili_jct = os.getenv("BILI_JCT")
        buvid3 = os.getenv("BILI_BUVID3")
        dedeuserid = os.getenv("BILI_DEDEUSERID")
        self.credential = None
        if sessdata:
            try:
                self.credential = Credential(
                    sessdata=sessdata,
                    bili_jct=bili_jct,
                    buvid3=buvid3,
                    dedeuserid=dedeuserid
                )
                logger.info("已加载 B 站凭证，用于减轻 412 风控")
            except Exception as e:
                logger.warning(f"加载 B 站凭证失败: {e}")

    def _request_json(self, url: str, params: Optional[Dict] = None, timeout: int = 10, retry: int = 2) -> Optional[Dict]:
        """
        直接通过 HTTP 请求获取 JSON（用于被风控 412 时的兜底）
        可配置环境变量 BILI_COOKIE / BILI_SESSDATA 提升成功率。
        添加重试机制和延迟，避免触发风控。
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36",
            "Referer": "https://www.bilibili.com/",
        }
        cookie = os.getenv("BILI_COOKIE") or os.getenv("BILI_SESSDATA")
        if cookie:
            headers["Cookie"] = cookie
        
        import time
        for attempt in range(retry + 1):
            try:
                # 如果不是第一次请求，添加延迟
                if attempt > 0:
                    delay = 2.0 * attempt  # 2秒、4秒...
                    logger.debug(f"HTTP请求重试 {attempt+1}/{retry+1}，等待 {delay}秒...")
                    time.sleep(delay)
                
                resp = requests.get(url, params=params, headers=headers, timeout=timeout)
                
                # 检查是否是412错误
                if resp.status_code == 412:
                    logger.warning(f"检测到412风控，等待更长时间后重试...")
                    if attempt < retry:
                        time.sleep(5.0 * (attempt + 1))  # 5秒、10秒...
                        continue
                    else:
                        logger.error(f"HTTP请求被412风控拦截: {url}")
                        return None
                
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict) and data.get("code") == 0:
                    return data
                else:
                    logger.debug(f"API返回错误码: {data.get('code')}, 消息: {data.get('message')}")
            except requests.exceptions.RequestException as e:
                logger.debug(f"HTTP 兜底请求失败 {url} (尝试 {attempt+1}/{retry+1}): {e}")
                if attempt < retry:
                    continue
            except Exception as e:
                logger.debug(f"HTTP 兜底请求异常 {url}: {e}")
                if attempt < retry:
                    continue
        
        return None

    def _fallback_user_info(self, mid: int) -> Optional[Dict]:
        """风控触发时，通过公开接口兜底获取用户信息"""
        url = "https://api.bilibili.com/x/web-interface/card"
        data = self._request_json(url, params={"mid": mid})
        if not data:
            return None
        card = (data.get("data") or {}).get("card", {})
        return {
            'mid': card.get('mid'),
            'name': card.get('name', ''),
            'face': card.get('face', ''),
            'sign': card.get('sign', ''),
            'level': card.get('level_info', {}).get('current_level', 0),
            'fans': card.get('fans', 0),
            'friend': card.get('friend', 0),
        }

    def _fallback_user_videos(self, mid: int, page_size: int = 20) -> List[Dict]:
        """风控触发时，通过公开接口兜底获取视频列表（按发布时间排序）"""
        url = "https://api.bilibili.com/x/space/arc/search"
        data = self._request_json(url, params={"mid": mid, "ps": page_size, "pn": 1, "order": "pubdate"})
        videos: List[Dict] = []
        if not data:
            return videos
        vlist = (data.get("data") or {}).get("list", {}).get("vlist", []) or []
        import time
        current_timestamp = int(time.time())
        for video in vlist:
            pubdate = video.get('created', 0) or video.get('pubdate', 0)
            if pubdate > current_timestamp * 10:
                pubdate = pubdate // 1000
            videos.append({
                'bvid': video.get('bvid', ''),
                'aid': video.get('aid', 0),
                'title': video.get('title', ''),
                'pic': video.get('pic', ''),
                'play': video.get('play', 0),
                'video_review': video.get('video_review', 0),
                'favorites': video.get('favorites', 0),
                'pubdate': pubdate,
                'description': video.get('description', ''),
                'length': video.get('length', ''),
            })
        return videos

    def _get_upstat(self, mid: int) -> Optional[Dict]:
        """通过公开API获取UP主统计数据（包括获赞数）"""
        url = "https://api.bilibili.com/x/space/upstat"
        data = self._request_json(url, params={"mid": mid})
        if not data:
            return None
        stat_data = data.get("data", {})
        return {
            'archive': stat_data.get('archive', {}),
            'article': stat_data.get('article', {}),
            'likes': stat_data.get('likes', 0),  # 获赞数
        }

    def _fallback_user_stat(self, mid: int, videos: List[Dict]) -> Dict:
        """风控触发时，基于兜底接口获取统计数据"""
        likes = 0
        # 优先使用upstat接口获取获赞数
        try:
            upstat = self._get_upstat(mid)
            if upstat:
                likes = upstat.get('likes', 0)
        except Exception as e:
            logger.debug(f"获取upstat数据失败: {e}")
        
        # 如果upstat失败，尝试从card接口获取
        if not likes:
            try:
                info = self._fallback_user_info(mid) or {}
                likes = info.get('likes', 0) or 0
            except Exception as e:
                logger.debug(f"从card接口获取likes失败: {e}")
        
        total_views = sum(v.get('play', 0) or 0 for v in videos)
        return {
            'videos': total_views,
            'likes': likes,
            'views': total_views,
        }
    
    async def _get_user_info_async(self, mid: int) -> Optional[Dict]:
        """
        异步获取UP主基本信息
        
        Args:
            mid: UP主的UID（用户ID）
            
        Returns:
            UP主信息字典
        """
        try:
            u = user.User(uid=mid, credential=self.credential)
            info = await u.get_user_info()
            
            result = {
                'mid': info.get('mid'),
                'name': info.get('name', ''),
                'face': info.get('face', ''),
                'sign': info.get('sign', ''),
                'level': info.get('level_info', {}).get('current_level', 0),
                'fans': info.get('fans', 0),
                'friend': info.get('friend', 0),  # 关注数
            }
            
            # 如果粉丝数为0，尝试使用fallback方法获取（官方SDK可能返回0）
            if result.get('fans', 0) == 0:
                try:
                    fallback_info = self._fallback_user_info(mid)
                    if fallback_info and fallback_info.get('fans', 0) > 0:
                        result['fans'] = fallback_info.get('fans', 0)
                        result['friend'] = fallback_info.get('friend', result.get('friend', 0))
                        logger.debug(f"使用fallback方法获取到粉丝数: {result['fans']}")
                except Exception as fallback_error:
                    logger.debug(f"fallback获取用户信息失败: {fallback_error}")
            
            return result
        except Exception as e:
            logger.error(f"获取UP主信息失败: {e}")
            # 如果官方SDK失败，尝试使用fallback方法
            try:
                return self._fallback_user_info(mid)
            except Exception as fallback_error:
                logger.error(f"fallback获取用户信息也失败: {fallback_error}")
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
            u = user.User(uid=mid, credential=self.credential)
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
            u = user.User(uid=mid, credential=self.credential)
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
            
            # 如果统计信息获取失败，尝试使用公开API获取获赞数
            if not likes:
                try:
                    upstat = self._get_upstat(mid)
                    if upstat:
                        likes = upstat.get('likes', 0)
                except Exception as upstat_error:
                    logger.debug(f"通过upstat接口获取获赞数失败: {upstat_error}")
            
            # 如果还是获取不到，尝试从用户信息中获取
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
            # 如果获取统计失败，尝试使用公开API兜底
            try:
                upstat = self._get_upstat(mid)
                if upstat:
                    return {
                        'videos': 0,
                        'likes': upstat.get('likes', 0),
                        'views': 0,
                    }
            except Exception as fallback_error:
                logger.debug(f"兜底获取统计数据失败: {fallback_error}")
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
        # 兜底：用公开接口+视频列表估算
        videos = self._fallback_user_videos(mid, page_size=10)
        return self._fallback_user_stat(mid, videos)
    
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
            # 使用异步方式获取数据，但添加小延迟避免并发请求过多
            async def fetch_all():
                import asyncio
                # 先获取用户信息
                user_info = await self._get_user_info_async(mid)
                await asyncio.sleep(0.5)  # 延迟500ms避免频繁请求
                
                # 再获取统计和视频（稍微错开）
                user_stat_task = self._get_user_stat_async(mid)
                await asyncio.sleep(0.3)  # 再延迟300ms
                videos_task = self._get_user_videos_async(mid, page=1, page_size=video_count)
                
                # 并发获取统计和视频数据
                user_stat, videos = await asyncio.gather(
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
            
            # 兜底补全（解决 412 风控导致的数据缺失）
            import time
            if not user_info:
                logger.info(f"使用fallback方法获取用户信息 (UID: {mid})")
                time.sleep(1.0)  # 延迟1秒避免频繁请求
                user_info = self._fallback_user_info(mid)
            elif user_info and user_info.get('fans', 0) == 0:
                # 如果粉丝数为0，尝试使用fallback方法获取（官方SDK可能返回0）
                try:
                    logger.info(f"粉丝数为0，使用fallback方法更新 (UID: {mid})")
                    time.sleep(1.0)  # 延迟1秒避免频繁请求
                    fallback_info = self._fallback_user_info(mid)
                    if fallback_info and fallback_info.get('fans', 0) > 0:
                        user_info['fans'] = fallback_info.get('fans', 0)
                        user_info['friend'] = fallback_info.get('friend', user_info.get('friend', 0))
                        logger.info(f"使用fallback方法更新粉丝数: {user_info['fans']}")
                except Exception as e:
                    logger.debug(f"fallback更新粉丝数失败: {e}")
            
            if not videos:
                logger.info(f"使用fallback方法获取视频列表 (UID: {mid})")
                time.sleep(1.5)  # 延迟1.5秒避免频繁请求
                videos = self._fallback_user_videos(mid, page_size=video_count)
            if not user_stat:
                logger.info(f"使用fallback方法获取统计数据 (UID: {mid})")
                time.sleep(1.0)  # 延迟1秒避免频繁请求
                user_stat = self._fallback_user_stat(mid, videos or [])
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




