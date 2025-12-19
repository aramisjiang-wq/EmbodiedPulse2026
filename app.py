"""
Flask Web Application for Embodied Pulse
"""
from flask import Flask, render_template, jsonify, request
import json
import os
import threading
import logging
from datetime import datetime

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
from daily_arxiv import load_config, demo, get_daily_papers
from models import init_db, get_session, Paper
from sqlalchemy import func, or_, and_, desc
from jobs_models import get_jobs_session, Job
from datasets_models import get_datasets_session, Dataset
from news_models import get_news_session, News
from bilibili_client import BilibiliClient, format_number, format_timestamp
from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from taxonomy import (
    CATEGORY_DISPLAY,
    CATEGORY_ORDER,
    CATEGORY_DISPLAY_NAMES,
    display_category,
    get_category_meta,
    normalize_category,
    get_category_from_tag,
    build_category_tree,
    build_nested_from_flat,
)
# 导入认证系统蓝图
from auth_routes import auth_bp, user_bp, admin_bp

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

# 初始化数据库（Flask-SQLAlchemy）
from database import init_db
init_db(app)
logger.info("✅ Flask-SQLAlchemy数据库已初始化")

# 注册认证系统蓝图
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)
logger.info("✅ 认证系统蓝图已注册")

# 标签体系由 taxonomy.py 提供，避免多处定义

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
    'data': None,  # 单个UP主数据缓存（用于 /api/bilibili）
    'expires_at': None,
    'all_data': None,  # 所有UP主数据缓存（用于 /api/bilibili/all）
    'all_expires_at': None
}
bilibili_cache_lock = threading.Lock()
BILIBILI_CACHE_DURATION = 600  # 缓存10分钟（600秒），force=1 时跳过缓存

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
                norm_cat = normalize_category(paper.category)
                paper_dict = paper.to_dict()
                paper_dict['category'] = norm_cat
                if norm_cat not in result:
                    result[norm_cat] = {}
                result[norm_cat][paper.id] = paper_dict
            
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


def build_nested_papers(papers):
    """将论文列表组织为扁平化分类结构（新版）"""
    flat = {}
    for paper in papers:
        norm_cat = normalize_category(paper.category)
        paper_dict = paper.to_dict()
        paper_dict['category'] = norm_cat  # 使用规范化后的标签
        flat.setdefault(norm_cat, []).append(paper_dict)
    return flat


def build_nested_stats_from_papers(papers):
    """从论文列表构建嵌套统计"""
    flat_counts = {}
    for (cat,) in papers:
        norm_cat = normalize_category(cat)
        flat_counts[norm_cat] = flat_counts.get(norm_cat, 0) + 1
    return build_nested_from_flat(flat_counts)


@app.route('/api/categories/meta')
def get_category_meta_api():
    """提供标签体系的配置，前端可用来对齐顺序/显示名"""
    meta = get_category_meta()
    return jsonify({
        'success': True,
        'data': meta
    })

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

@app.route('/bilibili')
def bilibili_page():
    """B站视频页面"""
    template_path = os.path.join(app.template_folder, 'bilibili.html')
    if not os.path.exists(template_path):
        # 如果模板不存在，返回404或使用index.html
        logger.warning(f"B站页面模板不存在: {template_path}，使用index.html")
        return render_template('index.html')
    return render_template('bilibili.html')

# ==================== 认证系统前端路由 ====================

@app.route('/login')
def login_page():
    """飞书登录页面"""
    return render_template('login.html')

@app.route('/profile')
def profile_page():
    """个人中心页面"""
    return render_template('profile.html')

@app.route('/auth/callback')
def auth_callback_page():
    """登录成功回调页面"""
    return render_template('auth_callback.html')

