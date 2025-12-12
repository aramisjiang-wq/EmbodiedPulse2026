"""
Flask Web Application for Embodied Pulse
"""
from flask import Flask, render_template, jsonify, request
import json
import os
import threading
import logging
from datetime import datetime
from daily_arxiv import load_config, demo, get_daily_papers
from models import init_db, get_session, Paper
from sqlalchemy import func, or_, and_, desc
from jobs_models import get_jobs_session, Job
from datasets_models import get_datasets_session, Dataset
from news_models import get_news_session, News
from bilibili_client import BilibiliClient, format_number, format_timestamp

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# 确保目录存在
if not os.path.exists(TEMPLATE_DIR):
    raise FileNotFoundError(f"模板目录不存在: {TEMPLATE_DIR}\n当前文件路径: {__file__}\nBASE_DIR: {BASE_DIR}")
if not os.path.exists(STATIC_DIR):
    raise FileNotFoundError(f"静态文件目录不存在: {STATIC_DIR}\n当前文件路径: {__file__}\nBASE_DIR: {BASE_DIR}")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 记录路径信息（用于调试）
logger.info(f"Flask应用初始化 - 文件路径: {__file__}")
logger.info(f"BASE_DIR: {BASE_DIR}")
logger.info(f"TEMPLATE_DIR: {TEMPLATE_DIR}")
logger.info(f"STATIC_DIR: {STATIC_DIR}")
logger.info(f"模板目录存在: {os.path.exists(TEMPLATE_DIR)}")
logger.info(f"静态目录存在: {os.path.exists(STATIC_DIR)}")

app = Flask(__name__, 
            template_folder=TEMPLATE_DIR,
            static_folder=STATIC_DIR)
app.config['JSON_AS_ASCII'] = False  # 支持中文

# 验证模板目录配置
if not os.path.exists(app.template_folder):
    logger.error(f"Flask模板目录不存在: {app.template_folder}")
    raise FileNotFoundError(f"Flask模板目录不存在: {app.template_folder}")

# 全局变量存储抓取状态
fetch_status = {
    'running': False,
    'progress': 0,
    'total': 0,
    'current_keyword': '',
    'message': '',
    'last_update': None
}
# 线程锁，保护fetch_status的更新
fetch_status_lock = threading.Lock()

# 全局变量存储新闻抓取状态
news_fetch_status = {
    'running': False,
    'progress': 0,
    'total': 0,
    'message': '',
    'last_update': None
}
# 线程锁，保护news_fetch_status的更新
news_fetch_status_lock = threading.Lock()

# Bilibili数据缓存
bilibili_cache = {
    'data': None,
    'expires_at': None
}
bilibili_cache_lock = threading.Lock()
BILIBILI_CACHE_DURATION = 600  # 缓存10分钟（600秒）

# 全局定时任务调度器（用于Gunicorn启动时自动启动）
scheduler = None

# 初始化定时任务调度器的函数（适用于Gunicorn等生产环境）
def init_scheduler():
    """初始化定时任务调度器（适用于Gunicorn等生产环境）"""
    global scheduler
    if scheduler is not None:
        logger.info("定时任务调度器已存在，跳过重复初始化")
        return scheduler  # 已经启动，直接返回
    
    auto_fetch_enabled = os.getenv('AUTO_FETCH_ENABLED', 'false').lower() == 'true'
    if auto_fetch_enabled:
        logger.info("=" * 60)
        logger.info("检测到 AUTO_FETCH_ENABLED=true，正在启动定时任务...")
        logger.info("=" * 60)
        scheduler = start_scheduler()
        if scheduler:
            logger.info("✅ 定时任务调度器已启动（适用于Gunicorn等生产环境）")
            logger.info("=" * 60)
        else:
            logger.warning("⚠️  定时任务调度器启动失败（需要安装 APScheduler）")
        return scheduler
    else:
        logger.info("ℹ️  自动定时抓取未启用（设置 AUTO_FETCH_ENABLED=true 启用）")
        return None

def load_papers_data(json_path='./docs/cv-arxiv-daily.json', use_db=True):
    """加载论文数据（优先使用数据库）"""
    if use_db:
        session = None
        try:
            session = get_session()
            papers = session.query(Paper).all()
            
            # 按类别组织数据
            result = {}
            for paper in papers:
                if paper.category not in result:
                    result[paper.category] = {}
                result[paper.category][paper.id] = paper.to_dict()
            
            return result
        except Exception as e:
            logger.warning(f"从数据库加载失败，尝试使用JSON: {e}")
            # 如果数据库失败，回退到JSON
        finally:
            if session:
                session.close()
    
    # 回退到JSON文件
    try:
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if content:
                    return json.loads(content)
        return {}
    except Exception as e:
        logger.error(f"加载论文数据失败: {e}")
        return {}

def parse_paper_entry(entry_str):
    """解析论文条目字符串"""
    try:
        # 格式: |**日期**|**标题**|作者 Team|[ID](URL)|**[link](code_url)**| 或 |**日期**|**标题**|作者 Team|[ID](URL)|null|
        parts = entry_str.split('|')
        if len(parts) >= 6:
            date = parts[1].replace('**', '').strip()
            title = parts[2].replace('**', '').strip()
            authors = parts[3].replace(' Team', '').strip()
            
            # 提取PDF链接和ID
            pdf_part = parts[4].strip()
            pdf_id = pdf_part.split('](')[0].replace('[', '').strip()
            pdf_url = pdf_part.split('](')[1].replace(')', '').strip() if '](' in pdf_part else ''
            
            # 提取代码链接
            code_part = parts[5].strip()
            code_url = None
            if 'link' in code_part and 'http' in code_part:
                code_url = code_part.split('](')[1].replace(')', '').replace('**', '').strip() if '](' in code_part else None
            
            return {
                'date': date,
                'title': title,
                'authors': authors,
                'pdf_id': pdf_id,
                'pdf_url': pdf_url,
                'code_url': code_url
            }
    except Exception as e:
        logger.error(f"解析论文条目失败: {e}, 条目: {entry_str[:100]}")
    return None

