#!/usr/bin/env python3
"""
B站数据流测试脚本
系统性检查从Bilibili API -> 数据库 -> 后端API -> 前端的完整数据流
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import json
from datetime import datetime, timedelta
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class BilibiliDataFlowTester:
    """B站数据流测试器"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }
        self.backend_url = 'http://localhost:5001'
    
    def log_test(self, test_name, status, message, data=None):
        """记录测试结果"""
        result = {
            'test': test_name,
            'status': status,  # 'PASS', 'FAIL', 'WARN'
            'message': message,
            'data': data
        }
        self.results['tests'].append(result)
        
        if status == 'PASS':
            logger.info(f"✅ {test_name}: {message}")
        elif status == 'FAIL':
            logger.error(f"❌ {test_name}: {message}")
        else:
            logger.warning(f"⚠️ {test_name}: {message}")
    
    def test_1_database_connection(self):
        """测试1: 数据库连接"""
        logger.info("\n" + "="*60)
        logger.info("测试 1: 数据库连接")
        logger.info("="*60)
        
        try:
            from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
            session = get_bilibili_session()
            
            # 检查UP主表
            up_count = session.query(BilibiliUp).count()
            active_up_count = session.query(BilibiliUp).filter_by(is_active=True).count()
            
            # 检查视频表
            video_count = session.query(BilibiliVideo).count()
            recent_video_count = session.query(BilibiliVideo).filter(
                BilibiliVideo.pubdate >= datetime.now() - timedelta(days=7)
            ).count()
            
            session.close()
            
            self.log_test(
                '数据库连接',
                'PASS',
                f'数据库连接成功',
                {
                    'up_total': up_count,
                    'up_active': active_up_count,
                    'video_total': video_count,
                    'video_recent_7days': recent_video_count
                }
            )
            return True
            
        except Exception as e:
            self.log_test('数据库连接', 'FAIL', f'数据库连接失败: {e}')
            return False
    
    def test_2_bilibili_api_fetch(self):
        """测试2: Bilibili API数据抓取"""
        logger.info("\n" + "="*60)
        logger.info("测试 2: Bilibili API 数据抓取")
        logger.info("="*60)
        
        try:
            from bilibili_client import BilibiliClient
            from app import BILIBILI_UP_LIST
            
            client = BilibiliClient()
            
            # 测试抓取第一个UP主（逐际动力）
            test_uid = BILIBILI_UP_LIST[0]
            logger.info(f"测试抓取 UID: {test_uid}")
            
            data = client.get_all_data(test_uid, video_count=5)
            
            if data:
                user_info = data.get('user_info', {})
                videos = data.get('videos', [])
                
                self.log_test(
                    'Bilibili API抓取',
                    'PASS',
                    f'成功抓取UP主数据',
                    {
                        'uid': test_uid,
                        'name': user_info.get('name'),
                        'fans': user_info.get('fans'),
                        'video_count': len(videos),
                        'latest_video': videos[0].get('title') if videos else None
                    }
                )
                return True
            else:
                self.log_test('Bilibili API抓取', 'FAIL', 'API返回数据为空')
                return False
                
        except Exception as e:
            self.log_test('Bilibili API抓取', 'FAIL', f'API抓取失败: {e}')
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def test_3_data_persistence(self):
        """测试3: 数据持久化"""
        logger.info("\n" + "="*60)
        logger.info("测试 3: 数据持久化")
        logger.info("="*60)
        
        try:
            from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
            from app import BILIBILI_UP_LIST
            
            session = get_bilibili_session()
            test_uid = BILIBILI_UP_LIST[0]
            
            # 检查UP主数据
            up = session.query(BilibiliUp).filter_by(uid=test_uid).first()
            if not up:
                self.log_test('数据持久化', 'FAIL', f'数据库中未找到UID {test_uid}')
                session.close()
                return False
            
            # 检查视频数据
            videos = session.query(BilibiliVideo).filter_by(uid=test_uid).order_by(
                BilibiliVideo.pubdate.desc()
            ).limit(5).all()
            
            session.close()
            
            self.log_test(
                '数据持久化',
                'PASS',
                f'数据库中存在完整数据',
                {
                    'up_name': up.name,
                    'up_fans': up.fans_formatted,
                    'video_count_in_db': len(videos),
                    'latest_video': videos[0].title if videos else None,
                    'latest_video_date': videos[0].pubdate.strftime('%Y-%m-%d') if videos else None
                }
            )
            return True
            
        except Exception as e:
            self.log_test('数据持久化', 'FAIL', f'数据持久化检查失败: {e}')
            return False
    
    def test_4_backend_api_all(self):
        """测试4: 后端API - /api/bilibili/all"""
        logger.info("\n" + "="*60)
        logger.info("测试 4: 后端API - /api/bilibili/all")
        logger.info("="*60)
        
        try:
            response = requests.get(f'{self.backend_url}/api/bilibili/all', timeout=30)
            
            if response.status_code != 200:
                self.log_test(
                    '/api/bilibili/all',
                    'FAIL',
                    f'API返回状态码: {response.status_code}'
                )
                return False
            
            data = response.json()
            
            if not data.get('success'):
                self.log_test(
                    '/api/bilibili/all',
                    'FAIL',
                    f'API返回错误: {data.get("error")}'
                )
                return False
            
            companies = data.get('data', [])
            
            self.log_test(
                '/api/bilibili/all',
                'PASS',
                f'API返回数据正常',
                {
                    'company_count': len(companies),
                    'first_company': companies[0].get('name') if companies else None,
                    'first_company_video_count': len(companies[0].get('videos', [])) if companies else 0
                }
            )
            return True
            
        except Exception as e:
            self.log_test('/api/bilibili/all', 'FAIL', f'API请求失败: {e}')
            return False
    
    def test_5_backend_api_monthly_stats(self):
        """测试5: 后端API - /api/bilibili/monthly_stats"""
        logger.info("\n" + "="*60)
        logger.info("测试 5: 后端API - /api/bilibili/monthly_stats")
        logger.info("="*60)
        
        try:
            response = requests.get(f'{self.backend_url}/api/bilibili/monthly_stats', timeout=30)
            
            if response.status_code != 200:
                self.log_test(
                    '/api/bilibili/monthly_stats',
                    'FAIL',
                    f'API返回状态码: {response.status_code}'
                )
                return False
            
            data = response.json()
            
            if not data.get('success'):
                self.log_test(
                    '/api/bilibili/monthly_stats',
                    'FAIL',
                    f'API返回错误: {data.get("error")}'
                )
                return False
            
            monthly_data = data.get('data', {})
            months = monthly_data.get('months', [])
            companies = monthly_data.get('companies', [])
            
            self.log_test(
                '/api/bilibili/monthly_stats',
                'PASS',
                f'API返回数据正常',
                {
                    'month_count': len(months),
                    'company_count': len(companies),
                    'months': months[-3:] if len(months) >= 3 else months  # 最近3个月
                }
            )
            return True
            
        except Exception as e:
            self.log_test('/api/bilibili/monthly_stats', 'FAIL', f'API请求失败: {e}')
            return False
    
    def test_6_backend_api_yearly_stats(self):
        """测试6: 后端API - /api/bilibili/yearly_stats"""
        logger.info("\n" + "="*60)
        logger.info("测试 6: 后端API - /api/bilibili/yearly_stats")
        logger.info("="*60)
        
        try:
            response = requests.get(f'{self.backend_url}/api/bilibili/yearly_stats', timeout=30)
            
            if response.status_code != 200:
                self.log_test(
                    '/api/bilibili/yearly_stats',
                    'FAIL',
                    f'API返回状态码: {response.status_code}'
                )
                return False
            
            data = response.json()
            
            if not data.get('success'):
                self.log_test(
                    '/api/bilibili/yearly_stats',
                    'FAIL',
                    f'API返回错误: {data.get("error")}'
                )
                return False
            
            yearly_data = data.get('data', {})
            year = yearly_data.get('year')
            companies = yearly_data.get('companies', [])
            
            self.log_test(
                '/api/bilibili/yearly_stats',
                'PASS',
                f'API返回数据正常',
                {
                    'year': year,
                    'company_count': len(companies),
                    'top_3': companies[:3] if len(companies) >= 3 else companies
                }
            )
            return True
            
        except Exception as e:
            self.log_test('/api/bilibili/yearly_stats', 'FAIL', f'API请求失败: {e}')
            return False
    
    def test_7_data_freshness(self):
        """测试7: 数据新鲜度"""
        logger.info("\n" + "="*60)
        logger.info("测试 7: 数据新鲜度")
        logger.info("="*60)
        
        try:
            from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
            from app import BILIBILI_UP_LIST
            
            session = get_bilibili_session()
            
            # 检查最新视频
            latest_video = session.query(BilibiliVideo).order_by(
                BilibiliVideo.pubdate.desc()
            ).first()
            
            # 检查12月15日和16日的视频
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
            
            # 检查逐际动力的最新视频
            limx_uid = 1172054289
            limx_latest = session.query(BilibiliVideo).filter_by(
                uid=limx_uid
            ).order_by(BilibiliVideo.pubdate.desc()).first()
            
            session.close()
            
            status = 'PASS'
            messages = []
            
            if latest_video:
                days_ago = (datetime.now() - latest_video.pubdate).days
                messages.append(f'最新视频: {latest_video.title[:30]}... ({latest_video.pubdate.strftime("%Y-%m-%d")})')
                
                if days_ago > 1:
                    status = 'WARN'
                    messages.append(f'⚠️ 最新视频距今 {days_ago} 天，可能需要更新数据')
            else:
                status = 'FAIL'
                messages.append('未找到任何视频数据')
            
            messages.append(f'12月15日视频数: {len(dec_15_videos)}')
            messages.append(f'12月16日视频数: {len(dec_16_videos)}')
            
            if limx_latest:
                messages.append(f'逐际动力最新视频: {limx_latest.pubdate.strftime("%Y-%m-%d")} - {limx_latest.title[:30]}...')
            
            self.log_test(
                '数据新鲜度',
                status,
                ' | '.join(messages),
                {
                    'latest_video_date': latest_video.pubdate.isoformat() if latest_video else None,
                    'dec_15_count': len(dec_15_videos),
                    'dec_16_count': len(dec_16_videos),
                    'limx_latest_date': limx_latest.pubdate.isoformat() if limx_latest else None
                }
            )
            return status == 'PASS'
            
        except Exception as e:
            self.log_test('数据新鲜度', 'FAIL', f'数据新鲜度检查失败: {e}')
            return False
    
    def test_8_frontend_modules(self):
        """测试8: 前端模块数据展示"""
        logger.info("\n" + "="*60)
        logger.info("测试 8: 前端模块数据展示")
        logger.info("="*60)
        
        # 这个测试需要检查前端页面能否正常加载和渲染
        # 我们通过检查API返回的数据结构来推断前端是否能正常展示
        
        modules = {
            '视频发布数量趋势（近30天）': '/api/bilibili/all',
            '7天内最新视频': '/api/bilibili/all',
            'TOP 5（近30天发布数量）': '/api/bilibili/all',
            '月度播放量对比（近1年）': '/api/bilibili/monthly_stats',
            '年度总播放量（当年）': '/api/bilibili/yearly_stats',
            '公司列表': '/api/bilibili/all'
        }
        
        all_pass = True
        
        for module_name, api_path in modules.items():
            try:
                response = requests.get(f'{self.backend_url}{api_path}', timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.log_test(
                            f'前端模块-{module_name}',
                            'PASS',
                            f'数据API正常，前端应能正常展示'
                        )
                    else:
                        self.log_test(
                            f'前端模块-{module_name}',
                            'FAIL',
                            f'API返回错误: {data.get("error")}'
                        )
                        all_pass = False
                else:
                    self.log_test(
                        f'前端模块-{module_name}',
                        'FAIL',
                        f'API返回状态码: {response.status_code}'
                    )
                    all_pass = False
                    
            except Exception as e:
                self.log_test(
                    f'前端模块-{module_name}',
                    'FAIL',
                    f'API请求失败: {e}'
                )
                all_pass = False
        
        return all_pass
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("\n" + "="*60)
        logger.info("B站数据流完整性测试")
        logger.info("="*60)
        
        # 运行所有测试
        self.test_1_database_connection()
        self.test_2_bilibili_api_fetch()
        self.test_3_data_persistence()
        self.test_4_backend_api_all()
        self.test_5_backend_api_monthly_stats()
        self.test_6_backend_api_yearly_stats()
        self.test_7_data_freshness()
        self.test_8_frontend_modules()
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        logger.info("\n" + "="*60)
        logger.info("测试报告汇总")
        logger.info("="*60)
        
        total = len(self.results['tests'])
        passed = sum(1 for t in self.results['tests'] if t['status'] == 'PASS')
        failed = sum(1 for t in self.results['tests'] if t['status'] == 'FAIL')
        warned = sum(1 for t in self.results['tests'] if t['status'] == 'WARN')
        
        logger.info(f"总测试数: {total}")
        logger.info(f"通过: {passed} ✅")
        logger.info(f"失败: {failed} ❌")
        logger.info(f"警告: {warned} ⚠️")
        logger.info(f"通过率: {passed/total*100:.1f}%")
        
        # 保存到文件
        report_file = f'bilibili_dataflow_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n详细测试报告已保存到: {report_file}")
        logger.info("="*60)

def main():
    """主函数"""
    tester = BilibiliDataFlowTester()
    tester.run_all_tests()

if __name__ == '__main__':
    main()