@app.route('/test')
def test_page():
    """快速测试页面"""
    with open(os.path.join(BASE_DIR, '快速测试.html'), 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/admin/login')
def admin_login_page():
    """管理员登录页面（临时）"""
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>管理员登录 - Embodied Pulse</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                background: white;
                padding: 48px;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 400px;
                width: 100%;
            }
            h1 { color: #333; margin-bottom: 32px; text-align: center; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; color: #666; font-size: 14px; }
            input {
                width: 100%;
                padding: 12px 16px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                font-size: 15px;
            }
            input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
            }
            button {
                width: 100%;
                padding: 14px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                margin-top: 8px;
            }
            button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102,126,234,0.3); }
            #result {
                margin-top: 20px;
                padding: 16px;
                border-radius: 8px;
                display: none;
            }
            #result.success { background: #e8f5e9; color: #2e7d32; }
            #result.error { background: #ffebee; color: #c62828; }
            pre { white-space: pre-wrap; word-wrap: break-word; font-size: 13px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>管理员登录</h1>
            <form id="admin-login-form">
                <div class="form-group">
                    <label>用户名</label>
                    <input type="text" name="username" placeholder="请输入用户名" required>
                </div>
                <div class="form-group">
                    <label>密码</label>
                    <input type="password" name="password" placeholder="请输入密码" required>
                </div>
                <button type="submit">登录</button>
            </form>
            <div id="result"></div>
        </div>
        <script>
        document.getElementById('admin-login-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            const resultDiv = document.getElementById('result');
            
            try {
                const response = await fetch('/api/admin/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                
                resultDiv.style.display = 'block';
                if (result.success) {
                    resultDiv.className = 'success';
                    resultDiv.innerHTML = '<strong>✅ 登录成功！</strong><br>正在跳转到管理仪表盘...';
                    localStorage.setItem('auth_token', result.token);
                    setTimeout(() => {
                        window.location.href = '/admin/dashboard';
                    }, 1000);
                } else {
                    resultDiv.className = 'error';
                    resultDiv.innerHTML = '<strong>❌ 登录失败</strong><br>' + result.message;
                }
            } catch (error) {
                resultDiv.style.display = 'block';
                resultDiv.className = 'error';
                resultDiv.textContent = '网络错误：' + error.message;
            }
        });
        </script>
    </body>
    </html>
    """

@app.route('/admin/dashboard')
def admin_dashboard_page():
    """管理仪表盘页面"""
    return render_template('admin_dashboard.html')

@app.route('/admin/users')
def admin_users_page():
    """用户管理页面"""
    return render_template('admin_users.html')

@app.route('/admin/logs')
def admin_logs_page():
    """日志监控页面"""
    return render_template('admin_logs.html')

@app.route('/admin/papers')
def admin_papers_page():
    """论文管理页面"""
    return render_template('admin_papers.html')

@app.route('/admin/bilibili')
def admin_bilibili_page():
    """视频管理页面"""
    return render_template('admin_bilibili.html')

# ==================== API路由（已通过蓝图注册） ====================

@app.route('/api/paper-stats')
def get_paper_stats():
    """获取论文统计数据"""
    from datetime import datetime, timedelta
    
    try:
        session = get_session()
        
        # 总论文数
        total = session.query(func.count(Paper.id)).scalar()
        
        # 今日新增（created_at为今天）
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_papers = session.query(func.count(Paper.id)).filter(
            Paper.created_at >= today_start
        ).scalar()
        
        # 近7天新增
        week_ago = datetime.now() - timedelta(days=7)
        week_papers = session.query(func.count(Paper.id)).filter(
            Paper.created_at >= week_ago
        ).scalar()
        
        # 近30天新增
        month_ago = datetime.now() - timedelta(days=30)
        month_papers = session.query(func.count(Paper.id)).filter(
            Paper.created_at >= month_ago
        ).scalar()
        
        # 最后更新时间
        last_update = session.query(Paper.updated_at).order_by(
            desc(Paper.updated_at)
        ).first()
        
        session.close()
        
        return jsonify({
            'total': total,
            'today': today_papers,
            'week': week_papers,
            'month': month_papers,
            'last_update': last_update[0].isoformat() if last_update else None
        })
        
    except Exception as e:
        logger.error(f"获取论文统计数据失败: {e}")
        return jsonify({
            'total': 0,
            'today': 0,
            'week': 0,
            'month': 0,
            'last_update': None,
            'error': str(e)
        }), 500

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
        
        # 按三层标签组织数据
        nested = build_nested_papers(papers)
        logger.info(f"build_nested_papers返回: {len(nested)} 个分类")
        logger.info(f"前5个分类: {list(nested.keys())[:5]}")
        
        # 计算总数
        total_count = len(papers)
        
        return jsonify({
            'success': True,
            'data': nested,
            'last_update': last_update,
            'total_count': total_count,
            'new_papers_count': new_papers_count  # 新增论文数量
        })
    except Exception as e:
        logger.error(f"获取论文列表失败: {e}")
        # 如果数据库失败，回退到JSON
        try:
            data = load_papers_data(use_db=False)
            flat_result = {}
            
            for keyword, papers in data.items():
                parsed_papers = []
                for paper_id, paper_entry in papers.items():
                    parsed = parse_paper_entry(paper_entry)
                    if parsed:
                        parsed['id'] = paper_id
                        parsed_papers.append(parsed)
                
                parsed_papers.sort(key=lambda x: x['date'], reverse=True)
                norm_key = normalize_category(keyword)
                flat_result[norm_key] = parsed_papers
            
            nested = build_nested_from_flat(flat_result)
            
            # 回退到JSON时，无法计算新论文数量，返回0
            return jsonify({
                'success': True,
                'data': nested,
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_count': sum(len(papers) for papers in flat_result.values()),
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
        
        # 获取时间范围内的所有论文，统一按新标签归类
        papers = session.query(Paper).filter(
            or_(
                and_(Paper.publish_date.isnot(None), Paper.publish_date >= start_date, Paper.publish_date <= end_date),
                and_(Paper.publish_date.is_(None),
                     func.date(Paper.created_at) >= start_date,
                     func.date(Paper.created_at) <= end_date)
            )
        ).all()

        # 为每个类别生成时间序列数据
        trends_data = {}
        for paper in papers:
            norm_cat = normalize_category(paper.category)
            if norm_cat == 'Uncategorized':
                continue
            if paper.publish_date:
                date_key = paper.publish_date
            elif paper.created_at:
                date_key = paper.created_at.date()
            else:
                continue
            if not (start_date <= date_key <= end_date):
                continue
            date_str = date_key.strftime('%Y-%m-%d')
            trends_data.setdefault(norm_cat, {'daily_counts': {}})
            trends_data[norm_cat]['daily_counts'][date_str] = trends_data[norm_cat]['daily_counts'].get(date_str, 0) + 1

        # 如果没有类别，返回空数据
        if not trends_data:
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

        # 生成完整的时间序列（包括没有论文的日期）
        for category, payload in trends_data.items():
            daily_counts = payload.get('daily_counts', {})
            date_list = []
            count_list = []
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                date_list.append(date_str)
                count_list.append(daily_counts.get(date_str, 0))
                current_date += timedelta(days=1)
            payload['dates'] = date_list
            payload['counts'] = count_list
            payload['total'] = sum(count_list)
        
        # 计算增长最快的方向（最近7天 vs 之前7天）
        growth_analysis = {}
        if days >= 14:
            recent_start = end_date - timedelta(days=7)
            previous_start = end_date - timedelta(days=14)
            
            for category in CATEGORY_ORDER:
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

@app.route('/api/research-activity')
def get_research_activity():
    """获取研究方向活跃度数据（按周统计）"""
    session = None
    try:
        from datetime import timedelta
        from collections import defaultdict
        
        session = get_session()
        
        # 获取查询参数
        weeks = request.args.get('weeks', type=int, default=8)  # 默认8周
        weeks = min(max(weeks, 4), 52)  # 限制在4-52周之间
        level = request.args.get('level', type=str, default='category')  # 'category' 或 'tag'
        category_filter = request.args.get('category', type=str, default=None)  # 可选，用于筛选子标签
        
        # 计算起始日期（按周计算）
        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=weeks)
        
        # 获取时间范围内的所有论文
        papers = session.query(Paper).filter(
            or_(
                and_(Paper.publish_date.isnot(None), Paper.publish_date >= start_date, Paper.publish_date <= end_date),
                and_(Paper.publish_date.is_(None),
                     func.date(Paper.created_at) >= start_date,
                     func.date(Paper.created_at) <= end_date)
            )
        ).all()
        
        # 按周分组统计
        # 生成周区间（周一到周日）
        week_ranges = []
        current_date = start_date
        # 找到第一个周一
        while current_date.weekday() != 0:  # 0 = Monday
            current_date -= timedelta(days=1)
        
        week_labels = []
        while current_date <= end_date:
            week_end = min(current_date + timedelta(days=6), end_date)
            week_ranges.append((current_date, week_end))
            # 生成周标签：MM/DD-MM/DD
            week_labels.append(f"{current_date.strftime('%m/%d')}-{week_end.strftime('%m/%d')}")
            current_date += timedelta(days=7)
        
        # 统计每个分类/子标签每周的论文数量
        activity_data = defaultdict(lambda: [0] * len(week_ranges))
        
        for paper in papers:
            # 确定日期
            if paper.publish_date:
                date_key = paper.publish_date
            elif paper.created_at:
                date_key = paper.created_at.date()
            else:
                continue
            
            if not (start_date <= date_key <= end_date):
                continue
            
            # 确定分类/子标签
            if level == 'category':
                # 分类视图：提取分类名称
                if paper.category and '/' in paper.category:
                    category = paper.category.split('/')[0]
                else:
                    category = normalize_category(paper.category)
                
                if category == 'Uncategorized':
                    continue
                
                # 找到该日期属于哪一周
                for i, (week_start, week_end) in enumerate(week_ranges):
                    if week_start <= date_key <= week_end:
                        activity_data[category][i] += 1
                        break
            else:
                # 子标签视图：使用完整category
                category = normalize_category(paper.category)
                if category == 'Uncategorized':
                    continue
                
                # 如果指定了分类筛选，只统计该分类下的子标签
                if category_filter:
                    if not category.startswith(category_filter + '/'):
                        continue
                
                # 找到该日期属于哪一周
                for i, (week_start, week_end) in enumerate(week_ranges):
                    if week_start <= date_key <= week_end:
                        activity_data[category][i] += 1
                        break
        
        # 转换为字典格式
        result_data = {}
        for key, counts in activity_data.items():
            result_data[key] = counts
        
        # 如果没有数据，返回空结果
        if not result_data:
            return jsonify({
                'success': True,
                'level': level,
                'weeks': week_labels,
                'data': {},
                'category_filter': category_filter,
                'message': '暂无论文数据'
            })
        
        return jsonify({
            'success': True,
            'level': level,
            'weeks': week_labels,
            'data': result_data,
            'category_filter': category_filter,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        })
        
    except Exception as e:
        logger.error(f"获取研究方向活跃度数据失败: {e}")
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
        papers = session.query(Paper.category).all()
        flat_counts = {}
        for (cat,) in papers:
            norm_cat = normalize_category(cat)
            flat_counts[norm_cat] = flat_counts.get(norm_cat, 0) + 1
        total = sum(flat_counts.values())
        nested_counts = build_nested_from_flat(flat_counts)
        
        return jsonify({
            'success': True,
            'stats': nested_counts,
            'total': total,
            'display': CATEGORY_DISPLAY
        })
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        # 回退到JSON
        try:
            data = load_papers_data(use_db=False)
            flat_counts = {}
            total = 0
            
            for keyword, papers in data.items():
                count = len(papers)
                norm_cat = normalize_category(keyword)
                flat_counts[norm_cat] = flat_counts.get(norm_cat, 0) + count
                total += count
            
            nested_counts = build_nested_from_flat(flat_counts)
            
            return jsonify({
                'success': True,
                'stats': nested_counts,
                'total': total,
                'display': CATEGORY_DISPLAY,
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

# B站UP主列表配置
BILIBILI_UP_LIST = [
    1172054289,       # 逐际动力
    3546595559737798, # 傅立叶智能（旧-保留）
    3494380742642452, # 傅立叶智能（官方？备份）
    3546665977907667, # 加速进化机器人
    3546728498202679, # 众擎
    22477177,         # 云深处
    519804427,        # 傅利叶（用户提供）
    521974986,        # Unitree宇树科技
    472153261,        # 优必选科技
    3546714680068378, # 松延动力
    3537120496978247, # 乐聚机器人LEJUROBOT
    3546561487309464, # 星动纪元ROBOTERA
]

@app.route('/api/bilibili/all')
def get_all_bilibili():
    """从数据库获取所有B站UP主和视频数据"""
    try:
        force = request.args.get('force') == '1'
        now_ts = datetime.now().timestamp()
        # 缩短缓存时间到5分钟，确保前端能及时获取最新数据
        CACHE_DURATION = 300  # 5分钟（300秒）
        if not force:
            with bilibili_cache_lock:
                # 使用 all_data 缓存，而不是 data 缓存
                # 同时验证缓存数据格式是否正确（必须是数组）
                cached_data = bilibili_cache.get('all_data')
                cache_expires_at = bilibili_cache.get('all_expires_at')
                if cached_data and cache_expires_at and cache_expires_at > now_ts:
                    # 验证数据格式：data字段必须是数组
                    if isinstance(cached_data.get('data'), list):
                        logger.info(f"使用B站所有数据缓存（剩余{int(cache_expires_at - now_ts)}秒）")
                        return jsonify(cached_data)
                    else:
                        logger.warning("缓存数据格式错误（不是数组），清除缓存并重新获取")
                        bilibili_cache['all_data'] = None
                        bilibili_cache['all_expires_at'] = None

        session = get_bilibili_session()
        all_data = []
        
        # 从数据库获取所有活跃的UP主
        # 排序：逐际动力(1172054289)始终在第一位，其他按UID排序
        LIMX_UID = 1172054289
        
        # 直接SQL查询检查（调试）
        from sqlalchemy import text
        direct_result = session.execute(text("""
            SELECT uid, name, videos_count, views_count, views_formatted 
            FROM bilibili_ups 
            WHERE uid = :uid AND is_active = true
        """), {"uid": LIMX_UID})
        direct_row = direct_result.fetchone()
        if direct_row:
            logger.info(f"DEBUG_直接SQL查询逐际动力: uid={direct_row[0]}, name={direct_row[1]}, videos_count={direct_row[2]}, views_count={direct_row[3]}")
        
        ups = session.query(BilibiliUp).filter_by(is_active=True).all()
        
        # 调试：检查查询到的UP主数据
        for up in ups:
            if up.uid == LIMX_UID:
                logger.info(f"DEBUG_ORM查询逐际动力: uid={up.uid}, name={up.name}, videos_count={up.videos_count}, views_count={up.views_count}")
        
        # 分离逐际动力和其他UP主
        limx_up = None
        other_ups = []
        for up in ups:
            if up.uid == LIMX_UID:
                limx_up = up
            else:
                other_ups.append(up)
        # 其他UP主按UID排序
        other_ups.sort(key=lambda x: x.uid)
        # 合并：逐际动力在第一位
        ups = ([limx_up] if limx_up else []) + other_ups
        
        if not ups:
            logger.warning("数据库中暂无UP主数据，请先运行 fetch_bilibili_data.py 抓取数据")
            # 返回空数据，但保持接口可用
            return jsonify({
                'success': True,
                'data': [],
                'total': 0,
                'updated_at': datetime.now().isoformat(),
                'message': '数据库中暂无数据，请先运行数据抓取脚本'
            })
        
        for up in ups:
            try:
                # 刷新UP主对象，确保数据是最新的
                session.refresh(up)
                
                # 获取该UP主的视频（按发布时间倒序，最多200条）
                videos_query = session.query(BilibiliVideo).filter_by(
                    uid=up.uid,
                    is_deleted=False
                ).order_by(BilibiliVideo.pubdate_raw.desc()).limit(200)
                
                videos = videos_query.all()
                
                # 转换为字典格式
                formatted_videos = []
                for video in videos:
                    formatted_videos.append({
                        'bvid': video.bvid,
                        'title': video.title or '',
                        'pic': video.pic or '',
                        'play': video.play_formatted or '0',
                        'play_raw': video.play or 0,
                        'favorites': video.favorites_formatted or '0',
                        'video_review': video.video_review_formatted or '0',
                        'pubdate': format_timestamp(video.pubdate_raw) if video.pubdate_raw else '',
                        'pubdate_raw': video.pubdate_raw or 0,
                        'description': video.description or '',
                        'length': video.length or '',
                        'url': video.url or f"https://www.bilibili.com/video/{video.bvid}"
                    })
                
                # 构建user_stat（确保正确处理）
                # ✅ 修复：如果数据库值为0，尝试从视频表计算
                from sqlalchemy import func
                
                if up.videos_count and up.videos_count > 0:
                    videos_val = format_number(up.videos_count)
                else:
                    # 从视频表计算
                    video_count = session.query(func.count(BilibiliVideo.bvid)).filter_by(
                        uid=up.uid, is_deleted=False
                    ).scalar()
                    videos_val = format_number(video_count) if video_count and video_count > 0 else '0'
                
                if up.views_count and up.views_count > 0:
                    views_val = up.views_formatted or format_number(up.views_count)
                else:
                    # 从视频表计算
                    total_views = session.query(func.sum(BilibiliVideo.play)).filter_by(
                        uid=up.uid, is_deleted=False
                    ).scalar() or 0
                    views_val = format_number(total_views) if total_views > 0 else '0'
                
                likes_val = up.likes_formatted or (format_number(up.likes_count) if up.likes_count else '0')
                
                # 调试日志（临时）
                if up.name == '逐际动力':
                    logger.info(f"DEBUG_逐际动力: videos_count={up.videos_count}, views_count={up.views_count}, views_formatted={up.views_formatted!r}")
                    logger.info(f"DEBUG_逐际动力计算结果: videos_val={videos_val!r}, views_val={views_val!r}")
                
                # 构建响应数据
                card_data = {
                    'user_info': {
                        'mid': up.uid,
                        'name': up.name,
                        'face': up.face or '',
                        'sign': up.sign or '',
                        'level': up.level,
                        'fans': up.fans_formatted or '0',
                        'fans_raw': up.fans or 0,
                        'friend': str(up.friend) if up.friend else '0',
                    },
                    'user_stat': {
                        'videos': videos_val,
                        'likes': likes_val,
                        'views': views_val,
                    },
                    'videos': formatted_videos,
                    'space_url': up.space_url or f"https://space.bilibili.com/{up.uid}",
                    'updated_at': up.last_fetch_at.isoformat() if up.last_fetch_at else datetime.now().isoformat()
                }
                
                # 如果有错误信息，添加错误标记
                if up.fetch_error:
                    card_data['error'] = True
                    card_data['error_message'] = up.fetch_error
                
                all_data.append(card_data)
                
            except Exception as e:
                logger.error(f"处理UP主 {up.uid} 数据失败: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # 添加错误数据
                all_data.append({
                    'user_info': {
                        'mid': up.uid,
                        'name': up.name or f'UP主{up.uid}',
                        'face': '',
                        'sign': f'数据处理失败: {str(e)}',
                        'level': 0,
                        'fans': '0',
                        'fans_raw': 0,
                        'friend': '0',
                    },
                    'user_stat': {},
                    'videos': [],
                    'space_url': f"https://space.bilibili.com/{up.uid}",
                    'error': True,
                    'error_message': str(e)
                })
        
        session.close()
        
        response_data = {
            'success': True,
            'data': all_data,
            'total': len(all_data),
            'updated_at': datetime.now().isoformat(),
            'source': 'database'  # 标识数据来源
        }
        
        logger.info(f"从数据库获取B站数据，共 {len(all_data)} 个UP主")
        
        # 保存到 all_data 缓存（只有成功获取数据时才缓存）
        # 缓存时间缩短到5分钟，与前端刷新频率一致
        CACHE_DURATION = 300  # 5分钟（300秒）
        with bilibili_cache_lock:
            bilibili_cache['all_data'] = response_data
            bilibili_cache['all_expires_at'] = datetime.now().timestamp() + CACHE_DURATION
            logger.info(f"B站所有数据已缓存，有效期至: {datetime.fromtimestamp(bilibili_cache['all_expires_at'])} (5分钟)")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"从数据库获取Bilibili数据失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/bilibili/yearly_stats')
def get_bilibili_yearly_stats():
    """从数据库统计各公司当前年份的总播放量（各公司当年发布的所有视频的播放量合计）"""
    try:
        from collections import defaultdict
        
        session = get_bilibili_session()
        
        # 从数据库获取所有活跃的UP主
        ups = session.query(BilibiliUp).filter_by(is_active=True).all()
        
        if not ups:
            logger.warning("数据库中暂无UP主数据")
            return jsonify({
                'success': True,
                'data': {
                    'year': str(datetime.now().year),
                    'companies': []
                },
                'total_companies': 0,
                'updated_at': datetime.now().isoformat()
            })
        
        # 统计当前年份各公司的总播放量
        current_year = datetime.now().year
        company_play_counts = defaultdict(int)
        all_companies_set = set()
        
        # 查询当前年份的数据
        year_start = datetime(current_year, 1, 1)
        year_end = datetime(current_year, 12, 31, 23, 59, 59)
        
        for up in ups:
            company_name = up.name
            all_companies_set.add(company_name)
            
            # 查询该UP主当前年份的所有视频
            videos = session.query(BilibiliVideo).filter(
                BilibiliVideo.uid == up.uid,
                BilibiliVideo.is_deleted == False,
                BilibiliVideo.pubdate >= year_start,
                BilibiliVideo.pubdate <= year_end
            ).all()
            
            # 统计该公司的年度总播放量
            for video in videos:
                if not video.pubdate or not video.play:
                    continue
                
                try:
                    if video.pubdate.year == current_year:
                        play_count = video.play or 0
                        company_play_counts[company_name] += play_count
                except Exception as e:
                    logger.debug(f"处理视频 {video.bvid} 日期失败: {e}")
                    continue
        
        session.close()
        
        # 公司排序：完全按播放量降序排序
        companies_list = [
            {'name': name, 'play_count': count}
            for name, count in company_play_counts.items()
        ]
        companies_list.sort(key=lambda x: x['play_count'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'year': str(current_year),
                'companies': companies_list
            },
            'total_companies': len(companies_list),
            'updated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取年度统计数据失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/bilibili/monthly_stats')
def get_bilibili_monthly_stats():
    """从数据库按月统计各公司播放量对比（各公司当月发布的所有视频的播放量合计）"""
    try:
        from collections import defaultdict
        from datetime import datetime as dt, timedelta
        from sqlalchemy import func, extract
        
        session = get_bilibili_session()
        
        # 从数据库获取所有活跃的UP主
        ups = session.query(BilibiliUp).filter_by(is_active=True).all()
        
        if not ups:
            logger.warning("数据库中暂无UP主数据")
            return jsonify({
                'success': True,
                'data': {
                    'months': [],
                    'companies': []
                },
                'total_companies': 0,
                'total_months': 0,
                'updated_at': datetime.now().isoformat()
            })
        
        # 按月份组织数据：{月份: {公司名: 播放量}}
        monthly_by_month = defaultdict(lambda: defaultdict(int))
        all_companies_set = set()
        
        # 从数据库查询视频数据，按月统计
        for up in ups:
            company_name = up.name
            all_companies_set.add(company_name)
            
            # 查询该UP主的所有视频（最近12个月）
            twelve_months_ago = datetime.now().replace(day=1)
            for _ in range(12):
                twelve_months_ago = (twelve_months_ago.replace(day=1) - timedelta(days=1)).replace(day=1)
            
            videos = session.query(BilibiliVideo).filter(
                BilibiliVideo.uid == up.uid,
                BilibiliVideo.is_deleted == False,
                BilibiliVideo.pubdate >= twelve_months_ago
            ).all()
            
            # 按月统计播放量
            for video in videos:
                if not video.pubdate or not video.play:
                    continue
                
                try:
                    month_key = video.pubdate.strftime('%Y-%m')  # 格式：2025-12
                    play_count = video.play or 0
                    monthly_by_month[month_key][company_name] += play_count
                except Exception as e:
                    logger.debug(f"处理视频 {video.bvid} 日期失败: {e}")
                    continue
        
        session.close()
        
        # 转换为列表格式，按月份排序（最近12个月）
        all_months = sorted(monthly_by_month.keys(), reverse=True)[:12]
        
        # 公司排序：逐际动力始终在第一位，其他按字母顺序
        LIMX_NAME = '逐际动力'
        all_companies = sorted(all_companies_set)
        if LIMX_NAME in all_companies:
            all_companies.remove(LIMX_NAME)
            all_companies.insert(0, LIMX_NAME)
        
        monthly_stats = []
        for month in all_months:
            month_data = {
                'month': month,
                'companies': {}
            }
            for company in all_companies:
                play_count = monthly_by_month[month].get(company, 0)
                month_data['companies'][company] = {
                    'play_count': play_count,
                    'play_count_formatted': format_number(play_count)
                }
            monthly_stats.append(month_data)
        
        return jsonify({
            'success': True,
            'data': {
                'months': monthly_stats,
                'companies': all_companies
            },
            'total_companies': len(all_companies),
            'total_months': len(monthly_stats),
            'updated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取月度统计数据失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/authors/ranking')
def get_author_ranking():
    """获取活跃作者排行榜"""
    session = None
    try:
        from datetime import date, timedelta
        from collections import defaultdict
        import re
        
        session = get_session()
        
        # 获取查询参数
        days = request.args.get('days', type=int, default=7)  # 默认7天
        category = request.args.get('category', type=str, default='')  # 类别筛选
        limit = request.args.get('limit', type=int, default=20)  # 默认top20
        normalized_filter = normalize_category(category) if category else ''
        
        # 计算日期范围
        today = date.today()
        start_date = today - timedelta(days=days)
        
        # 构建查询（时间范围内的所有论文，后续按新标签过滤）
        papers = session.query(Paper).filter(
            or_(
                and_(Paper.publish_date.isnot(None), Paper.publish_date >= start_date, Paper.publish_date <= today),
                and_(Paper.publish_date.is_(None), 
                     func.date(Paper.created_at) >= start_date, 
                     func.date(Paper.created_at) <= today)
            )
        ).all()
        
        # 统计作者论文数量
        author_count = defaultdict(lambda: {'count': 0, 'papers': []})
        
        for paper in papers:
            norm_cat = normalize_category(paper.category)
            if normalized_filter and norm_cat != normalized_filter:
                continue
            if not paper.authors:
                continue
            
            # 解析作者列表（可能是逗号分隔的字符串）
            authors_str = paper.authors.strip()
            if not authors_str:
                continue
            
            # 分割作者（处理各种分隔符）
            authors = re.split(r'[,，;；]', authors_str)
            
            for author in authors:
                author = author.strip()
                if not author or len(author) < 2:  # 过滤太短的名称
                    continue
                
                # 移除常见的后缀（如"Team", "et al."等）
                author = re.sub(r'\s+(Team|et al\.?|等)$', '', author, flags=re.IGNORECASE)
                author = author.strip()
                
                if not author or len(author) < 2:
                    continue
                
                author_count[author]['count'] += 1
                author_count[author]['papers'].append({
                    'id': paper.id,
                    'title': paper.title,
                    'date': paper.publish_date.strftime('%Y-%m-%d') if paper.publish_date else '',
                    'category': norm_cat,
                    'pdf_url': paper.pdf_url,
                    'code_url': paper.code_url,
                })
        
        # 转换为列表并排序
        author_list = []
        for author, data in author_count.items():
            author_list.append({
                'author': author,
                'count': data['count'],
                'papers': sorted(data['papers'], key=lambda x: x['date'], reverse=True)
            })
        
        # 按论文数量排序，取top N
        author_list.sort(key=lambda x: x['count'], reverse=True)
        author_list = author_list[:limit]
        
        # 计算环比（与上一个周期对比）
        prev_start_date = start_date - timedelta(days=days)
        prev_query = session.query(Paper).filter(
            or_(
                and_(Paper.publish_date.isnot(None), Paper.publish_date >= prev_start_date, Paper.publish_date < start_date),
                and_(Paper.publish_date.is_(None), 
                     func.date(Paper.created_at) >= prev_start_date, 
                     func.date(Paper.created_at) < start_date)
            )
        )
        prev_papers = prev_query.all()
        
        # 统计上一个周期的作者数量
        prev_author_count = defaultdict(int)
        for paper in prev_papers:
            norm_cat = normalize_category(paper.category)
            if normalized_filter and norm_cat != normalized_filter:
                continue
            if not paper.authors:
                continue
            authors_str = paper.authors.strip()
            if not authors_str:
                continue
            authors = re.split(r'[,，;；]', authors_str)
            for author in authors:
                author = author.strip()
                if not author or len(author) < 2:
                    continue
                author = re.sub(r'\s+(Team|et al\.?|等)$', '', author, flags=re.IGNORECASE)
                author = author.strip()
                if author and len(author) >= 2:
                    prev_author_count[author] += 1
        
        # 计算环比增长率
        for author_data in author_list:
            author = author_data['author']
            current_count = author_data['count']
            prev_count = prev_author_count.get(author, 0)
            
            if prev_count > 0:
                growth_rate = ((current_count - prev_count) / prev_count) * 100
            elif current_count > 0:
                growth_rate = 100  # 从0增长到有数据
            else:
                growth_rate = 0
            
            author_data['growth_rate'] = round(growth_rate, 1)
            author_data['prev_count'] = prev_count
        
        return jsonify({
            'success': True,
            'data': author_list,
            'days': days,
            'category': category,
            'total': len(author_list),
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': today.strftime('%Y-%m-%d')
        })
        
    except Exception as e:
        logger.error(f"获取作者排行榜失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if session:
            session.close()

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
    # 使用锁保护读取，并在这里做一次“兜底纠错”
    # 场景：某些情况下底层进度已经到达 total，但 running 标志未及时置为 False，
    # 会导致前端一直显示“正在抓取 General-Robot (24/24)...”
    with fetch_status_lock:
        # 先拷贝一份当前状态
        status_copy = fetch_status.copy()

        # 如果发现 progress >= total 且 total > 0，但 running 仍为 True，则在这里自动纠正
        try:
            running = bool(status_copy.get('running'))
            total = int(status_copy.get('total', 0) or 0)
            progress = int(status_copy.get('progress', 0) or 0)
        except Exception:
            running = status_copy.get('running', False)
            total = status_copy.get('total', 0) or 0
            progress = status_copy.get('progress', 0) or 0

        if running and total > 0 and progress >= total:
            logger.warning(
                f"检测到抓取进度已完成但running仍为True，自动纠正状态：progress={progress}, total={total}, "
                f"current_keyword={status_copy.get('current_keyword')}"
            )
            fetch_status['running'] = False
            fetch_status['message'] = '抓取完成！（由进度自动纠正状态）'
            fetch_status['current_keyword'] = ''
            fetch_status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # 重新拷贝一份修正后的状态
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
        
        if not query:
            return jsonify({
                'success': False,
                'error': '请提供搜索关键词'
            }), 400
        
        session = get_session()
        
        # 构建查询（全局搜索，不受类别限制）
        papers_query = session.query(Paper)
        
        # 按关键词搜索（标题、作者或摘要）
        if query:
            papers_query = papers_query.filter(
                or_(
                    Paper.title.contains(query),
                    Paper.authors.contains(query),
                    Paper.abstract.contains(query)
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
    from datetime import datetime, timedelta  # 在函数开头导入，确保整个函数可用
    
    # 使用锁保护整个检查-设置过程，确保原子性操作
    with fetch_status_lock:
        # 检查状态，如果running为True但last_update超过10分钟，认为任务已卡死，重置状态
        if fetch_status['running']:
            last_update_str = fetch_status.get('last_update', '')
            if last_update_str:
                try:
                    last_update = datetime.strptime(last_update_str, '%Y-%m-%d %H:%M:%S')
                    if datetime.now() - last_update > timedelta(minutes=10):
                        logger.warning("检测到抓取任务可能已卡死，重置状态")
                        fetch_status['running'] = False
                        fetch_status['progress'] = 0
                        fetch_status['current_keyword'] = ''
                        fetch_status['message'] = '检测到任务可能已卡死，已重置状态'
                    else:
                        # 任务正在运行，拒绝新请求
                        logger.info(f"拒绝新的抓取请求：任务正在运行中（{last_update.strftime('%Y-%m-%d %H:%M:%S')}）")
                        return jsonify({
                            'success': False,
                            'message': '抓取任务正在运行中，请稍候...',
                            'status': fetch_status.copy()
                        }), 400
                except Exception as e:
                    # 如果解析失败，重置状态
                    logger.warning(f"无法解析last_update时间，重置状态: {e}")
                    fetch_status['running'] = False
                    fetch_status['progress'] = 0
                    fetch_status['current_keyword'] = ''
            else:
                # 如果没有last_update，重置状态
                logger.warning("没有last_update信息，重置状态")
                fetch_status['running'] = False
                fetch_status['progress'] = 0
                fetch_status['current_keyword'] = ''
        
        # 原子性设置running状态，防止并发问题
        # 在锁内检查并设置，确保不会有多个任务同时启动
        if fetch_status['running']:
            # 如果检查后状态仍然是running，说明确实有任务在运行
            return jsonify({
                'success': False,
                'message': '抓取任务正在运行中，请稍候...',
                'status': fetch_status.copy()
            }), 400
        
        # 设置running状态（在锁内，确保原子性）
        fetch_status['running'] = True
        fetch_status['message'] = '准备启动抓取任务...'
        fetch_status['progress'] = 0
        fetch_status['total'] = 0
        fetch_status['current_keyword'] = ''
        fetch_status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 简化版：不需要配置参数，直接执行脚本
    # 脚本内部已配置好所有参数（max_results=100, days_back=14等）
    
    def fetch_task():
        """后台抓取任务 - 直接调用 fetch_new_data.fetch_papers() 函数"""
        global fetch_status
        from datetime import datetime  # 在函数内部导入，避免作用域问题
        
        try:
            # 注意：running状态已经在trigger_fetch中设置，这里只需要更新消息
            with fetch_status_lock:
                fetch_status['message'] = '开始抓取论文...'
                fetch_status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info("=" * 60)
            logger.info("开始抓取论文数据（通过/api/fetch接口）...")
            logger.info("=" * 60)
            
            # 直接导入并调用 fetch_papers 函数，传递 fetch_status 和 fetch_status_lock
            # 这样可以实时更新状态，而不需要解析 stdout
            from fetch_new_data import fetch_papers
            
            logger.info("调用 fetch_papers() 函数...")
            
            # 调用函数，传递状态更新参数
            fetch_papers(fetch_status=fetch_status, fetch_status_lock=fetch_status_lock)
            
            # 任务完成，更新状态
            with fetch_status_lock:
                fetch_status['message'] = '抓取完成！'
                fetch_status['running'] = False  # 关键：标记任务已完成
                fetch_status['current_keyword'] = ''
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
            # 确保在所有情况下都重置running状态
            with fetch_status_lock:
                if fetch_status.get('running', False):
                    # 如果还在运行状态，说明可能异常退出，重置状态
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
        
        # 配置全量抓取定时任务（每天凌晨2点执行，避免与关键词抓取冲突）
        try:
            def scheduled_full_fetch():
                """定时全量抓取论文任务 - 使用宽泛关键词查询"""
                global fetch_status
                if fetch_status['running']:
                    logger.info("全量抓取任务跳过：已有任务正在运行")
                    return
                
                try:
                    logger.info("=" * 60)
                    logger.info("开始执行定时全量论文抓取任务...")
                    logger.info("=" * 60)
                    
                    from scripts.full_fetch_papers import fetch_full_papers
                    fetch_full_papers(days_back=3, max_results_per_query=100)
                    
                    logger.info("=" * 60)
                    logger.info("定时全量论文抓取任务完成")
                    logger.info("=" * 60)
                except Exception as e:
                    logger.error("=" * 60)
                    logger.error(f"定时全量论文抓取任务失败: {e}")
                    logger.error("=" * 60)
                    import traceback
                    logger.error(traceback.format_exc())
            
            # 每天凌晨2点执行全量抓取（避免与关键词抓取和Semantic Scholar更新冲突）
            full_fetch_schedule = os.getenv('AUTO_FETCH_FULL_SCHEDULE', '0 2 * * *')
            if full_fetch_schedule:
                parts = full_fetch_schedule.split()
                if len(parts) == 5:
                    minute, hour, day, month, weekday = parts
                    scheduler.add_job(
                        scheduled_full_fetch,
                        trigger=CronTrigger(
                            minute=minute,
                            hour=hour,
                            day=day,
                            month=month,
                            day_of_week=weekday
                        ),
                        id='daily_full_fetch_papers',
                        name='每天全量论文抓取',
                        replace_existing=True
                    )
                    logger.info(f"全量抓取定时任务已配置: {full_fetch_schedule}")
        except Exception as e:
            logger.warning(f"配置全量抓取定时任务失败: {e}")
            import traceback
            logger.warning(traceback.format_exc())
        
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
        
        # 配置B站数据抓取定时任务（每6小时执行一次，避免触发风控）
        try:
            def scheduled_fetch_bilibili():
                """定时抓取B站数据任务"""
                try:
                    logger.info("=" * 60)
                    logger.info("开始执行定时B站数据抓取任务...")
                    logger.info("=" * 60)
                    from fetch_bilibili_data import fetch_all_bilibili_data
                    # 使用较长的延迟避免触发风控
                    fetch_all_bilibili_data(video_count=50, delay_between_requests=2.0)
                    logger.info("=" * 60)
                    logger.info("定时B站数据抓取任务完成")
                    logger.info("=" * 60)
                except Exception as e:
                    logger.error("=" * 60)
                    logger.error(f"定时B站数据抓取任务失败: {e}")
                    logger.error("=" * 60)
                    import traceback
                    logger.error(traceback.format_exc())
            
            # 支持通过环境变量自定义B站数据抓取的cron表达式
            # 格式：分钟 小时 日 月 星期，如 "0 */6 * * *" 表示每6小时执行一次
            # 如果环境变量未设置，默认每6小时执行一次（避免触发风控）
            bilibili_schedule_cron = os.getenv('AUTO_FETCH_BILIBILI_SCHEDULE', '0 */6 * * *')  # 默认每6小时执行
            
            # 解析 cron 表达式（支持多个，用分号分隔）
            if bilibili_schedule_cron:
                cron_list = bilibili_schedule_cron.split(';')
                for idx, cron_expr in enumerate(cron_list):
                    cron_expr = cron_expr.strip()
                    if not cron_expr:
                        continue
                    parts = cron_expr.split()
                    if len(parts) == 5:
                        minute, hour, day, month, weekday = parts
                        job_id = f'hourly_fetch_bilibili_{idx}'
                        job_name = f'B站数据抓取_{idx+1}'
                        scheduler.add_job(
                            scheduled_fetch_bilibili,
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
                        logger.info(f"B站数据抓取定时任务已配置 ({job_name}): {cron_expr}")
        except Exception as e:
            logger.warning(f"配置B站数据抓取定时任务失败: {e}")
            import traceback
            logger.warning(traceback.format_exc())
        
        # 配置Semantic Scholar数据更新定时任务（支持增量更新）
        try:
            # 每天凌晨3点：更新最近30天的论文（增量更新）
            def scheduled_update_recent_semantic_scholar():
                """定时更新最近30天的Semantic Scholar数据（增量更新）"""
                try:
                    logger.info("开始执行定时Semantic Scholar数据更新任务（最近30天，增量更新）...")
                    from scripts.improve_semantic_update import update_recent_papers
                    update_limit = int(os.getenv('SEMANTIC_UPDATE_LIMIT', 200))
                    update_recent_papers(days=30, limit=update_limit)
                    logger.info("定时Semantic Scholar数据更新任务完成")
                except Exception as e:
                    logger.error(f"定时Semantic Scholar数据更新任务失败: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            # 每周日凌晨3点：更新最近90天的论文（增量更新）
            def scheduled_update_weekly_semantic_scholar():
                """定时更新最近90天的Semantic Scholar数据（增量更新）"""
                try:
                    logger.info("开始执行定时Semantic Scholar数据更新任务（最近90天，增量更新）...")
                    from scripts.improve_semantic_update import update_recent_papers
                    update_recent_papers(days=90, limit=500)
                    logger.info("定时Semantic Scholar数据更新任务完成")
                except Exception as e:
                    logger.error(f"定时Semantic Scholar数据更新任务失败: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            # 每月1日凌晨3点：更新所有论文（增量更新）
            def scheduled_update_monthly_semantic_scholar():
                """定时更新所有论文的Semantic Scholar数据（增量更新）"""
                try:
                    logger.info("开始执行定时Semantic Scholar数据更新任务（所有论文，增量更新）...")
                    from scripts.improve_semantic_update import update_all_papers_incremental
                    update_all_papers_incremental(limit=1000, skip_recent=True)
                    logger.info("定时Semantic Scholar数据更新任务完成")
                except Exception as e:
                    logger.error(f"定时Semantic Scholar数据更新任务失败: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            update_limit = int(os.getenv('SEMANTIC_UPDATE_LIMIT', 200))
            
            # 每天凌晨3点：更新最近30天的论文
            scheduler.add_job(
                scheduled_update_recent_semantic_scholar,
                trigger=CronTrigger(hour=3, minute=0),
                id='daily_update_semantic_scholar_recent',
                name='每天Semantic Scholar数据更新（最近30天）',
                replace_existing=True
            )
            
            # 每周日凌晨3点：更新最近90天的论文
            scheduler.add_job(
                scheduled_update_weekly_semantic_scholar,
                trigger=CronTrigger(day_of_week=6, hour=3, minute=0),  # 周日 = 6
                id='weekly_update_semantic_scholar',
                name='每周Semantic Scholar数据更新（最近90天）',
                replace_existing=True
            )
            
            # 每月1日凌晨3点：更新所有论文
            scheduler.add_job(
                scheduled_update_monthly_semantic_scholar,
                trigger=CronTrigger(day=1, hour=3, minute=0),
                id='monthly_update_semantic_scholar',
                name='每月Semantic Scholar数据更新（所有论文）',
                replace_existing=True
            )
            
            logger.info(f"Semantic Scholar数据更新定时任务已配置:")
            logger.info(f"  - 每天凌晨3点：更新最近30天的论文（每次{update_limit}篇）")
            logger.info(f"  - 每周日凌晨3点：更新最近90天的论文（每次500篇）")
            logger.info(f"  - 每月1日凌晨3点：更新所有论文（每次1000篇，跳过7天内已更新的）")
        except Exception as e:
            logger.warning(f"配置Semantic Scholar数据更新定时任务失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
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
    # 确保加载.env文件
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
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

