#!/usr/bin/env python3
"""
数据健康检查脚本
全面检查网站数据的可用性和可靠性
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, date
from models import get_session, Paper
from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from news_models import get_news_session, News
from jobs_models import get_jobs_session, Job
from datasets_models import get_datasets_session, Dataset
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class DataHealthChecker:
    """数据健康检查器"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.info = []
    
    def check_papers_data(self):
        """检查论文数据健康状态"""
        logger.info("=" * 60)
        logger.info("检查论文数据...")
        logger.info("=" * 60)
        
        session = get_session()
        try:
            # 1. 检查总论文数
            total_papers = session.query(Paper).count()
            self.info.append(f"总论文数: {total_papers}")
            logger.info(f"总论文数: {total_papers}")
            
            # 2. 检查最新论文日期
            latest_paper = session.query(Paper).order_by(Paper.publish_date.desc()).first()
            if latest_paper and latest_paper.publish_date:
                latest_date = latest_paper.publish_date
                days_ago = (date.today() - latest_date).days
                self.info.append(f"最新论文日期: {latest_date} ({days_ago}天前)")
                logger.info(f"最新论文日期: {latest_date} ({days_ago}天前)")
                
                # 如果最新论文超过2天，发出警告
                if days_ago > 2:
                    warning = f"⚠️  最新论文日期是{days_ago}天前，可能没有及时更新"
                    self.warnings.append(warning)
                    logger.warning(warning)
            else:
                issue = "❌ 无法获取最新论文日期"
                self.issues.append(issue)
                logger.error(issue)
            
            # 3. 检查今天是否有新论文
            today = date.today()
            today_start = datetime.combine(today, datetime.min.time())
            today_papers = session.query(Paper).filter(
                Paper.created_at >= today_start
            ).count()
            self.info.append(f"今天新增论文: {today_papers}篇")
            logger.info(f"今天新增论文: {today_papers}篇")
            
            # 4. 检查昨天是否有新论文
            yesterday = today - timedelta(days=1)
            yesterday_start = datetime.combine(yesterday, datetime.min.time())
            today_start = datetime.combine(today, datetime.min.time())
            yesterday_papers = session.query(Paper).filter(
                Paper.created_at >= yesterday_start,
                Paper.created_at < today_start
            ).count()
            self.info.append(f"昨天新增论文: {yesterday_papers}篇")
            logger.info(f"昨天新增论文: {yesterday_papers}篇")
            
            if yesterday_papers == 0:
                warning = "⚠️  昨天没有新增论文，定时任务可能未执行"
                self.warnings.append(warning)
                logger.warning(warning)
            
            # 5. 检查最近7天的论文数量
            week_ago = datetime.now() - timedelta(days=7)
            week_papers = session.query(Paper).filter(
                Paper.created_at >= week_ago
            ).count()
            self.info.append(f"最近7天新增论文: {week_papers}篇")
            logger.info(f"最近7天新增论文: {week_papers}篇")
            
            # 6. 检查未分类论文
            uncategorized = session.query(Paper).filter(
                Paper.category == 'Uncategorized'
            ).count()
            if uncategorized > 0:
                warning = f"⚠️  有{uncategorized}篇未分类论文"
                self.warnings.append(warning)
                logger.warning(warning)
            
            # 7. 检查最后更新时间
            last_update = session.query(Paper).order_by(Paper.updated_at.desc()).first()
            if last_update and last_update.updated_at:
                hours_ago = (datetime.now() - last_update.updated_at).total_seconds() / 3600
                self.info.append(f"最后更新时间: {last_update.updated_at} ({hours_ago:.1f}小时前)")
                logger.info(f"最后更新时间: {last_update.updated_at} ({hours_ago:.1f}小时前)")
                
                if hours_ago > 25:  # 超过25小时
                    warning = f"⚠️  数据最后更新时间是{hours_ago:.1f}小时前，可能没有及时更新"
                    self.warnings.append(warning)
                    logger.warning(warning)
            
        except Exception as e:
            issue = f"❌ 检查论文数据失败: {e}"
            self.issues.append(issue)
            logger.error(issue, exc_info=True)
        finally:
            session.close()
    
    def check_bilibili_data(self):
        """检查B站数据健康状态"""
        logger.info("=" * 60)
        logger.info("检查B站数据...")
        logger.info("=" * 60)
        
        session = get_bilibili_session()
        try:
            # 1. 检查UP主数量
            total_ups = session.query(BilibiliUp).filter_by(is_active=True).count()
            self.info.append(f"活跃UP主数: {total_ups}")
            logger.info(f"活跃UP主数: {total_ups}")
            
            if total_ups == 0:
                issue = "❌ 没有活跃的UP主数据，需要运行 fetch_bilibili_data.py"
                self.issues.append(issue)
                logger.error(issue)
                return
            
            # 2. 检查每个UP主的数据
            ups = session.query(BilibiliUp).filter_by(is_active=True).all()
            for up in ups:
                # 检查最后抓取时间
                if up.last_fetch_at:
                    hours_ago = (datetime.now() - up.last_fetch_at).total_seconds() / 3600
                    if hours_ago > 25:  # 超过25小时
                        warning = f"⚠️  UP主 {up.name}({up.uid}) 数据已{hours_ago:.1f}小时未更新"
                        self.warnings.append(warning)
                        logger.warning(warning)
                    
                    self.info.append(f"UP主 {up.name}: 最后更新 {up.last_fetch_at} ({hours_ago:.1f}小时前)")
                    logger.info(f"UP主 {up.name}: 最后更新 {up.last_fetch_at} ({hours_ago:.1f}小时前)")
                else:
                    warning = f"⚠️  UP主 {up.name}({up.uid}) 从未更新过数据"
                    self.warnings.append(warning)
                    logger.warning(warning)
                
                # 检查是否有错误
                if up.fetch_error:
                    warning = f"⚠️  UP主 {up.name}({up.uid}) 抓取错误: {up.fetch_error}"
                    self.warnings.append(warning)
                    logger.warning(warning)
                
                # 检查视频数量
                video_count = session.query(BilibiliVideo).filter_by(
                    uid=up.uid,
                    is_deleted=False
                ).count()
                self.info.append(f"UP主 {up.name}: {video_count}个视频")
                logger.info(f"UP主 {up.name}: {video_count}个视频")
                
                # 检查最新视频日期
                latest_video = session.query(BilibiliVideo).filter_by(
                    uid=up.uid,
                    is_deleted=False
                ).order_by(BilibiliVideo.pubdate_raw.desc()).first()
                
                if latest_video and latest_video.pubdate:
                    days_ago = (date.today() - latest_video.pubdate.date()).days
                    if days_ago > 7:
                        warning = f"⚠️  UP主 {up.name} 最新视频是{days_ago}天前发布的"
                        self.warnings.append(warning)
                        logger.warning(warning)
            
            # 3. 检查总视频数
            total_videos = session.query(BilibiliVideo).filter_by(is_deleted=False).count()
            self.info.append(f"总视频数: {total_videos}")
            logger.info(f"总视频数: {total_videos}")
            
        except Exception as e:
            issue = f"❌ 检查B站数据失败: {e}"
            self.issues.append(issue)
            logger.error(issue, exc_info=True)
        finally:
            session.close()
    
    def check_news_data(self):
        """检查新闻数据健康状态"""
        logger.info("=" * 60)
        logger.info("检查新闻数据...")
        logger.info("=" * 60)
        
        session = get_news_session()
        try:
            # 1. 检查24小时内的新闻
            twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
            recent_news = session.query(News).filter(
                News.created_at >= twenty_four_hours_ago
            ).count()
            self.info.append(f"24小时内新闻: {recent_news}条")
            logger.info(f"24小时内新闻: {recent_news}条")
            
            if recent_news == 0:
                warning = "⚠️  24小时内没有新新闻，可能没有及时更新"
                self.warnings.append(warning)
                logger.warning(warning)
            
            # 2. 检查总新闻数
            total_news = session.query(News).count()
            self.info.append(f"总新闻数: {total_news}")
            logger.info(f"总新闻数: {total_news}")
            
        except Exception as e:
            issue = f"❌ 检查新闻数据失败: {e}"
            self.issues.append(issue)
            logger.error(issue, exc_info=True)
        finally:
            session.close()
    
    def check_jobs_data(self):
        """检查招聘数据健康状态"""
        logger.info("=" * 60)
        logger.info("检查招聘数据...")
        logger.info("=" * 60)
        
        session = get_jobs_session()
        try:
            # 1. 检查总招聘数
            total_jobs = session.query(Job).count()
            self.info.append(f"总招聘数: {total_jobs}")
            logger.info(f"总招聘数: {total_jobs}")
            
            # 2. 检查今天新增的招聘
            today = date.today()
            today_start = datetime.combine(today, datetime.min.time())
            today_jobs = session.query(Job).filter(
                Job.created_at >= today_start
            ).count()
            self.info.append(f"今天新增招聘: {today_jobs}条")
            logger.info(f"今天新增招聘: {today_jobs}条")
            
        except Exception as e:
            issue = f"❌ 检查招聘数据失败: {e}"
            self.issues.append(issue)
            logger.error(issue, exc_info=True)
        finally:
            session.close()
    
    def check_scheduler_status(self):
        """检查定时任务状态"""
        logger.info("=" * 60)
        logger.info("检查定时任务配置...")
        logger.info("=" * 60)
        
        auto_fetch_enabled = os.getenv('AUTO_FETCH_ENABLED', 'false').lower() == 'true'
        if auto_fetch_enabled:
            self.info.append("定时任务: 已启用")
            logger.info("定时任务: 已启用")
            
            schedule_cron = os.getenv('AUTO_FETCH_SCHEDULE', '0 * * * *')
            self.info.append(f"论文抓取计划: {schedule_cron}")
            logger.info(f"论文抓取计划: {schedule_cron}")
            
            news_schedule = os.getenv('AUTO_FETCH_NEWS_SCHEDULE', '0 * * * *')
            self.info.append(f"新闻抓取计划: {news_schedule}")
            logger.info(f"新闻抓取计划: {news_schedule}")
            
            jobs_schedule = os.getenv('AUTO_FETCH_JOBS_SCHEDULE', '0 * * * *')
            self.info.append(f"招聘抓取计划: {jobs_schedule}")
            logger.info(f"招聘抓取计划: {jobs_schedule}")
            
            # 检查B站数据是否有定时任务
            bilibili_schedule = os.getenv('AUTO_FETCH_BILIBILI_SCHEDULE', None)
            if not bilibili_schedule:
                issue = "❌ B站数据没有配置定时任务，需要手动运行 fetch_bilibili_data.py"
                self.issues.append(issue)
                logger.error(issue)
            else:
                self.info.append(f"B站抓取计划: {bilibili_schedule}")
                logger.info(f"B站抓取计划: {bilibili_schedule}")
        else:
            warning = "⚠️  定时任务未启用 (AUTO_FETCH_ENABLED=false)"
            self.warnings.append(warning)
            logger.warning(warning)
    
    def generate_report(self):
        """生成检查报告"""
        logger.info("=" * 60)
        logger.info("生成检查报告...")
        logger.info("=" * 60)
        
        print("\n" + "=" * 60)
        print("数据健康检查报告")
        print("=" * 60)
        print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        if self.info:
            print("📊 信息:")
            for item in self.info:
                print(f"  {item}")
            print()
        
        if self.warnings:
            print("⚠️  警告:")
            for item in self.warnings:
                print(f"  {item}")
            print()
        
        if self.issues:
            print("❌ 问题:")
            for item in self.issues:
                print(f"  {item}")
            print()
        
        # 总结
        print("=" * 60)
        print("总结:")
        print(f"  信息: {len(self.info)}条")
        print(f"  警告: {len(self.warnings)}条")
        print(f"  问题: {len(self.issues)}条")
        
        if len(self.issues) == 0 and len(self.warnings) == 0:
            print("  ✅ 数据健康状态良好")
        elif len(self.issues) == 0:
            print("  ⚠️  数据基本正常，但有警告需要关注")
        else:
            print("  ❌ 数据存在问题，需要修复")
        print("=" * 60)
        
        return {
            'info_count': len(self.info),
            'warning_count': len(self.warnings),
            'issue_count': len(self.issues),
            'issues': self.issues,
            'warnings': self.warnings,
            'info': self.info
        }


def main():
    """主函数"""
    checker = DataHealthChecker()
    
    # 执行各项检查
    checker.check_scheduler_status()
    checker.check_papers_data()
    checker.check_bilibili_data()
    checker.check_news_data()
    checker.check_jobs_data()
    
    # 生成报告
    report = checker.generate_report()
    
    # 返回退出码
    if report['issue_count'] > 0:
        sys.exit(1)
    elif report['warning_count'] > 0:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()

