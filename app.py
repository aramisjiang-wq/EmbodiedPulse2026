"""
Flask Web Application for Robotics ArXiv Daily
"""
from flask import Flask, render_template, jsonify, request
import json
import os
import threading
import logging
from datetime import datetime
from daily_arxiv import load_config, demo, get_daily_papers
from models import init_db, get_session, Paper
from sqlalchemy import func, or_

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 支持中文

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def load_papers_data(json_path='./docs/cv-arxiv-daily.json', use_db=True):
    """加载论文数据（优先使用数据库）"""
    if use_db:
        try:
            session = get_session()
            papers = session.query(Paper).all()
            
            # 按类别组织数据
            result = {}
            for paper in papers:
                if paper.category not in result:
                    result[paper.category] = {}
                result[paper.category][paper.id] = paper.to_dict()
            
            session.close()
            return result
        except Exception as e:
            logger.warning(f"从数据库加载失败，尝试使用JSON: {e}")
            # 如果数据库失败，回退到JSON
    
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
    return render_template('index.html')

@app.route('/api/papers')
def get_papers():
    """获取论文列表API（使用数据库）"""
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
        
        # 按类别组织数据
        result = {}
        for paper in papers:
            if paper.category not in result:
                result[paper.category] = []
            result[paper.category].append(paper.to_dict())
        
        # 计算总数
        total_count = len(papers)
        
        session.close()
        
        return jsonify({
            'success': True,
            'data': result,
            'last_update': last_update,
            'total_count': total_count  # 添加总数
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
            
            return jsonify({
                'success': True,
                'data': result,
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'warning': '使用JSON文件作为数据源'
            })
        except Exception as e2:
            return jsonify({
                'success': False,
                'error': str(e2)
            }), 500

@app.route('/api/stats')
def get_stats():
    """获取统计信息（使用数据库）"""
    try:
        session = get_session()
        
        # 按类别统计
        stats_query = session.query(
            Paper.category,
            func.count(Paper.id).label('count')
        ).group_by(Paper.category).all()
        
        stats = {category: count for category, count in stats_query}
        total = session.query(func.count(Paper.id)).scalar() or 0
        
        session.close()
        
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

@app.route('/api/fetch-status')
def get_fetch_status():
    """获取抓取状态"""
    # 使用锁保护读取
    with fetch_status_lock:
        status_copy = fetch_status.copy()
    # 添加调试日志
    if status_copy.get('running'):
        logger.debug(f"返回抓取状态: {status_copy}")
    return jsonify(status_copy)

@app.route('/api/search')
def search_papers():
    """搜索论文"""
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
        
        session.close()
        
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })
    except Exception as e:
        logger.error(f"搜索论文失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/fetch', methods=['POST'])
def trigger_fetch():
    """触发论文抓取"""
    global fetch_status
    
    with fetch_status_lock:
        if fetch_status['running']:
            return jsonify({
                'success': False,
                'message': '抓取任务正在运行中，请稍候...'
            }), 400
    
    # 获取配置参数
    config_path = request.json.get('config_path', 'config.yaml')
    max_results = request.json.get('max_results', 20)
    
    def fetch_task():
        global fetch_status
        try:
            with fetch_status_lock:
                fetch_status['running'] = True
                fetch_status['message'] = '开始抓取论文...'
                fetch_status['progress'] = 0
                fetch_status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"抓取任务开始，fetch_status: {fetch_status}")
            
            config = load_config(config_path)
            config['max_results'] = max_results
            config['update_paper_links'] = False  # 确保是抓取模式
            config['enable_dedup'] = True  # 启用智能去重
            config['enable_incremental'] = False  # 暂时关闭增量更新，确保所有类别都有论文
            config['days_back'] = 60  # 抓取最近60天的论文，确保覆盖所有类别
            
            keywords = config['kv']
            with fetch_status_lock:
                fetch_status['total'] = len(keywords)
            logger.info(f"准备抓取 {fetch_status['total']} 个类别")
            
            # 执行抓取（传入fetch_status和lock用于更新进度）
            demo(**config, fetch_status=fetch_status, fetch_status_lock=fetch_status_lock)
            
            with fetch_status_lock:
                fetch_status['message'] = '抓取完成！'
                fetch_status['progress'] = fetch_status['total']
                fetch_status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"抓取任务完成，最终进度: {fetch_status['progress']}/{fetch_status['total']}")
            
        except Exception as e:
            logger.error(f"抓取任务失败: {e}", exc_info=True)
            with fetch_status_lock:
                fetch_status['message'] = f'抓取失败: {str(e)}'
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
    
    return jsonify({
        'success': True,
        'message': '抓取任务已启动'
    })

def start_scheduler():
    """启动定时任务调度器"""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        scheduler = BackgroundScheduler()
        
        def scheduled_fetch():
            """定时抓取任务"""
            global fetch_status
            if fetch_status['running']:
                logger.info("定时抓取任务跳过：已有任务正在运行")
                return
            
            try:
                logger.info("开始执行定时抓取任务...")
                config = load_config('config.yaml')
                config['max_results'] = int(os.getenv('AUTO_FETCH_MAX_RESULTS', 10))  # 定时任务使用较小数量
                config['update_paper_links'] = False
                config['publish_gitpage'] = False  # 定时任务不更新gitpage
                config['publish_wechat'] = False   # 定时任务不更新wechat
                
                # 执行抓取
                demo(**config)
                logger.info("定时抓取任务完成")
            except Exception as e:
                logger.error(f"定时抓取任务失败: {e}")
        
        # 配置定时任务
        # 每天凌晨2点执行（UTC时间，可根据时区调整）
        schedule_cron = os.getenv('AUTO_FETCH_SCHEDULE', '0 2 * * *')  # 默认每天凌晨2点
        
        # 解析 cron 表达式
        if schedule_cron:
            parts = schedule_cron.split()
            if len(parts) == 5:
                minute, hour, day, month, weekday = parts
                scheduler.add_job(
                    scheduled_fetch,
                    trigger=CronTrigger(
                        minute=minute,
                        hour=hour,
                        day=day,
                        month=month,
                        day_of_week=weekday
                    ),
                    id='daily_fetch',
                    name='每日论文抓取',
                    replace_existing=True
                )
                logger.info(f"定时任务已配置: {schedule_cron}")
        
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

