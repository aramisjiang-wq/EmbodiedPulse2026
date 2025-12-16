#!/usr/bin/env python3
"""
B站数据流简化测试脚本(不依赖bilibili-api-python)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import requests
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_database():
    """测试数据库"""
    logger.info("\n" + "="*60)
    logger.info("测试 1: 数据库连接和数据统计")
    logger.info("="*60)
    
    try:
        from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
        
        session = get_bilibili_session()
        
        # 统计数据
        up_count = session.query(BilibiliUp).count()
        active_up_count = session.query(BilibiliUp).filter_by(is_active=True).count()
        video_count = session.query(BilibiliVideo).count()
        
        # 最新视频
        latest_video = session.query(BilibiliVideo).order_by(
            BilibiliVideo.pubdate.desc()
        ).first()
        
        # 7天内视频
        week_ago = datetime.now() - timedelta(days=7)
        recent_videos = session.query(BilibiliVideo).filter(
            BilibiliVideo.pubdate >= week_ago
        ).count()
        
        # 12月15日和16日视频
        dec_15_start = datetime(2025, 12, 15, 0, 0, 0)
        dec_15_end = datetime(2025, 12, 15, 23, 59, 59)
        dec_16_start = datetime(2025, 12, 16, 0, 0, 0)
        dec_16_end = datetime(2025, 12, 16, 23, 59, 59)
        
        dec_15_videos = session.query(BilibiliVideo).filter(
            BilibiliVideo.pubdate >= dec_15_start,
            BilibiliVideo.pubdate <= dec_15_end
        ).all()
        
        dec_16_videos = session.query(BilibiliVideo).filter(
            BilibiliVideo.pubdate >= dec_16_start,
            BilibiliVideo.pubdate <= dec_16_end
        ).all()
        
        # 逐际动力数据
        limx_uid = 1172054289
        limx_up = session.query(BilibiliUp).filter_by(uid=limx_uid).first()
        limx_videos = session.query(BilibiliVideo).filter_by(uid=limx_uid).count()
        limx_latest = session.query(BilibiliVideo).filter_by(uid=limx_uid).order_by(
            BilibiliVideo.pubdate.desc()
        ).first()
        
        session.close()
        
        # 输出结果
        logger.info(f"✅ 数据库连接成功")
        logger.info(f"  UP主总数: {up_count} (活跃: {active_up_count})")
        logger.info(f"  视频总数: {video_count}")
        logger.info(f"  7天内视频: {recent_videos}")
        logger.info(f"  最新视频: {latest_video.title[:40]}... ({latest_video.pubdate.strftime('%Y-%m-%d %H:%M')})" if latest_video else "  无视频")
        logger.info(f"  12月15日视频数: {len(dec_15_videos)}")
        if dec_15_videos:
            for v in dec_15_videos[:3]:
                logger.info(f"    - [{v.pubdate.strftime('%H:%M')}] {v.title[:40]}...")
        logger.info(f"  12月16日视频数: {len(dec_16_videos)}")
        if dec_16_videos:
            for v in dec_16_videos[:3]:
                logger.info(f"    - [{v.pubdate.strftime('%H:%M')}] {v.title[:40]}...")
        
        if limx_up:
            logger.info(f"  逐际动力(UID:{limx_uid}):")
            logger.info(f"    - 名称: {limx_up.name}")
            logger.info(f"    - 粉丝: {limx_up.fans_formatted}")
            logger.info(f"    - 视频数: {limx_videos}")
            logger.info(f"    - 最新视频: {limx_latest.title if limx_latest else '无'}")
            logger.info(f"    - 最新视频日期: {limx_latest.pubdate.strftime('%Y-%m-%d %H:%M') if limx_latest else '无'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_backend_apis():
    """测试后端API"""
    logger.info("\n" + "="*60)
    logger.info("测试 2: 后端API端点")
    logger.info("="*60)
    
    backend_url = 'http://localhost:5001'
    apis = {
        '/api/bilibili/all': '获取所有UP主和视频数据',
        '/api/bilibili/monthly_stats': '月度播放量统计',
        '/api/bilibili/yearly_stats': '年度播放量统计'
    }
    
    all_pass = True
    
    for api_path, description in apis.items():
        try:
            response = requests.get(f'{backend_url}{api_path}', timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info(f"✅ {api_path}: {description} - 正常")
                    
                    # 显示一些关键数据
                    if api_path == '/api/bilibili/all':
                        companies = data.get('data', [])
                        logger.info(f"    - 公司数: {len(companies)}")
                        if companies:
                            logger.info(f"    - 第一个: {companies[0].get('name')} ({len(companies[0].get('videos', []))}个视频)")
                    
                    elif api_path == '/api/bilibili/monthly_stats':
                        monthly_data = data.get('data', {})
                        months = monthly_data.get('months', [])
                        companies = monthly_data.get('companies', [])
                        logger.info(f"    - 月份数: {len(months)}")
                        logger.info(f"    - 公司数: {len(companies)}")
                        if months:
                            logger.info(f"    - 最近月份: {', '.join(months[-3:])}")
                    
                    elif api_path == '/api/bilibili/yearly_stats':
                        yearly_data = data.get('data', {})
                        year = yearly_data.get('year')
                        companies = yearly_data.get('companies', [])
                        logger.info(f"    - 年份: {year}")
                        logger.info(f"    - 公司数: {len(companies)}")
                        if companies:
                            logger.info(f"    - 播放量最高: {companies[0].get('name')} ({companies[0].get('play_count')})")
                else:
                    logger.error(f"❌ {api_path}: API返回错误 - {data.get('error')}")
                    all_pass = False
            else:
                logger.error(f"❌ {api_path}: HTTP {response.status_code}")
                all_pass = False
                
        except Exception as e:
            logger.error(f"❌ {api_path}: 请求失败 - {e}")
            all_pass = False
    
    return all_pass

def check_frontend_modules():
    """检查前端模块数据源"""
    logger.info("\n" + "="*60)
    logger.info("测试 3: 前端模块数据源检查")
    logger.info("="*60)
    
    backend_url = 'http://localhost:5001'
    
    modules = {
        '视频发布数量趋势（近30天）': {
            'api': '/api/bilibili/all',
            'data_keys': ['data'],
            'check': lambda d: len(d.get('data', [])) > 0
        },
        '7天内最新视频': {
            'api': '/api/bilibili/all',
            'data_keys': ['data'],
            'check': lambda d: any(len(c.get('videos', [])) > 0 for c in d.get('data', []))
        },
        'TOP 5（近30天发布数量）': {
            'api': '/api/bilibili/all',
            'data_keys': ['data'],
            'check': lambda d: len(d.get('data', [])) > 0
        },
        '月度播放量对比（近1年）': {
            'api': '/api/bilibili/monthly_stats',
            'data_keys': ['data', 'months'],
            'check': lambda d: len(d.get('data', {}).get('months', [])) > 0
        },
        '年度总播放量（当年）': {
            'api': '/api/bilibili/yearly_stats',
            'data_keys': ['data', 'companies'],
            'check': lambda d: len(d.get('data', {}).get('companies', [])) > 0
        },
        '公司列表': {
            'api': '/api/bilibili/all',
            'data_keys': ['data'],
            'check': lambda d: len(d.get('data', [])) > 0
        }
    }
    
    all_pass = True
    
    for module_name, config in modules.items():
        try:
            response = requests.get(f"{backend_url}{config['api']}", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and config['check'](data):
                    logger.info(f"✅ {module_name}: 数据源正常")
                else:
                    logger.error(f"❌ {module_name}: 数据源无数据或格式错误")
                    all_pass = False
            else:
                logger.error(f"❌ {module_name}: API返回 HTTP {response.status_code}")
                all_pass = False
                
        except Exception as e:
            logger.error(f"❌ {module_name}: 检查失败 - {e}")
            all_pass = False
    
    return all_pass

def main():
    """主函数"""
    logger.info("="*60)
    logger.info("B站数据流简化测试")
    logger.info("="*60)
    
    results = []
    results.append(('数据库', test_database()))
    results.append(('后端API', test_backend_apis()))
    results.append(('前端模块', check_frontend_modules()))
    
    logger.info("\n" + "="*60)
    logger.info("测试汇总")
    logger.info("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{name}: {status}")
    
    logger.info(f"\n总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    logger.info("="*60)

if __name__ == '__main__':
    main()

