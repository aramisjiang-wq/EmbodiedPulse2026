#!/usr/bin/env python3
"""
系统性检查B站数据更新流程
检查：前端 -> API -> 数据库 -> 定时任务 -> 数据抓取
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def check_data_freshness():
    """检查数据新鲜度"""
    logger.info("=" * 60)
    logger.info("1. 检查数据新鲜度")
    logger.info("=" * 60)
    
    session = get_bilibili_session()
    try:
        ups = session.query(BilibiliUp).filter_by(is_active=True).all()
        
        issues = []
        warnings = []
        
        for up in ups:
            if not up.last_fetch_at:
                issues.append(f"❌ {up.name}: 从未更新过数据")
                continue
            
            hours_ago = (datetime.now() - up.last_fetch_at).total_seconds() / 3600
            
            if hours_ago > 24:
                issues.append(f"❌ {up.name}: 数据已{hours_ago:.1f}小时未更新（超过24小时）")
            elif hours_ago > 12:
                warnings.append(f"⚠️  {up.name}: 数据已{hours_ago:.1f}小时未更新（超过12小时）")
            else:
                logger.info(f"✅ {up.name}: {hours_ago:.1f}小时前更新")
        
        if issues:
            logger.error("\n严重问题:")
            for issue in issues:
                logger.error(f"  {issue}")
        
        if warnings:
            logger.warning("\n警告:")
            for warning in warnings:
                logger.warning(f"  {warning}")
        
        return len(issues) == 0
        
    finally:
        session.close()


def check_scheduler_config():
    """检查定时任务配置"""
    logger.info("=" * 60)
    logger.info("2. 检查定时任务配置")
    logger.info("=" * 60)
    
    auto_fetch_enabled = os.getenv('AUTO_FETCH_ENABLED', 'false').lower() == 'true'
    bilibili_schedule = os.getenv('AUTO_FETCH_BILIBILI_SCHEDULE', None)
    
    if not auto_fetch_enabled:
        logger.error("❌ AUTO_FETCH_ENABLED 未设置或为 false")
        logger.error("   解决方案: 在 .env 文件中设置 AUTO_FETCH_ENABLED=true")
        logger.error("   或者: export AUTO_FETCH_ENABLED=true")
        return False
    
    logger.info("✅ AUTO_FETCH_ENABLED=true")
    
    if bilibili_schedule:
        logger.info(f"✅ AUTO_FETCH_BILIBILI_SCHEDULE={bilibili_schedule}")
    else:
        logger.info("ℹ️  AUTO_FETCH_BILIBILI_SCHEDULE 未设置，使用默认值: 0 */6 * * * (每6小时)")
    
    return True


def check_scheduler_running():
    """检查定时任务是否正在运行"""
    logger.info("=" * 60)
    logger.info("3. 检查定时任务是否运行")
    logger.info("=" * 60)
    
    # 检查日志中是否有定时任务启动的记录
    log_file = 'app.log'
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if '定时任务调度器已启动' in content or '定时任务已配置' in content:
                logger.info("✅ 日志显示定时任务已配置")
                
                # 检查是否有B站定时任务配置
                if 'B站数据抓取定时任务已配置' in content:
                    logger.info("✅ B站数据抓取定时任务已配置")
                else:
                    logger.warning("⚠️  日志中未找到B站定时任务配置记录")
                
                # 检查是否有执行记录
                if '开始执行定时B站数据抓取任务' in content:
                    logger.info("✅ 发现定时任务执行记录")
                    # 查找最近的执行时间
                    lines = content.split('\n')
                    for line in reversed(lines):
                        if '开始执行定时B站数据抓取任务' in line:
                            logger.info(f"   最近执行: {line[:50]}...")
                            break
                else:
                    logger.warning("⚠️  日志中未找到定时任务执行记录")
                    logger.warning("   可能原因: 定时任务还未到执行时间，或执行失败")
            else:
                logger.error("❌ 日志中未找到定时任务启动记录")
                logger.error("   可能原因: AUTO_FETCH_ENABLED=false 或定时任务未启动")
    else:
        logger.warning("⚠️  日志文件不存在，无法检查定时任务状态")
    
    return True


def check_database_data():
    """检查数据库中的数据"""
    logger.info("=" * 60)
    logger.info("4. 检查数据库数据")
    logger.info("=" * 60)
    
    session = get_bilibili_session()
    try:
        ups = session.query(BilibiliUp).filter_by(is_active=True).all()
        logger.info(f"✅ 活跃UP主数: {len(ups)}")
        
        total_videos = session.query(BilibiliVideo).filter_by(is_deleted=False).count()
        logger.info(f"✅ 总视频数: {total_videos}")
        
        # 检查数据完整性
        for up in ups[:3]:  # 检查前3个
            video_count = session.query(BilibiliVideo).filter_by(uid=up.uid, is_deleted=False).count()
            if video_count == 0:
                logger.warning(f"⚠️  {up.name}: 没有视频数据")
            else:
                logger.info(f"✅ {up.name}: {video_count}个视频")
        
        return True
        
    finally:
        session.close()


def check_api_endpoint():
    """检查API端点"""
    logger.info("=" * 60)
    logger.info("5. 检查API端点")
    logger.info("=" * 60)
    
    try:
        import requests
        response = requests.get('http://localhost:5001/api/bilibili/all', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and isinstance(data.get('data'), list):
                logger.info(f"✅ API正常，返回 {len(data.get('data'))} 个UP主")
                return True
            else:
                logger.error(f"❌ API返回格式错误: data不是数组")
                return False
        else:
            logger.error(f"❌ API返回错误状态码: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ API检查失败: {e}")
        return False


def generate_report(results):
    """生成检查报告"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("检查报告总结")
    logger.info("=" * 60)
    
    logger.info(f"数据新鲜度: {'✅ 正常' if results['freshness'] else '❌ 需要更新'}")
    logger.info(f"定时任务配置: {'✅ 已配置' if results['scheduler_config'] else '❌ 未配置'}")
    logger.info(f"定时任务运行: {'✅ 正常' if results['scheduler_running'] else '⚠️  需检查'}")
    logger.info(f"数据库数据: {'✅ 正常' if results['database'] else '❌ 有问题'}")
    logger.info(f"API端点: {'✅ 正常' if results['api'] else '❌ 有问题'}")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("建议操作")
    logger.info("=" * 60)
    
    if not results['scheduler_config']:
        logger.info("1. 设置环境变量启用定时任务:")
        logger.info("   echo 'AUTO_FETCH_ENABLED=true' >> .env")
        logger.info("   echo 'AUTO_FETCH_BILIBILI_SCHEDULE=0 */6 * * *' >> .env")
        logger.info("   然后重启Flask服务器")
    
    if not results['freshness']:
        logger.info("2. 手动触发一次数据抓取:")
        logger.info("   python3 fetch_bilibili_data.py")
    
    if not results['scheduler_running']:
        logger.info("3. 检查定时任务是否正常启动:")
        logger.info("   查看 app.log 文件，搜索 '定时任务' 相关日志")


def main():
    """主函数"""
    logger.info("开始系统性检查B站数据更新流程...")
    logger.info("")
    
    results = {
        'freshness': check_data_freshness(),
        'scheduler_config': check_scheduler_config(),
        'scheduler_running': check_scheduler_running(),
        'database': check_database_data(),
        'api': check_api_endpoint()
    }
    
    generate_report(results)
    
    # 返回退出码
    if not results['scheduler_config'] or not results['freshness']:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()