@app.route('/')
def index():
    """主页"""
    # 调试信息：确保模板路径正确
    template_path = os.path.join(app.template_folder, 'index.html')
    if not os.path.exists(template_path):
        error_msg = (
            f"模板文件不存在: {template_path}\n"
            f"Flask模板目录: {app.template_folder}\n"
            f"当前工作目录: {os.getcwd()}\n"
            f"app.py文件路径: {__file__}"
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    logger.debug(f"渲染模板: {template_path}")
    return render_template('index.html')

@app.route('/api/papers')
def get_papers():
    """获取论文列表API（使用数据库）"""
    session = None
    try:
        session = get_session()
        
        # 从数据库查询所有论文
        papers = session.query(Paper).order_by(Paper.publish_date.desc()).all()
        
        # 获取最后更新时间（数据库中最新的updated_at）
        last_update_query = session.query(func.max(Paper.updated_at)).scalar()
        if last_update_query:
            last_update = last_update_query.strftime('%Y-%m-%d %H:%M:%S')
        else:
            last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 计算昨天新创建的论文数量（新规则：今天看昨天的）
        # 规则：使用created_at字段，计算昨天（前一天）00:00:00到23:59:59之间创建的论文
        from datetime import date, timedelta
        today = date.today()
        yesterday = today - timedelta(days=1)
        yesterday_start = datetime.combine(yesterday, datetime.min.time())  # 昨天 00:00:00
        today_start = datetime.combine(today, datetime.min.time())  # 今天 00:00:00
        
        new_papers_count = session.query(Paper).filter(
            Paper.created_at >= yesterday_start,
            Paper.created_at < today_start
        ).count()
        
        logger.info(f"昨天新论文查询: yesterday={yesterday}, yesterday_start={yesterday_start}, today_start={today_start}, new_count={new_papers_count} (使用created_at判断，今天看昨天的新论文)")
        
        # 按类别组织数据
        result = {}
        for paper in papers:
            if paper.category not in result:
                result[paper.category] = []
            result[paper.category].append(paper.to_dict())
        
        # 计算总数
        total_count = len(papers)
        
        return jsonify({
            'success': True,
            'data': result,
            'last_update': last_update,
            'total_count': total_count,
            'new_papers_count': new_papers_count  # 新增论文数量
        })
    except Exception as e:
        logger.error(f"获取论文列表失败: {e}")
        # 如果数据库失败，回退到JSON
        try:
            data = load_papers_data(use_db=False)
            result = {}
            
            for keyword, papers in data.items():
                parsed_papers = []
                for paper_id, paper_entry in papers.items():
                    parsed = parse_paper_entry(paper_entry)
                    if parsed:
                        parsed['id'] = paper_id
                        parsed_papers.append(parsed)
                
                parsed_papers.sort(key=lambda x: x['date'], reverse=True)
                result[keyword] = parsed_papers
            
            # 回退到JSON时，无法计算新论文数量，返回0
            return jsonify({
                'success': True,
                'data': result,
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_count': sum(len(papers) for papers in result.values()),
                'new_papers_count': 0,  # JSON回退时无法计算，返回0
                'warning': '使用JSON文件作为数据源'
            })
        except Exception as e2:
            return jsonify({
                'success': False,
                'error': str(e2)
            }), 500
    finally:
        if session:
            session.close()

@app.route('/api/trends')
def get_trends():
    """获取论文趋势分析数据（近7天/30天）"""
    session = None
    try:
        from datetime import timedelta
        
        session = get_session()
        
        # 获取查询参数
        days = request.args.get('days', type=int, default=30)  # 默认30天
        days = min(max(days, 7), 90)  # 限制在7-90天之间
        
        # 计算起始日期
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 获取所有研究方向
        categories = session.query(Paper.category).distinct().all()
        categories = [cat[0] for cat in categories if cat[0]]  # 过滤None值
        
        # 如果没有类别，返回空数据
        if not categories:
            return jsonify({
                'success': True,
                'days': days,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'trends': {},
                'growth': {},
                'updated_at': datetime.now().isoformat(),
                'message': '暂无论文数据，请先抓取论文'
            })
        
        # 为每个类别生成时间序列数据
        trends_data = {}
        
        for category in categories:
            # 查询该类别在指定时间范围内的论文，按日期分组统计
            # 使用 publish_date 或 created_at 作为时间基准
            daily_counts = {}
            
            # 查询该类别在时间范围内的所有论文
            # 优先使用 publish_date，如果没有则使用 created_at
            papers = session.query(Paper).filter(
                Paper.category == category
            ).filter(
                or_(
                    and_(Paper.publish_date.isnot(None), Paper.publish_date >= start_date, Paper.publish_date <= end_date),
                    and_(Paper.publish_date.is_(None), 
                         func.date(Paper.created_at) >= start_date, 
                         func.date(Paper.created_at) <= end_date)
                )
            ).all()
            
            # 按日期分组统计
            for paper in papers:
                # 优先使用 publish_date，如果没有则使用 created_at 的日期部分
                if paper.publish_date:
                    date_key = paper.publish_date
                elif paper.created_at:
                    date_key = paper.created_at.date()
                else:
                    continue
                
                if start_date <= date_key <= end_date:
                    date_str = date_key.strftime('%Y-%m-%d')
                    daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
            
            # 生成完整的时间序列（包括没有论文的日期）
            date_list = []
            count_list = []
            current_date = start_date
            
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                date_list.append(date_str)
                count_list.append(daily_counts.get(date_str, 0))
                current_date += timedelta(days=1)
            
            trends_data[category] = {
                'dates': date_list,
                'counts': count_list,
                'total': sum(count_list)
            }
        
        # 计算增长最快的方向（最近7天 vs 之前7天）
        growth_analysis = {}
        if days >= 14:
            recent_start = end_date - timedelta(days=7)
            previous_start = end_date - timedelta(days=14)
            
            for category in categories:
                recent_count = trends_data[category]['total'] if category in trends_data else 0
                # 计算最近7天的数量
                recent_papers = session.query(Paper).filter(
                    Paper.category == category
                ).filter(
                    or_(
                        and_(Paper.publish_date.isnot(None), Paper.publish_date >= recent_start, Paper.publish_date <= end_date),
                        and_(Paper.publish_date.is_(None), 
                             func.date(Paper.created_at) >= recent_start, 
                             func.date(Paper.created_at) <= end_date)
                    )
                ).count()
                
                # 计算之前7天的数量
                previous_papers = session.query(Paper).filter(
                    Paper.category == category
                ).filter(
                    or_(
                        and_(Paper.publish_date.isnot(None), Paper.publish_date >= previous_start, Paper.publish_date < recent_start),
                        and_(Paper.publish_date.is_(None), 
                             func.date(Paper.created_at) >= previous_start, 
                             func.date(Paper.created_at) < recent_start)
                    )
                ).count()
                
                if previous_papers > 0:
                    growth_rate = ((recent_papers - previous_papers) / previous_papers) * 100
                elif recent_papers > 0:
                    growth_rate = 100  # 从0增长到有数据
                else:
                    growth_rate = 0
                
                growth_analysis[category] = {
                    'recent': recent_papers,
                    'previous': previous_papers,
                    'growth_rate': round(growth_rate, 1)
                }
        
        return jsonify({
            'success': True,
            'days': days,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'trends': trends_data,
            'growth': growth_analysis,
            'updated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取趋势数据失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if session:
            session.close()

@app.route('/api/stats')
def get_stats():
    """获取统计信息（使用数据库）"""
    session = None
    try:
        session = get_session()
        
        # 按类别统计
        stats_query = session.query(
            Paper.category,
            func.count(Paper.id).label('count')
        ).group_by(Paper.category).all()
        
        stats = {category: count for category, count in stats_query}
        total = session.query(func.count(Paper.id)).scalar() or 0
        
        return jsonify({
            'success': True,
            'stats': stats,
            'total': total
        })
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        # 回退到JSON
        try:
            data = load_papers_data(use_db=False)
            stats = {}
            total = 0
            
            for keyword, papers in data.items():
                count = len(papers)
                stats[keyword] = count
                total += count
            
            return jsonify({
                'success': True,
                'stats': stats,
                'total': total,
                'warning': '使用JSON文件作为数据源'
            })
        except Exception as e2:
            return jsonify({
                'success': False,
                'error': str(e2)
            }), 500
    finally:
        if session:
            session.close()

@app.route('/api/jobs')
def get_jobs():
    """获取招聘信息列表API"""
    session = None
    try:
        session = get_jobs_session()
        
        # 获取查询参数
        limit = request.args.get('limit', type=int, default=20)
        offset = request.args.get('offset', type=int, default=0)
        
        # 查询所有招聘信息
        all_jobs = session.query(Job).all()
        
        # 转换为字典列表
        jobs_list = [job.to_dict() for job in all_jobs]
        
        # 按日期排序（从近到远）
        # update_date格式: "2025.9.8" 或 "2025.10.1"
        def parse_date(date_str):
            """将日期字符串转换为可比较的元组"""
            if not date_str:
                return (0, 0, 0)  # 空日期排最后
            try:
                parts = date_str.split('.')
                if len(parts) == 3:
                    year = int(parts[0])
                    month = int(parts[1])
                    day = int(parts[2])
                    return (year, month, day)
                else:
                    return (0, 0, 0)
            except:
                return (0, 0, 0)
        
        # 按日期从近到远排序（最新的在前）
        jobs_list.sort(key=lambda x: parse_date(x.get('update_date', '')), reverse=True)
        
        # 应用分页
        total_count = len(jobs_list)
        jobs_list = jobs_list[offset:offset + limit]
        
        # 检查是否有今天新增的岗位
        from datetime import date
        today = date.today()
        has_new_today = False
        for job in all_jobs:
            if job.created_at and job.created_at.date() == today:
                has_new_today = True
                break
        
        return jsonify({
            'success': True,
            'jobs': jobs_list,
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_new_today': has_new_today  # 是否有今天新增的岗位
        })
    except Exception as e:
        logger.error(f"获取招聘信息失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if session:
            session.close()

@app.route('/api/datasets')
def get_datasets():
    """获取数据集信息列表API"""
    session = None
    try:
        session = get_datasets_session()
        
        # 获取查询参数
        limit = request.args.get('limit', type=int, default=20)
        offset = request.args.get('offset', type=int, default=0)
        category = request.args.get('category', type=str, default='')
        
        # 构建查询
        query = session.query(Dataset)
        
        # 按类别筛选
        if category:
            query = query.filter(Dataset.category == category)
        
        # 查询数据集信息，按创建时间倒序排列
        datasets = query.order_by(
            desc(Dataset.created_at)
        ).limit(limit).offset(offset).all()
        
        # 转换为字典列表
        datasets_list = [dataset.to_dict() for dataset in datasets]
        
        # 获取总数
        total_count = session.query(Dataset).count()
        
        # 检查是否有今天新增的数据集
        from datetime import date
        today = date.today()
        has_new_today = False
        for dataset in datasets:
            if dataset.created_at and dataset.created_at.date() == today:
                has_new_today = True
                break
        
        return jsonify({
            'success': True,
            'datasets': datasets_list,
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_new_today': has_new_today  # 是否有今天新增的数据集
        })
    except Exception as e:
        logger.error(f"获取数据集信息失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if session:
            session.close()

@app.route('/api/bilibili')
def get_bilibili():
    """获取Bilibili UP主信息和视频列表（带缓存机制）"""
    global bilibili_cache
    
    try:
        # 逐际动力的Bilibili UID
        UP_UID = 1172054289
        
        # 检查缓存
        with bilibili_cache_lock:
            now = datetime.now().timestamp()
            if (bilibili_cache.get('data') is not None and 
                bilibili_cache.get('expires_at') is not None and 
                now < bilibili_cache['expires_at']):
                # 缓存有效，直接返回缓存数据
                logger.info("使用Bilibili缓存数据")
                cached_data = bilibili_cache['data']
                return jsonify(cached_data)
        
        # 缓存无效或不存在，重新获取数据
        logger.info("Bilibili缓存已过期或不存在，重新获取数据")
        client = BilibiliClient()
        
        # 获取完整数据
        data = client.get_all_data(UP_UID, video_count=10)
        
        if not data:
            # 尝试单独获取用户信息，提供更详细的错误信息
            user_info = client.get_user_info(UP_UID, retry=3)  # 增加重试次数
            if not user_info:
                # 如果仍然失败，检查是否有缓存数据可用
                with bilibili_cache_lock:
                    if (bilibili_cache.get('data') is not None and 
                        bilibili_cache.get('expires_at') is not None):
                        # 即使缓存过期，也返回缓存数据（总比没有好）
                        logger.warning("API请求失败，返回过期的缓存数据")
                        return jsonify(bilibili_cache['data'])
                
                # 如果仍然失败，返回一个友好的错误信息，但标记为部分成功，让前端可以显示提示
                error_response = {
                    'success': True,  # 标记为成功，但数据为空
                    'data': {
                        'user_info': {
                            'mid': UP_UID,
                            'name': '逐际动力',
                            'face': '',
                            'sign': 'Bilibili API暂时无法访问，请稍后刷新',
                            'level': 0,
                            'fans': '0',
                            'fans_raw': 0,
                            'friend': '0',
                        },
                        'user_stat': {},
                        'videos': [],
                        'updated_at': datetime.now().isoformat(),
                        'space_url': f"https://space.bilibili.com/{UP_UID}",
                        'error': True,  # 标记为错误状态
                        'error_message': 'Bilibili API频率限制，请稍后重试（已启用缓存机制，10分钟内不会重复请求）'
                    }
                }
                return jsonify(error_response), 200  # 返回200，但包含错误标记
            
            # 如果用户信息获取成功，但其他数据失败，返回部分数据
            return jsonify({
                'success': True,
                'data': {
                    'user_info': {
                        'mid': user_info.get('mid'),
                        'name': user_info.get('name', '逐际动力'),
                        'face': user_info.get('face', ''),
                        'sign': user_info.get('sign', ''),
                        'level': user_info.get('level', 0),
                        'fans': format_number(user_info.get('fans', 0)),
                        'fans_raw': user_info.get('fans', 0),
                        'friend': format_number(user_info.get('friend', 0)),
                    },
                    'user_stat': {},
                    'videos': [],
                    'updated_at': datetime.now().isoformat(),
                    'space_url': f"https://space.bilibili.com/{UP_UID}",
                    'partial': True  # 标记为部分数据
                }
            })
        
        # 格式化数据
        user_info = data.get('user_info', {})
        user_stat = data.get('user_stat', {})
        videos = data.get('videos', [])
        
        # 格式化视频数据并按日期从新到旧排序
        formatted_videos = []
        for video in videos:
            formatted_videos.append({
                'bvid': video.get('bvid', ''),
                'title': video.get('title', ''),
                'pic': video.get('pic', ''),
                'play': format_number(video.get('play', 0)),
                'play_raw': video.get('play', 0),  # 原始数字用于排序
                'favorites': format_number(video.get('favorites', 0)),
                'video_review': format_number(video.get('video_review', 0)),
                'pubdate': format_timestamp(video.get('pubdate', 0)),
                'pubdate_raw': video.get('pubdate', 0),  # 原始时间戳用于排序
                'description': video.get('description', ''),
                'length': video.get('length', ''),
                'url': f"https://www.bilibili.com/video/{video.get('bvid', '')}"
            })
        
        # 按日期从新到旧排序
        formatted_videos.sort(key=lambda x: x.get('pubdate_raw', 0), reverse=True)
        
        response_data = {
            'success': True,
            'data': {
                'user_info': {
                    'mid': user_info.get('mid'),
                    'name': user_info.get('name', '逐际动力'),
                    'face': user_info.get('face', ''),
                    'sign': user_info.get('sign', ''),
                    'level': user_info.get('level', 0),
                    'fans': format_number(user_info.get('fans', 0)),
                    'fans_raw': user_info.get('fans', 0),
                    'friend': format_number(user_info.get('friend', 0)),
                },
                'user_stat': {
                    'videos': format_number(user_stat.get('videos', 0)),
                    'likes': format_number(user_stat.get('likes', 0)),
                    'views': format_number(user_stat.get('views', 0)),
                },
                'videos': formatted_videos,
                'updated_at': data.get('updated_at'),
                'space_url': f"https://space.bilibili.com/{UP_UID}"
            }
        }
        
        # 保存到缓存（只有成功获取数据时才缓存）
        with bilibili_cache_lock:
            bilibili_cache['data'] = response_data
            bilibili_cache['expires_at'] = datetime.now().timestamp() + BILIBILI_CACHE_DURATION
            logger.info(f"Bilibili数据已缓存，有效期至: {datetime.fromtimestamp(bilibili_cache['expires_at'])}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"获取Bilibili数据失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/news')
def get_news():
    """获取新闻信息列表API"""
    session = None
    try:
        session = get_news_session()
        
        # 获取查询参数
        limit = request.args.get('limit', type=int, default=30)  # 默认增加到30条
        offset = request.args.get('offset', type=int, default=0)
        platform = request.args.get('platform', type=str, default='')
        
        # 计算24小时前的时间
        from datetime import datetime, timedelta
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        
        # 构建查询
        query = session.query(News)
        
        # 只显示24小时内的新闻
        # 优先使用published_at，如果没有则使用created_at
        query = query.filter(
            or_(
                and_(News.published_at.isnot(None), News.published_at >= twenty_four_hours_ago),
                and_(News.published_at.is_(None), News.created_at >= twenty_four_hours_ago)
            )
        )
        
        # 按平台筛选
        if platform:
            query = query.filter(News.platform == platform)
        
        # 查询新闻信息，按创建时间倒序排列（最新的新闻在前面）
        # 优先使用created_at（刷新时间），确保显示最新刷新的新闻
        news = query.order_by(
            desc(News.created_at),
            desc(News.published_at)
        ).limit(limit).offset(offset).all()
        
        # 转换为字典列表
        news_list = [item.to_dict() for item in news]
        
        # 获取24小时内的总数
        from datetime import datetime, timedelta
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        total_count = session.query(News).filter(
            or_(
                and_(News.published_at.isnot(None), News.published_at >= twenty_four_hours_ago),
                and_(News.published_at.is_(None), News.created_at >= twenty_four_hours_ago)
            )
        ).count()
        
        return jsonify({
            'success': True,
            'news': news_list,
            'total': total_count,
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        logger.error(f"获取新闻信息失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if session:
            session.close()

# 刷新任务状态（全局变量）
refresh_status = {
    'running': False,
    'papers': {'status': 'idle', 'message': ''},
    'jobs': {'status': 'idle', 'message': ''},
    'news': {'status': 'idle', 'message': ''}
}
refresh_status_lock = threading.Lock()

@app.route('/api/refresh-all', methods=['POST'])
def refresh_all_data():
    """一键刷新所有数据：论文、招聘、新闻（异步执行）"""
    import threading
    from fetch_jobs import fetch_and_save_jobs
    from fetch_news import fetch_and_save_news
    
    global refresh_status
    
    with refresh_status_lock:
        if refresh_status['running']:
            return jsonify({
                'success': True,
                'message': '刷新任务已在运行中',
                'status': refresh_status
            })
        
        refresh_status['running'] = True
        refresh_status['papers'] = {'status': 'pending', 'message': '等待刷新...'}
        refresh_status['jobs'] = {'status': 'pending', 'message': '等待刷新...'}
        refresh_status['news'] = {'status': 'pending', 'message': '等待刷新...'}
    
    def refresh_papers():
        """刷新论文数据 - 使用fetch_new_data.py中的fetch_papers函数"""
        global refresh_status
        try:
            with refresh_status_lock:
                refresh_status['papers'] = {'status': 'running', 'message': '正在刷新论文...'}
            logger.info("=" * 60)
            logger.info("开始刷新论文数据...")
            logger.info("=" * 60)
            
            # 检查必要的模块是否可以导入
            try:
                from fetch_new_data import fetch_papers
                logger.info("论文抓取模块导入成功")
            except ImportError as e:
                raise ImportError(f"无法导入论文抓取模块: {str(e)}，请检查fetch_new_data.py文件是否存在")
            
            # 检查配置文件是否存在
            config_path = 'config.yaml'
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"配置文件不存在: {config_path}")
            logger.info(f"配置文件检查通过: {config_path}")
            
            logger.info("开始执行论文抓取...")
            fetch_papers()
            
            with refresh_status_lock:
                refresh_status['papers'] = {'status': 'success', 'message': '论文刷新完成'}
            logger.info("=" * 60)
            logger.info("论文数据刷新完成")
            logger.info("=" * 60)
        except FileNotFoundError as e:
            error_msg = f"配置文件不存在: {str(e)}"
            with refresh_status_lock:
                refresh_status['papers'] = {'status': 'error', 'message': error_msg}
            logger.error("=" * 60)
            logger.error(f"论文数据刷新失败: {error_msg}")
            logger.error("=" * 60)
            import traceback
            logger.error(traceback.format_exc())
        except ImportError as e:
            error_msg = f"导入模块失败: {str(e)}，请检查依赖是否安装"
            with refresh_status_lock:
                refresh_status['papers'] = {'status': 'error', 'message': error_msg}
            logger.error("=" * 60)
            logger.error(f"论文数据刷新失败: {error_msg}")
            logger.error("=" * 60)
            import traceback
            logger.error(traceback.format_exc())
        except Exception as e:
            error_msg = f"刷新失败: {str(e)}"
            with refresh_status_lock:
                refresh_status['papers'] = {'status': 'error', 'message': error_msg}
            logger.error("=" * 60)
            logger.error(f"论文数据刷新失败: {error_msg}")
            logger.error("=" * 60)
            import traceback
            logger.error(traceback.format_exc())
        finally:
            # 确保在所有情况下都检查并更新running状态
            with refresh_status_lock:
                # 检查所有任务是否都完成
                papers_done = refresh_status.get('papers', {}).get('status', 'idle') in ['success', 'error']
                jobs_done = refresh_status.get('jobs', {}).get('status', 'idle') in ['success', 'error']
                news_done = refresh_status.get('news', {}).get('status', 'idle') in ['success', 'error']
                if papers_done and jobs_done and news_done:
                    refresh_status['running'] = False
    
    def refresh_jobs():
        """刷新招聘数据 - 使用fetch_jobs.py中的fetch_and_save_jobs函数"""
        global refresh_status
        try:
            with refresh_status_lock:
                refresh_status['jobs'] = {'status': 'running', 'message': '正在刷新招聘信息...'}
            logger.info("=" * 60)
            logger.info("开始刷新招聘数据...")
            logger.info("=" * 60)
            
            # 检查必要的模块是否可以导入
            try:
                from fetch_jobs import fetch_and_save_jobs
                logger.info("招聘信息抓取模块导入成功")
            except ImportError as e:
                raise ImportError(f"无法导入招聘信息抓取模块: {str(e)}，请检查fetch_jobs.py文件是否存在")
            
            logger.info("开始执行招聘信息抓取...")
            fetch_and_save_jobs()
            
            with refresh_status_lock:
                refresh_status['jobs'] = {'status': 'success', 'message': '招聘信息刷新完成'}
            logger.info("=" * 60)
            logger.info("招聘数据刷新完成")
            logger.info("=" * 60)
        except ImportError as e:
            error_msg = f"模块导入失败: {str(e)}"
            with refresh_status_lock:
                refresh_status['jobs'] = {'status': 'error', 'message': error_msg}
            logger.error("=" * 60)
            logger.error(f"招聘数据刷新失败: {error_msg}")
            logger.error("=" * 60)
            import traceback
            logger.error(traceback.format_exc())
        except Exception as e:
            error_msg = f"刷新失败: {str(e)}"
            with refresh_status_lock:
                refresh_status['jobs'] = {'status': 'error', 'message': error_msg}
            logger.error("=" * 60)
            logger.error(f"招聘数据刷新失败: {error_msg}")
            logger.error("=" * 60)
            import traceback
            logger.error(traceback.format_exc())
        finally:
            # 确保在所有情况下都检查并更新running状态
            with refresh_status_lock:
                # 检查所有任务是否都完成
                papers_done = refresh_status.get('papers', {}).get('status', 'idle') in ['success', 'error']
                jobs_done = refresh_status.get('jobs', {}).get('status', 'idle') in ['success', 'error']
                news_done = refresh_status.get('news', {}).get('status', 'idle') in ['success', 'error']
                if papers_done and jobs_done and news_done:
                    refresh_status['running'] = False
    
    def refresh_news():
        """刷新新闻数据 - 使用fetch_news.py中的fetch_and_save_news函数"""
        global refresh_status
        try:
            with refresh_status_lock:
                refresh_status['news'] = {'status': 'running', 'message': '正在刷新新闻...'}
            logger.info("=" * 60)
            logger.info("开始刷新新闻数据...")
            logger.info("=" * 60)
            
            # 检查必要的模块是否可以导入
            try:
                from fetch_news import fetch_and_save_news
                logger.info("新闻抓取模块导入成功")
            except ImportError as e:
                raise ImportError(f"无法导入新闻抓取模块: {str(e)}，请检查fetch_news.py文件是否存在")
            
            # 检查数据库连接
            session = None
            try:
                from news_models import init_news_db, get_news_session
                init_news_db()
                session = get_news_session()
                logger.info("新闻数据库连接正常")
            except Exception as e:
                logger.warning(f"新闻数据库初始化警告: {e}")
            finally:
                if session:
                    session.close()
            
            logger.info("开始执行新闻抓取...")
            fetch_and_save_news()
            
            with refresh_status_lock:
                refresh_status['news'] = {'status': 'success', 'message': '新闻刷新完成'}
            logger.info("=" * 60)
            logger.info("新闻数据刷新完成")
            logger.info("=" * 60)
        except ImportError as e:
            error_msg = f"模块导入失败: {str(e)}"
            with refresh_status_lock:
                refresh_status['news'] = {'status': 'error', 'message': error_msg}
            logger.error("=" * 60)
            logger.error(f"新闻数据刷新失败: {error_msg}")
            logger.error("=" * 60)
            import traceback
            logger.error(traceback.format_exc())
        except Exception as e:
            error_msg = f"刷新失败: {str(e)}"
            with refresh_status_lock:
                refresh_status['news'] = {'status': 'error', 'message': error_msg}
            logger.error("=" * 60)
            logger.error(f"新闻数据刷新失败: {error_msg}")
            logger.error("=" * 60)
            import traceback
            logger.error(traceback.format_exc())
        finally:
            # 确保在所有情况下都检查并更新running状态
            with refresh_status_lock:
                # 检查所有任务是否都完成
                papers_done = refresh_status.get('papers', {}).get('status', 'idle') in ['success', 'error']
                jobs_done = refresh_status.get('jobs', {}).get('status', 'idle') in ['success', 'error']
                news_done = refresh_status.get('news', {}).get('status', 'idle') in ['success', 'error']
                if papers_done and jobs_done and news_done:
                    refresh_status['running'] = False
    
    # 在后台线程中执行刷新任务（避免阻塞）
    paper_thread = threading.Thread(target=refresh_papers, daemon=True)
    jobs_thread = threading.Thread(target=refresh_jobs, daemon=True)
    news_thread = threading.Thread(target=refresh_news, daemon=True)
    
    paper_thread.start()
    jobs_thread.start()
    news_thread.start()
    
    # 立即返回，不等待完成
    with refresh_status_lock:
        status_copy = refresh_status.copy()
    
    return jsonify({
        'success': True,
        'message': '刷新任务已启动',
        'status': status_copy
    })

@app.route('/api/refresh-status', methods=['GET'])
def get_refresh_status():
    """获取刷新任务状态"""
    global refresh_status
    with refresh_status_lock:
        status_copy = refresh_status.copy()
        
        # 检查是否所有任务都完成
        # 确保所有任务都有状态，且都不是 'running' 或 'pending'
        papers_done = status_copy.get('papers', {}).get('status', 'idle') in ['success', 'error']
        jobs_done = status_copy.get('jobs', {}).get('status', 'idle') in ['success', 'error']
        news_done = status_copy.get('news', {}).get('status', 'idle') in ['success', 'error']
        
        all_done = papers_done and jobs_done and news_done
        
        if all_done and status_copy.get('running', False):
            # 所有任务完成，重置running状态
            status_copy['running'] = False
            refresh_status['running'] = False  # 同步更新全局状态
            logger.info(f"所有刷新任务完成: papers={status_copy.get('papers', {}).get('status')}, jobs={status_copy.get('jobs', {}).get('status')}, news={status_copy.get('news', {}).get('status')}")
    
    return jsonify(status_copy)

@app.route('/api/fetch-status')
def get_fetch_status():
    """获取论文抓取状态"""
    # 使用锁保护读取
    with fetch_status_lock:
        status_copy = fetch_status.copy()
    # 添加调试日志
    if status_copy.get('running'):
        logger.debug(f"返回抓取状态: {status_copy}")
    return jsonify(status_copy)

@app.route('/api/fetch-news-status')
def get_news_fetch_status():
    """获取新闻抓取状态"""
    # 使用锁保护读取
    with news_fetch_status_lock:
        status_copy = news_fetch_status.copy()
    return jsonify(status_copy)

@app.route('/api/search')
def search_papers():
    """搜索论文"""
    session = None
    try:
        query = request.args.get('q', '').strip()
        category = request.args.get('category', '').strip()
        
        if not query and not category:
            return jsonify({
                'success': False,
                'error': '请提供搜索关键词或类别'
            }), 400
        
        session = get_session()
        
        # 构建查询
        papers_query = session.query(Paper)
        
        # 按类别筛选
        if category:
            papers_query = papers_query.filter(Paper.category == category)
        
        # 按关键词搜索（标题或作者）
        if query:
            papers_query = papers_query.filter(
                or_(
                    Paper.title.contains(query),
                    Paper.authors.contains(query)
                )
            )
        
        # 排序和限制
        papers = papers_query.order_by(Paper.publish_date.desc()).limit(100).all()
        
        result = [paper.to_dict() for paper in papers]
        
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })
    except Exception as e:
        if session:
            session.close()
        logger.error(f"搜索论文失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if session:
            session.close()

@app.route('/api/fetch', methods=['POST'])
def trigger_fetch():
    """触发论文抓取 - 通过命令行执行 python3 fetch_new_data.py --papers"""
    global fetch_status
    
    with fetch_status_lock:
        if fetch_status['running']:
            return jsonify({
                'success': False,
                'message': '抓取任务正在运行中，请稍候...'
            }), 400
    
    # 简化版：不需要配置参数，直接执行脚本
    # 脚本内部已配置好所有参数（max_results=100, days_back=14等）
    
    def fetch_task():
        """后台抓取任务 - 通过命令行执行 python3 fetch_new_data.py --papers"""
        global fetch_status
        import subprocess
        import sys
        
        try:
            with fetch_status_lock:
                fetch_status['running'] = True
                fetch_status['message'] = '开始抓取论文...'
                fetch_status['progress'] = 0
                fetch_status['total'] = 0
                fetch_status['current_keyword'] = ''
                fetch_status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info("=" * 60)
            logger.info("开始抓取论文数据（通过/api/fetch接口）...")
            logger.info("=" * 60)
            
            # 获取脚本路径
            script_path = os.path.join(os.path.dirname(__file__), 'fetch_new_data.py')
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"脚本文件不存在: {script_path}")
            
            logger.info(f"执行命令: python3 {script_path} --papers")
            
            # 通过subprocess执行命令，实时捕获输出
            process = subprocess.Popen(
                [sys.executable, script_path, '--papers'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # 行缓冲
                universal_newlines=True
            )
            
            # 实时读取输出并更新进度
            current_keyword = ''
            total_keywords = 0
            current_progress = 0
            
            for line in process.stdout:
                line = line.strip()
                if line:
                    logger.info(f"抓取输出: {line}")
                    
                    # 解析输出，提取进度信息
                    # 例如："正在抓取 Perception (1/9)..." 或 "Keyword: Perception (1/9)"
                    if '正在抓取' in line or 'Keyword:' in line:
                        # 尝试提取类别和进度
                        import re
                        # 匹配 "正在抓取 {类别} ({进度}/{总数})..."
                        match = re.search(r'正在抓取\s+(\w+)\s+\((\d+)/(\d+)\)', line)
                        if not match:
                            match = re.search(r'Keyword:\s+(\w+)\s+\((\d+)/(\d+)\)', line)
                        
                        if match:
                            keyword = match.group(1)
                            progress = int(match.group(2))
                            total = int(match.group(3))
                            
                            with fetch_status_lock:
                                fetch_status['current_keyword'] = keyword
                                fetch_status['message'] = f'正在抓取 {keyword} ({progress}/{total})...'
                                fetch_status['progress'] = progress
                                fetch_status['total'] = total
                            current_keyword = keyword
                            current_progress = progress
                            total_keywords = total
                    
                    # 如果检测到"GET daily papers begin"，说明开始抓取
                    if 'GET daily papers begin' in line:
                        with fetch_status_lock:
                            fetch_status['message'] = '准备开始抓取论文...'
                    
                    # 如果检测到完成信息
                    if '论文抓取完成' in line or 'GET daily papers end' in line:
                        with fetch_status_lock:
                            fetch_status['message'] = '抓取完成！'
                            if total_keywords > 0:
                                fetch_status['progress'] = total_keywords
            
            # 等待进程完成
            return_code = process.wait()
            
            if return_code != 0:
                raise Exception(f"抓取脚本执行失败，返回码: {return_code}")
            
            with fetch_status_lock:
                fetch_status['message'] = '抓取完成！'
                if total_keywords > 0:
                    fetch_status['progress'] = total_keywords
                fetch_status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info("=" * 60)
            logger.info("论文数据抓取完成")
            logger.info("=" * 60)
            
        except FileNotFoundError as e:
            error_msg = f"配置文件不存在: {str(e)}"
            logger.error("=" * 60)
            logger.error(f"论文数据抓取失败: {error_msg}")
            logger.error("=" * 60)
            import traceback
            logger.error(traceback.format_exc())
            with fetch_status_lock:
                fetch_status['message'] = error_msg
                fetch_status['running'] = False
                fetch_status['progress'] = 0
                fetch_status['current_keyword'] = ''
                fetch_status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        except ImportError as e:
            error_msg = f"导入模块失败: {str(e)}，请检查依赖是否安装"
            logger.error("=" * 60)
            logger.error(f"论文数据抓取失败: {error_msg}")
            logger.error("=" * 60)
            import traceback
            logger.error(traceback.format_exc())
            with fetch_status_lock:
                fetch_status['message'] = error_msg
                fetch_status['running'] = False
                fetch_status['progress'] = 0
                fetch_status['current_keyword'] = ''
                fetch_status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            error_msg = f"抓取失败: {str(e)}"
            logger.error("=" * 60)
            logger.error(f"论文数据抓取失败: {error_msg}")
            logger.error("=" * 60)
            import traceback
            logger.error(traceback.format_exc())
            with fetch_status_lock:
                fetch_status['message'] = error_msg
                fetch_status['running'] = False
                fetch_status['progress'] = 0
                fetch_status['current_keyword'] = ''
                fetch_status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        finally:
            with fetch_status_lock:
                if fetch_status['running']:  # 如果还没被设置为False
                    fetch_status['running'] = False
                    fetch_status['progress'] = 0
                    fetch_status['current_keyword'] = ''
                    if not fetch_status.get('last_update'):
                        fetch_status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 在后台线程中运行
    thread = threading.Thread(target=fetch_task)
    thread.daemon = True
    thread.start()
    
    # 立即返回，不等待完成
    with fetch_status_lock:
        status_copy = fetch_status.copy()
    
    return jsonify({
        'success': True,
        'message': '抓取任务已启动',
        'status': status_copy
    })

@app.route('/api/fetch-news', methods=['POST'])
def trigger_fetch_news():
    """触发新闻抓取 - 通过命令行执行 python3 fetch_new_data.py --news"""
    global news_fetch_status
    
    with news_fetch_status_lock:
        if news_fetch_status['running']:
            return jsonify({
                'success': False,
                'message': '新闻抓取任务正在运行中，请稍候...'
            }), 400
    
    def fetch_news_task():
        """后台新闻抓取任务 - 通过命令行执行 python3 fetch_new_data.py --news"""
        global news_fetch_status
        import subprocess
        import sys
        
        try:
            with news_fetch_status_lock:
                news_fetch_status['running'] = True
                news_fetch_status['message'] = '开始抓取新闻...'
                news_fetch_status['progress'] = 0
                news_fetch_status['total'] = 1  # 新闻抓取是单步任务
                news_fetch_status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info("=" * 60)
            logger.info("开始抓取新闻数据（通过/api/fetch-news接口）...")
            logger.info("=" * 60)
            
            # 获取脚本路径
            script_path = os.path.join(os.path.dirname(__file__), 'fetch_new_data.py')
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"脚本文件不存在: {script_path}")
            
            # 使用字符串命令执行：python3 fetch_new_data.py --news
            command = f"python3 {script_path} --news"
            logger.info(f"执行命令: {command}")
            
            # 通过subprocess执行命令，实时捕获输出
            process = subprocess.Popen(
                command,
                shell=True,  # 使用shell执行字符串命令
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # 行缓冲
                universal_newlines=True
            )
            
            # 实时读取输出并更新进度
            for line in process.stdout:
                line = line.strip()
                if line:
                    logger.info(f"新闻抓取输出: {line}")
                    
                    # 更新状态消息
                    if '开始抓取新新闻' in line or '开始抓取' in line:
                        with news_fetch_status_lock:
                            news_fetch_status['message'] = '正在抓取新闻...'
                            news_fetch_status['progress'] = 0
                    
                    # 如果检测到完成信息
                    if '新闻抓取完成' in line or '✅' in line:
                        with news_fetch_status_lock:
                            news_fetch_status['message'] = '新闻抓取完成！'
                            news_fetch_status['progress'] = 1
            
            # 等待进程完成
            return_code = process.wait()
            
            if return_code != 0:
                raise Exception(f"新闻抓取脚本执行失败，返回码: {return_code}")
            
            with news_fetch_status_lock:
                news_fetch_status['message'] = '新闻抓取完成！'
                news_fetch_status['progress'] = 1
                news_fetch_status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info("=" * 60)
            logger.info("新闻数据抓取完成")
            logger.info("=" * 60)
            
        except FileNotFoundError as e:
            error_msg = f"脚本文件不存在: {str(e)}"
            logger.error("=" * 60)
            logger.error(f"新闻数据抓取失败: {error_msg}")
            logger.error("=" * 60)
            import traceback
            logger.error(traceback.format_exc())
            with news_fetch_status_lock:
                news_fetch_status['message'] = error_msg
                news_fetch_status['running'] = False
                news_fetch_status['progress'] = 0
                news_fetch_status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            error_msg = f"抓取失败: {str(e)}"
            logger.error("=" * 60)
            logger.error(f"新闻数据抓取失败: {error_msg}")
            logger.error("=" * 60)
            import traceback
            logger.error(traceback.format_exc())
            with news_fetch_status_lock:
                news_fetch_status['message'] = error_msg
                news_fetch_status['running'] = False
                news_fetch_status['progress'] = 0
                news_fetch_status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        finally:
            with news_fetch_status_lock:
                if news_fetch_status['running']:  # 如果还没被设置为False
                    news_fetch_status['running'] = False
                    news_fetch_status['progress'] = 0
                    if not news_fetch_status.get('last_update'):
                        news_fetch_status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 在后台线程中运行
    thread = threading.Thread(target=fetch_news_task)
    thread.daemon = True
    thread.start()
    
    # 立即返回，不等待完成
    with news_fetch_status_lock:
        status_copy = news_fetch_status.copy()
    
    return jsonify({
        'success': True,
        'message': '新闻抓取任务已启动',
        'status': status_copy
    })

def start_scheduler():
    """启动定时任务调度器"""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        scheduler = BackgroundScheduler()
        
        def scheduled_fetch():
            """定时抓取论文任务 - 使用fetch_new_data.fetch_papers()函数"""
            global fetch_status
            if fetch_status['running']:
                logger.info("定时抓取任务跳过：已有任务正在运行")
                return
            
            try:
                logger.info("=" * 60)
                logger.info("开始执行定时论文抓取任务...")
                logger.info("=" * 60)
                
                # 使用统一的函数调用方式（与手动刷新一致）
                from fetch_new_data import fetch_papers
                fetch_papers()
                
                logger.info("=" * 60)
                logger.info("定时论文抓取任务完成")
                logger.info("=" * 60)
            except Exception as e:
                logger.error("=" * 60)
                logger.error(f"定时论文抓取任务失败: {e}")
                logger.error("=" * 60)
                import traceback
                logger.error(traceback.format_exc())
        
        def scheduled_fetch_jobs():
            """定时抓取招聘信息任务"""
            try:
                logger.info("开始执行定时招聘信息抓取任务...")
                from fetch_jobs import fetch_and_save_jobs
                fetch_and_save_jobs()
                logger.info("定时招聘信息抓取任务完成")
            except Exception as e:
                logger.error(f"定时招聘信息抓取任务失败: {e}")
        
        # 配置论文抓取定时任务（每小时执行一次）
        # 支持通过环境变量自定义，格式：用分号分隔多个cron表达式，如 "0 * * * *"
        # 如果环境变量未设置，默认每小时执行一次
        schedule_cron = os.getenv('AUTO_FETCH_SCHEDULE', '0 * * * *')  # 默认每小时整点执行
        
        # 解析 cron 表达式（支持多个，用分号分隔）
        if schedule_cron:
            cron_list = schedule_cron.split(';')
            for idx, cron_expr in enumerate(cron_list):
                cron_expr = cron_expr.strip()
                if not cron_expr:
                    continue
                parts = cron_expr.split()
                if len(parts) == 5:
                    minute, hour, day, month, weekday = parts
                    job_id = f'hourly_fetch_papers_{idx}'
                    job_name = f'每小时论文抓取_{idx+1}'
                    scheduler.add_job(
                        scheduled_fetch,
                        trigger=CronTrigger(
                            minute=minute,
                            hour=hour,
                            day=day,
                            month=month,
                            day_of_week=weekday
                        ),
                        id=job_id,
                        name=job_name,
                        replace_existing=True
                    )
                    logger.info(f"定时任务已配置 ({job_name}): {cron_expr}")
        
        # 配置招聘信息抓取定时任务（使用cron表达式，可选）
        try:
            # 支持通过环境变量自定义招聘信息抓取时间（cron表达式）
            # 如果未设置，默认每小时整点执行
            jobs_schedule_cron = os.getenv('AUTO_FETCH_JOBS_SCHEDULE', os.getenv('AUTO_FETCH_SCHEDULE', '0 * * * *'))
            
            # 解析 cron 表达式（支持多个，用分号分隔）
            if jobs_schedule_cron:
                cron_list = jobs_schedule_cron.split(';')
                for idx, cron_expr in enumerate(cron_list):
                    cron_expr = cron_expr.strip()
                    if not cron_expr:
                        continue
                    parts = cron_expr.split()
                    if len(parts) == 5:
                        minute, hour, day, month, weekday = parts
                        job_id = f'hourly_fetch_jobs_{idx}'
                        job_name = f'招聘信息抓取_{idx+1}'
                        scheduler.add_job(
                            scheduled_fetch_jobs,
                            trigger=CronTrigger(
                                minute=minute,
                                hour=hour,
                                day=day,
                                month=month,
                                day_of_week=weekday
                            ),
                            id=job_id,
                            name=job_name,
                            replace_existing=True
                        )
                        logger.info(f"招聘信息抓取定时任务已配置 ({job_name}): {cron_expr}")
        except Exception as e:
            logger.warning(f"配置招聘信息抓取定时任务失败: {e}")
            import traceback
            logger.warning(traceback.format_exc())
        
        # 配置新闻信息抓取定时任务（使用cron表达式）
        try:
            def scheduled_fetch_news():
                """定时抓取新闻信息任务"""
                try:
                    logger.info("=" * 60)
                    logger.info("开始执行定时新闻信息抓取任务...")
                    logger.info("=" * 60)
                    from fetch_news import fetch_and_save_news
                    fetch_and_save_news()
                    logger.info("=" * 60)
                    logger.info("定时新闻信息抓取任务完成")
                    logger.info("=" * 60)
                except Exception as e:
                    logger.error("=" * 60)
                    logger.error(f"定时新闻信息抓取任务失败: {e}")
                    logger.error("=" * 60)
                    import traceback
                    logger.error(traceback.format_exc())
            
            # 支持通过环境变量自定义新闻抓取的cron表达式
            # 格式：分钟 小时 日 月 星期，如 "0 * * * *" 表示每小时整点执行
            # 如果环境变量未设置，默认每小时整点执行
            news_schedule_cron = os.getenv('AUTO_FETCH_NEWS_SCHEDULE', '0 * * * *')  # 默认每小时整点执行
            
            # 解析 cron 表达式（支持多个，用分号分隔）
            if news_schedule_cron:
                cron_list = news_schedule_cron.split(';')
                for idx, cron_expr in enumerate(cron_list):
                    cron_expr = cron_expr.strip()
                    if not cron_expr:
                        continue
                    parts = cron_expr.split()
                    if len(parts) == 5:
                        minute, hour, day, month, weekday = parts
                        job_id = f'hourly_fetch_news_{idx}'
                        job_name = f'新闻信息抓取_{idx+1}'
                        scheduler.add_job(
                            scheduled_fetch_news,
                            trigger=CronTrigger(
                                minute=minute,
                                hour=hour,
                                day=day,
                                month=month,
                                day_of_week=weekday
                            ),
                            id=job_id,
                            name=job_name,
                            replace_existing=True
                        )
                        logger.info(f"新闻信息抓取定时任务已配置 ({job_name}): {cron_expr}")
        except Exception as e:
            logger.warning(f"配置新闻信息抓取定时任务失败: {e}")
            import traceback
            logger.warning(traceback.format_exc())
        
        # 配置Semantic Scholar数据更新定时任务（每天凌晨3点执行）
        try:
            def scheduled_update_semantic_scholar():
                """定时更新Semantic Scholar数据任务"""
                try:
                    logger.info("开始执行定时Semantic Scholar数据更新任务...")
                    from update_semantic_scholar_data import update_all_papers
                    # 每次更新100篇论文（避免一次性更新太多导致API限制）
                    # 只更新没有Semantic Scholar数据的论文
                    update_all_papers(limit=100, skip_existing=True)
                    logger.info("定时Semantic Scholar数据更新任务完成")
                except Exception as e:
                    logger.error(f"定时Semantic Scholar数据更新任务失败: {e}")
            
            # 每天凌晨3点执行一次（避免与论文抓取任务冲突）
            # 可以通过环境变量 SEMANTIC_UPDATE_LIMIT 自定义每次更新的数量（默认200篇）
            update_limit = int(os.getenv('SEMANTIC_UPDATE_LIMIT', 200))
            
            # 修改函数以使用配置的limit
            def scheduled_update_semantic_scholar_with_limit():
                """定时更新Semantic Scholar数据任务（带配置的limit）"""
                try:
                    logger.info(f"开始执行定时Semantic Scholar数据更新任务（每次{update_limit}篇）...")
                    from update_semantic_scholar_data import update_all_papers
                    # 每次更新指定数量的论文（避免一次性更新太多导致API限制）
                    # 只更新没有Semantic Scholar数据的论文
                    update_all_papers(limit=update_limit, skip_existing=True)
                    logger.info("定时Semantic Scholar数据更新任务完成")
                except Exception as e:
                    logger.error(f"定时Semantic Scholar数据更新任务失败: {e}")
            
            scheduler.add_job(
                scheduled_update_semantic_scholar_with_limit,
                trigger=CronTrigger(hour=3, minute=0),
                id='daily_update_semantic_scholar',
                name='每天Semantic Scholar数据更新',
                replace_existing=True
            )
            logger.info(f"Semantic Scholar数据更新定时任务已配置: 每天凌晨3点执行，每次更新{update_limit}篇")
        except Exception as e:
            logger.warning(f"配置Semantic Scholar数据更新定时任务失败: {e}")
        
        scheduler.start()
        return scheduler
    except ImportError:
        logger.warning("APScheduler 未安装，定时任务功能不可用")
        logger.warning("安装命令: pip install apscheduler")
        return None
    except Exception as e:
        logger.error(f"启动定时任务失败: {e}")
        return None

if __name__ == '__main__':
    # 确保数据库已初始化
    try:
        init_db()
        print("=" * 50)
        print("Robotics ArXiv Daily Web 应用")
        print("=" * 50)
        port = int(os.getenv('PORT', 5001))
        print(f"访问地址: http://localhost:{port}")
        
        # 启动定时任务（如果启用）
        auto_fetch_enabled = os.getenv('AUTO_FETCH_ENABLED', 'false').lower() == 'true'
        if auto_fetch_enabled:
            scheduler = start_scheduler()
            if scheduler:
                print("✅ 自动定时抓取已启用")
            else:
                print("⚠️  自动定时抓取未启用（需要安装 APScheduler）")
        else:
            print("ℹ️  自动定时抓取未启用（设置 AUTO_FETCH_ENABLED=true 启用）")
        
        print("按 Ctrl+C 停止服务器")
        print("=" * 50)
    except Exception as e:
        print(f"数据库初始化警告: {e}")
        print("将使用 JSON 文件作为数据源")
    
    port = int(os.getenv('PORT', 5001))  # 使用5001避免与AirPlay冲突
    print(f"服务器运行在: http://localhost:{port}")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=port, use_reloader=False)  # 禁用reloader避免定时任务重复启动
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        if 'scheduler' in locals() and scheduler:
            scheduler.shutdown()

