#!/usr/bin/env python3
"""
手动整理的数据集信息
从 https://juejin.cn/post/7475651131450327040 文章内容中手动整理

使用方法：
1. 阅读文章，整理数据集信息
2. 将数据集信息添加到下面的 datasets 列表中
3. 运行: python3 manual_datasets_data.py
"""
from save_datasets_to_db import batch_save_datasets
from datasets_models import init_datasets_db

# 手动整理的数据集信息
# 从 https://juejin.cn/post/7475651131450327040 文章内容中整理
# 格式：每个数据集包含 name, description, category, link, paper_link, tags

datasets = [
    # DROID数据集示例（完整格式）
    {
        'name': 'DROID',
        'description': '创建大型、多样化、高质量的机器人操作数据集是迈向更强大、更稳健的机器人操作策略的重要基石。然而，创建这样的数据集具有挑战性：在多样化环境中收集机器人操作数据会带来后勤和安全挑战，并且需要大量硬件和人力投入。研究人员引入了 DROID（分布式机器人交互数据集），这是一个多样化的机器人操作数据集。研究发现与利用现有大规模机器人操作数据集的最先进的方法相比，DROID 将策略性能、稳健性和通用性平均提高了20%。',
        'category': '操作',
        'publisher': 'Stanford University, UC Berkeley, Toyota Research Institute',
        'publish_date': '2024.03',
        'project_link': 'https://droid-dataset.github.io/',
        'paper_link': 'https://arxiv.org/abs/2403.12945',
        'dataset_link': 'https://droid-dataset.github.io/',
        'scale': 'DROID数据集共1.7TB数据，包含76,000个机器人演示轨迹，涵盖86个任务和564个场景',
        'source': 'juejin',
        'source_url': 'https://juejin.cn/post/7475651131450327040',
        'tags': ['操作', '机器人', '大规模']
    },
    # 从文章中提取的其他数据集（需要补充完整信息）
    {
        'name': 'AgiBot World',
        'description': 'AgiBot World是一个具身智能世界模型数据集，专注于构建和理解具身智能系统的世界模型。该数据集旨在支持具身智能代理在复杂环境中的感知、理解和决策能力。',
        'category': '多模态',
        'publisher': '',
        'publish_date': '',
        'project_link': 'https://huggingface.co/agibot-world',
        'paper_link': '',
        'dataset_link': 'https://huggingface.co/agibot-world',
        'scale': '数据集规模待补充',
        'source': 'juejin',
        'source_url': 'https://juejin.cn/post/7475651131450327040',
        'tags': ['具身智能', '世界模型', '多模态']
    },
    {
        'name': 'Open X-Embodiment',
        'description': 'Google DeepMind开放的大规模机器人操作数据集，整合了多个机器人操作数据集，旨在促进机器人学习的可扩展性和泛化能力。该数据集汇集了来自不同实验室和环境的多样化机器人操作演示数据。',
        'category': '操作',
        'publisher': 'Google DeepMind',
        'publish_date': '2023.10',
        'project_link': 'https://robotics-transformer.github.io/',
        'paper_link': 'https://arxiv.org/abs/2308.12952',
        'dataset_link': 'https://github.com/google-deepmind/open_x_embodiment',
        'scale': '整合了来自22个不同机器人平台的数据，包含超过100万个机器人演示轨迹',
        'source': 'juejin',
        'source_url': 'https://juejin.cn/post/7475651131450327040',
        'tags': ['操作', '机器人', '大规模', '多平台']
    },
    {
        'name': 'Robotics Transformer (RT-2)',
        'description': '机器人Transformer模型RT-2的相关数据集，结合视觉-语言-动作模型，能够将网络规模的语言和视觉预训练转移到机器人控制中。RT-2展示了强大的泛化能力和新兴能力，包括对未见过的物体的推理能力。',
        'category': '多模态',
        'publisher': 'Google DeepMind',
        'publish_date': '2023.07',
        'project_link': 'https://robotics-transformer2.github.io/',
        'paper_link': 'https://arxiv.org/abs/2307.15818',
        'dataset_link': 'https://robotics-transformer2.github.io/',
        'scale': '基于RT-1数据集，包含130,000个机器人演示，涵盖700多个任务',
        'source': 'juejin',
        'source_url': 'https://juejin.cn/post/7475651131450327040',
        'tags': ['多模态', 'Transformer', '机器人', '视觉语言动作']
    },
    {
        'name': 'BridgeData',
        'description': 'BridgeData是一个大规模机器人学习数据集，旨在促进可扩展的机器人学习研究。该数据集包含多样化的机器人操作演示，覆盖多种任务和环境。',
        'category': '操作',
        'publisher': 'UC Berkeley, RAIL Lab',
        'publish_date': '2022.06',
        'project_link': 'https://rail-berkeley.github.io/bridgedata',
        'paper_link': 'https://arxiv.org/abs/2206.12452',
        'dataset_link': 'https://rail-berkeley.github.io/bridgedata',
        'scale': '包含60,000多个机器人演示轨迹，涵盖多种操作任务',
        'source': 'juejin',
        'source_url': 'https://juejin.cn/post/7475651131450327040',
        'tags': ['操作', '机器人', '大规模']
    },
    {
        'name': 'BridgeData V2',
        'description': 'BridgeData V2是BridgeData数据集的升级版本，包含更大规模和更多样化的机器人操作数据。该数据集旨在促进可扩展的机器人学习研究，支持更复杂的操作任务和更广泛的泛化能力。',
        'category': '操作',
        'publisher': 'UC Berkeley, RAIL Lab',
        'publish_date': '2023.08',
        'project_link': 'https://rail-berkeley.github.io/bridgedata',
        'paper_link': 'https://arxiv.org/abs/2308.12952',
        'dataset_link': 'https://rail-berkeley.github.io/bridgedata',
        'scale': '包含60,096个轨迹，跨越24个不同的环境，涵盖更多样化的操作任务',
        'source': 'juejin',
        'source_url': 'https://juejin.cn/post/7475651131450327040',
        'tags': ['操作', '机器人', '大规模', '多样化']
    },
    {
        'name': 'Wild Robot Manipulation Dataset',
        'description': 'Wild Robot Manipulation Dataset（也称为DexWild）是一个野外灵巧人类交互数据集。该数据集包含多位数据收集者在多种环境和物体上使用人手进行的交互数据，通过DexWild-System设备记录，旨在提升机器人策略在真实环境中的泛化能力，特别是在新环境、任务和形态上的表现。',
        'category': '操作',
        'publisher': 'Carnegie Mellon University',
        'publish_date': '2025.05',
        'project_link': 'https://dexwild.github.io',
        'paper_link': 'https://arxiv.org/abs/2505.07813',
        'dataset_link': 'https://dexwild.github.io',
        'scale': '包含数小时的交互数据，涵盖多种环境和物体，由多样化的团队收集',
        'source': 'juejin',
        'source_url': 'https://juejin.cn/post/7475651131450327040',
        'tags': ['操作', '机器人', '真实场景', '灵巧操作', '野外数据']
    },
    
    # 提示：以下数据集需要根据文章完整内容补充详细信息
    # 建议阅读文章后，补充以下字段：
    # - description: 详细描述
    # - link: 完整链接
    # - paper_link: 相关论文链接
    # - tags: 更准确的标签
]

if __name__ == "__main__":
    print("=" * 60)
    print("保存手动整理的数据集信息")
    print("=" * 60)
    
    # 确保数据库已初始化
    init_datasets_db()
    
    # 批量保存
    stats = batch_save_datasets(datasets)
    
    print("\n" + "=" * 60)
    print("保存完成")
    print("=" * 60)
    print(f"总计: {stats['total']} 条")
    print(f"新建: {stats['created']} 条")
    print(f"更新: {stats['updated']} 条")
    print(f"跳过: {stats['skipped']} 条")
    print(f"错误: {stats['error']} 条")
    print("\n提示: 请根据文章内容继续添加更多数据集信息到 datasets 列表中")

