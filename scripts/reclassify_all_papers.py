#!/usr/bin/env python3
"""
批量重新分类所有论文脚本

功能：
1. 读取数据库中的所有论文
2. 根据标题和摘要智能分类（使用关键词匹配）
3. 清除所有旧标签，应用新标签
4. 批量更新数据库
5. 生成分类报告
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import get_session, Paper
from taxonomy import (
    NEW_TAXONOMY, normalize_category, display_category,
    get_search_keywords, UNCATEGORIZED_KEY, get_category_from_tag
)
import logging
from collections import defaultdict
from typing import List, Dict, Tuple
import re

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def classify_paper_by_keywords(paper: Paper) -> List[str]:
    """
    根据关键词匹配对论文进行分类
    检索词需要在标题或摘要中出现（分别检查）
    
    Args:
        paper: 论文对象
    
    Returns:
        匹配的标签列表（可能多个）
    """
    title = (paper.title or '').lower()
    abstract = (paper.abstract or '').lower()
    
    if not title and not abstract:
        return [UNCATEGORIZED_KEY]
    
    matched_tags = []
    tag_scores = defaultdict(int)
    
    # 遍历所有标签，计算匹配分数
    for tag_key, (chinese, english, keywords) in NEW_TAXONOMY.items():
        score = 0
        
        # 检查关键词匹配（分别检查标题和摘要）
        for keyword in keywords:
            keyword_lower = keyword.lower()
            title_match = False
            abstract_match = False
            
            # 特殊处理：对于"embodied benchmark"，允许"embodied"和"benchmark"在较近位置出现
            if keyword_lower == "embodied benchmark":
                # 检查标题
                if title:
                    # 1. 精确匹配短语
                    if 'embodied benchmark' in title:
                        title_match = True
                        score += 5
                    # 2. 检查"embodied"和"benchmark"是否都在标题中，且在较近位置（50个字符内）
                    elif 'embodied' in title and 'benchmark' in title:
                        emb_positions = [m.start() for m in re.finditer(r'\bembodied\b', title)]
                        bench_positions = [m.start() for m in re.finditer(r'\bbenchmark\b', title)]
                        for emb_pos in emb_positions:
                            for bench_pos in bench_positions:
                                if abs(emb_pos - bench_pos) <= 50:
                                    title_match = True
                                    score += 4  # 较近位置匹配，权重稍低
                                    break
                            if title_match:
                                break
                
                # 检查摘要
                if abstract:
                    # 1. 精确匹配短语
                    if 'embodied benchmark' in abstract:
                        abstract_match = True
                        score += 5
                    # 2. 检查"embodied"和"benchmark"是否都在摘要中，且在较近位置（50个字符内）
                    elif 'embodied' in abstract and 'benchmark' in abstract:
                        emb_positions = [m.start() for m in re.finditer(r'\bembodied\b', abstract)]
                        bench_positions = [m.start() for m in re.finditer(r'\bbenchmark\b', abstract)]
                        for emb_pos in emb_positions:
                            for bench_pos in bench_positions:
                                if abs(emb_pos - bench_pos) <= 50:
                                    abstract_match = True
                                    score += 4  # 较近位置匹配，权重稍低
                                    break
                            if abstract_match:
                                break
            else:
                # 其他关键词的常规匹配逻辑
                # 检查标题
                if title:
            # 1. 精确匹配（单词边界）- 权重最高
            pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                    if re.search(pattern, title):
                        title_match = True
                        score += 5  # 标题精确匹配权重
                    # 2. 部分匹配
                    elif keyword_lower in title:
                        title_match = True
                        score += 2
                    # 3. 模糊匹配（处理空格、连字符变体）
                    else:
                        keyword_variants = [
                            keyword_lower.replace(' ', ''),
                            keyword_lower.replace(' ', '-'),
                            keyword_lower.replace(' ', '_'),
                            keyword_lower.replace('-', ' '),
                        ]
                        for variant in keyword_variants:
                            if variant in title:
                                title_match = True
                                score += 1
                                break
                
                # 检查摘要
                if abstract:
                    # 1. 精确匹配（单词边界）- 权重最高
                    pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                    if re.search(pattern, abstract):
                        abstract_match = True
                        score += 5  # 摘要精确匹配权重
                    # 2. 部分匹配
                    elif keyword_lower in abstract:
                        abstract_match = True
                        score += 2
            # 3. 模糊匹配（处理空格、连字符变体）
                    else:
            keyword_variants = [
                keyword_lower.replace(' ', ''),
                keyword_lower.replace(' ', '-'),
                keyword_lower.replace(' ', '_'),
                keyword_lower.replace('-', ' '),
            ]
            for variant in keyword_variants:
                            if variant in abstract:
                                abstract_match = True
                    score += 1
                    break
            
            # 如果标题和摘要都匹配，额外加分
            if title_match and abstract_match:
                score += 3
        
        # 检查英文术语匹配（分别检查标题和摘要）
        # 注意：对于基准分类（Benchmark/Benchmark），只匹配检索词"embodied benchmark"，不匹配单独的"benchmark"
        english_lower = english.lower()
        title_term_match = False
        abstract_term_match = False
        
        # 对于基准分类，跳过英文术语匹配（只使用检索词匹配）
        if tag_key != "Benchmark/Benchmark":
            if title:
                pattern = r'\b' + re.escape(english_lower) + r'\b'
                if re.search(pattern, title):
                    title_term_match = True
                    score += 3
                elif english_lower in title:
                    title_term_match = True
                    score += 1.5
            
            if abstract:
        pattern = r'\b' + re.escape(english_lower) + r'\b'
                if re.search(pattern, abstract):
                    abstract_term_match = True
                    score += 3
                elif english_lower in abstract:
                    abstract_term_match = True
            score += 1.5
            
            # 如果标题和摘要都匹配术语，额外加分
            if title_term_match and abstract_term_match:
                score += 2
        
        if score > 0:
            tag_scores[tag_key] = score
    
    # 按分数排序，取最高分的标签
    if tag_scores:
        sorted_tags = sorted(
            tag_scores.items(),
            key=lambda x: (-x[1], x[0])  # 先按分数降序，再按标签键排序
        )
        # 只取分数最高的1个标签
        matched_tags.append(sorted_tags[0][0])
    
    # 如果没有匹配，使用兜底分类逻辑
    if not matched_tags:
        # 兜底分类：根据标题和摘要中的常见词汇进行模糊匹配
        text = f"{title} {abstract}".lower()
        
        # 检查是否包含robot相关词（更广泛的匹配）
        robot_words = [
            'robot', 'robotic', 'robotics', 'embodied', 'agent', 'autonomous', 
            'human-robot', 'robot learning', 'robotic system', 'manipulator', 
            'manipulation', 'ros ', 'ros2', 'endoscopic', 'exosuit', 'servo',
            'trajectory', 'pose estimation', 'visual servo', 'hand trajectory',
            'embodiment', 'cross-embodiment', 'active perception', 'active exploration',
            'pushingbots', 'collision avoidance', 'drone', 'uav', 'bot', 'bots'
        ]
        has_robot_context = any(word in text for word in robot_words)
        
        if has_robot_context:
            # 根据关键词进行兜底分类（优先级从高到低）
            # 1. 感知相关
            if 'vlm' in text or 'vision language' in text or 'multimodal' in text or 'clip' in text or 'visual instruction' in text:
                matched_tags.append('Perception/Vision-Language Model')
            elif 'visual reasoning' in text or 'visual interpretation' in text or 'visual evidence' in text or 'visual reasoner' in text:
                matched_tags.append('Perception/Vision-Language Model')
            elif '3d' in text or 'point cloud' in text or 'depth' in text or 'lidar' in text or 'rgb-d' in text or 'rgbd' in text or 'gaussian' in text or 'splatting' in text or '6d pose' in text or 'pose estimation' in text or '3d-gaussian' in text or 'gaussian simulators' in text or 'monocular' in text or 'spatial reasoning' in text or 'spatial' in text:
                matched_tags.append('Perception/3D Perception')
            elif 'detect' in text or 'detection' in text or 'recognition' in text:
                matched_tags.append('Perception/Object Detection')
            elif 'segment' in text or 'segmentation' in text or 'mask' in text:
                matched_tags.append('Perception/Instance Segmentation')
            elif 'visual servo' in text or 'servo' in text:
                matched_tags.append('Perception/2D Perception')
            elif 'perception' in text or 'proprioception' in text or 'active perception' in text or 'active sensing' in text:
                # 包含perception的，优先归类到感知
                if '3d' in text or 'spatial' in text or 'monocular' in text:
                    matched_tags.append('Perception/3D Perception')
                else:
                    matched_tags.append('Perception/2D Perception')
            elif 'vision' in text or 'visual' in text or 'image' in text or 'camera' in text:
                if '3d' in text or 'spatial' in text or 'monocular' in text:
                    matched_tags.append('Perception/3D Perception')
                else:
                    matched_tags.append('Perception/2D Perception')
            # 2. 操作相关
            elif 'grasp' in text or 'grasping' in text or 'pick' in text or 'place' in text or 'manipulator' in text:
                matched_tags.append('Operation/Grasp')
            elif 'manipulation' in text or 'manipulate' in text or 'manipulators' in text:
                matched_tags.append('Operation/Grasp')
            elif 'hand trajectory' in text or 'hand trajectories' in text or 'exosuit' in text or 'soft finger' in text:
                matched_tags.append('Operation/Dexterous Hands')
            elif 'bimanual' in text or 'dual arm' in text or 'two-arm' in text:
                matched_tags.append('Operation/Bimanual Manipulation')
            elif 'dexterous' in text or 'dexterity' in text:
                matched_tags.append('Operation/Dexterous Hands')
            elif 'vla' in text or 'vision language action' in text:
                matched_tags.append('Operation/Vision-Language-Action Models')
            elif 'collision avoidance' in text or 'collision' in text:
                matched_tags.append('Decision/Task Planning')
            elif 'policy' in text or 'policies' in text or 'visuomotor' in text or 'action model' in text or 'flow matching policies' in text:
                matched_tags.append('Operation/Policy')
            # 3. 学习相关
            elif 'imitation learning' in text or 'il' in text or 'behavior cloning' in text or 'demonstration' in text or 'demonstrations' in text or 'imitation' in text or 'offline imitation' in text:
                matched_tags.append('Learning/Imitation Learning')
            elif 'reinforcement learning' in text or 'rl' in text or 'ppo' in text or 'sac' in text or 'reinforcement' in text:
                matched_tags.append('Learning/Reinforcement Learning')
            elif 'cross-embodiment' in text or 'embodiment' in text or 'embodied learning' in text:
                matched_tags.append('Learning/Imitation Learning')
            elif 'learning' in text or 'train' in text or 'training' in text:
                # 通用学习相关，优先选择模仿学习（因为更常见）
                matched_tags.append('Learning/Imitation Learning')
            # 4. 决策相关
            elif 'planning' in text or 'plan' in text or 'navigation' in text or 'reasoning' in text or 'planner' in text or 'odometry' in text or 'mapping' in text or 'exploration' in text:
                matched_tags.append('Decision/Task Planning')
            # 5. 运动相关
            elif 'locomotion' in text or 'walking' in text or 'gait' in text:
                matched_tags.append('Motion Control/Locomotion Control')
            elif 'humanoid' in text or 'bipedal' in text:
                matched_tags.append('Motion Control/Humanoid Robot')
            elif 'quadruped' in text or 'four-legged' in text:
                matched_tags.append('Motion Control/Quadruped Robot')
            elif 'motion' in text or 'movement' in text:
                matched_tags.append('Motion Control/Locomotion Control')
            # 6. 最后的兜底：如果包含robot相关词但无法精确分类
            else:
                # 根据常见词汇进行更宽松的匹配
                if 'model' in text or 'network' in text or 'neural' in text:
                    matched_tags.append('Learning/Reinforcement Learning')
                else:
                    matched_tags.append('Operation/Policy')
        else:
            # 如果不包含robot相关词，检查是否包含AI/ML/CV相关词汇
            ai_keywords = ['learning', 'model', 'neural', 'network', 'vision', 'image', 'video', 'ai', 'machine', 'deep', 'benchmark', 'dataset', 'demonstration', 'imitation']
            has_ai_context = any(kw in text for kw in ai_keywords)
            
            if has_ai_context:
                # 根据关键词进行AI/ML/CV相关的兜底分类（优先级从高到低）
                if 'demonstration' in text or 'demonstrations' in text or 'imitation' in text:
                    matched_tags.append('Learning/Imitation Learning')
                elif 'visual reasoning' in text or 'visual interpretation' in text or 'visual evidence' in text or 'visual reasoner' in text or 'visual knowledge' in text:
                    matched_tags.append('Perception/Vision-Language Model')
                elif 'perception' in text:
                    # 包含perception的，优先归类到感知
                    if '3d' in text or 'spatial' in text or 'monocular' in text:
                        matched_tags.append('Perception/3D Perception')
                    else:
                        matched_tags.append('Perception/2D Perception')
                elif 'visual' in text or 'vision' in text or 'image' in text or 'video' in text:
                    if '3d' in text or 'pose' in text or 'depth' in text or 'monocular' in text or 'odometry' in text or 'inertial' in text or 'spatial' in text:
                        matched_tags.append('Perception/3D Perception')
                    else:
                        matched_tags.append('Perception/2D Perception')
                elif 'test-time' in text or 'adaptation' in text or 'test time' in text:
                    matched_tags.append('Learning/Imitation Learning')
                elif 'reasoning' in text or 'reasoner' in text:
                    matched_tags.append('Decision/Task Planning')
                elif 'vr' in text or 'telepresence' in text or 'virtual reality' in text or 'vr sickness' in text:
                    matched_tags.append('Operation/Teleoperation')
                elif 'odometry' in text or 'inertial odometry' in text:
                    matched_tags.append('Decision/Task Planning')
                elif 'navigation' in text or 'mapping' in text or 'exploration' in text:
                    matched_tags.append('Decision/Task Planning')
                elif 'learning' in text or 'model' in text or 'neural' in text or 'network' in text:
                    # 通用AI/ML相关，归类到模仿学习
                    matched_tags.append('Learning/Imitation Learning')
                else:
                    # 最后的AI相关兜底：归类到模仿学习
                    matched_tags.append('Learning/Imitation Learning')
            else:
                # 最后的兜底：保持未分类（可能是纯数学、物理等非AI领域）
        matched_tags.append(UNCATEGORIZED_KEY)
    
    return matched_tags


def reclassify_all_papers(dry_run: bool = True, batch_size: int = 100):
    """
    重新分类所有论文
    
    Args:
        dry_run: 是否为试运行（不实际更新数据库）
        batch_size: 批量处理大小
    """
    session = get_session()
    
    try:
        # 获取所有论文
        all_papers = session.query(Paper).all()
        total_count = len(all_papers)
        
        logger.info("=" * 60)
        logger.info(f"开始重新分类论文（{'试运行' if dry_run else '正式运行'}）")
        logger.info(f"论文总数: {total_count}")
        logger.info("=" * 60)
        
        # 统计信息
        stats = {
            "total": total_count,
            "updated": 0,
            "unchanged": 0,
            "uncategorized": 0,
            "by_category": defaultdict(int),
            "by_tag": defaultdict(int),
        }
        
        # 批量处理
        updated_papers = []
        
        for idx, paper in enumerate(all_papers, 1):
            # 分类
            new_tags = classify_paper_by_keywords(paper)
            primary_tag = new_tags[0] if new_tags else UNCATEGORIZED_KEY
            
            # 统计
            stats["by_category"][get_category_from_tag(primary_tag)] += 1
            stats["by_tag"][primary_tag] += 1
            
            if primary_tag == UNCATEGORIZED_KEY:
                stats["uncategorized"] += 1
            
            # 检查是否需要更新
            old_category = paper.category or ""
            if old_category != primary_tag:
                paper.category = primary_tag
                updated_papers.append(paper)
                stats["updated"] += 1
                
                if idx % 10 == 0:
                    logger.info(f"进度: {idx}/{total_count} | "
                              f"更新: {stats['updated']} | "
                              f"当前: {display_category(primary_tag)}")
            else:
                stats["unchanged"] += 1
            
            # 批量提交
            if not dry_run and len(updated_papers) >= batch_size:
                session.commit()
                logger.info(f"已提交 {len(updated_papers)} 条更新")
                updated_papers = []
        
        # 提交剩余更新
        if not dry_run and updated_papers:
            session.commit()
            logger.info(f"已提交剩余 {len(updated_papers)} 条更新")
        
        # 打印统计报告
        logger.info("=" * 60)
        logger.info("分类统计报告")
        logger.info("=" * 60)
        logger.info(f"总论文数: {stats['total']}")
        logger.info(f"已更新: {stats['updated']}")
        logger.info(f"未变化: {stats['unchanged']}")
        logger.info(f"未分类: {stats['uncategorized']}")
        logger.info("")
        logger.info("按分类统计:")
        for category, count in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
            logger.info(f"  {category}: {count}")
        logger.info("")
        logger.info("Top 10 标签:")
        for tag, count in sorted(stats['by_tag'].items(), key=lambda x: -x[1])[:10]:
            logger.info(f"  {display_category(tag)}: {count}")
        
        if dry_run:
            logger.info("")
            logger.info("⚠️  这是试运行，数据库未实际更新")
            logger.info("运行时不加 --dry-run 参数将正式更新数据库")
        
    except Exception as e:
        session.rollback()
        logger.error(f"重新分类失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    finally:
        session.close()


def get_category_from_tag(tag_key: str) -> str:
    """从标签键提取分类"""
    if '/' in tag_key:
        return tag_key.split('/')[0]
    return UNCATEGORIZED_KEY


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='重新分类所有论文')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='试运行模式（不实际更新数据库）')
    parser.add_argument('--execute', action='store_true',
                       help='正式执行（覆盖--dry-run）')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='批量处理大小')
    
    args = parser.parse_args()
    
    # 如果指定了--execute，则不是dry_run
    dry_run = not args.execute
    
    if not dry_run:
        # 直接执行，不需要确认
        logger.info("⚠️  开始更新数据库中的所有论文标签...")
    
    reclassify_all_papers(dry_run=dry_run, batch_size=args.batch_size)


if __name__ == '__main__':
    main()
