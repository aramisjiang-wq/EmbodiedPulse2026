#!/usr/bin/env python3
"""
具身智能新闻关键词配置
涵盖具身机器人领域所有关键词，包括公司融资、新技术等
"""

# 核心具身智能关键词
CORE_EMBODIED_KEYWORDS = [
    # 英文
    'embodied ai', 'embodied intelligence', 'embodied agent', 'embodied cognition',
    'embodied learning', 'embodied robotics', 'embodied system',
    # 中文
    '具身智能', '具身AI', '具身机器人', '具身认知', '具身学习',
    '具身系统', '具身交互', '具身感知', '具身决策', '具身执行'
]

# 机器人相关关键词
ROBOTICS_KEYWORDS = [
    # 英文
    'robotics', 'robot', 'robotic', 'robotic system', 'robotic platform',
    'autonomous robot', 'intelligent robot', 'service robot', 'industrial robot',
    'mobile robot', 'humanoid robot', 'humanoid', 'bipedal robot', 'quadruped robot',
    'legged robot', 'wheeled robot', 'flying robot', 'drone', 'uav',
    'manipulator', 'robotic arm', 'robotic hand', 'gripper', 'end effector',
    # 中文
    '机器人', '机器人系统', '机器人平台', '自主机器人', '智能机器人',
    '服务机器人', '工业机器人', '移动机器人', '人形机器人', '双足机器人',
    '四足机器人', '腿式机器人', '轮式机器人', '飞行机器人', '无人机',
    '机械臂', '机器人手臂', '机器人手', '抓取器', '末端执行器'
]

# 研究方向关键词
RESEARCH_KEYWORDS = [
    # 感知层
    'visual perception', 'scene understanding', 'object detection', 'semantic segmentation',
    'depth estimation', 'optical flow', 'visual odometry', 'slam', 'simultaneous localization',
    '视觉感知', '场景理解', '目标检测', '语义分割', '深度估计', '光流', '视觉里程计',
    
    # 决策层
    'task planning', 'path planning', 'motion planning', 'trajectory planning',
    'navigation', 'pathfinding', 'route planning', 'action planning',
    '任务规划', '路径规划', '运动规划', '轨迹规划', '导航', '路径搜索', '动作规划',
    
    # 学习层
    'reinforcement learning', 'imitation learning', 'robot learning', 'deep rl',
    'policy learning', 'skill learning', 'transfer learning', 'meta learning',
    '强化学习', '模仿学习', '机器人学习', '深度强化学习', '策略学习', '技能学习',
    
    # 执行层
    'manipulation', 'grasping', 'dexterous manipulation', 'fine manipulation',
    'locomotion', 'walking', 'running', 'jumping', 'balancing',
    '操作', '抓取', '灵巧操作', '精细操作', '移动', '行走', '跑步', '跳跃', '平衡',
    
    # 多模态
    'vision language model', 'vlm', 'vision language action', 'vla',
    'multimodal learning', 'visual language', 'vision language',
    '视觉语言模型', '多模态学习', '视觉语言', '视觉语言动作',
    
    # 其他
    'sim-to-real', 'sim2real', 'simulation', 'simulator',
    'world model', 'dynamics model', 'physics engine',
    '仿真到现实', '仿真', '世界模型', '动力学模型'
]

# 公司融资相关关键词
COMPANY_FUNDING_KEYWORDS = [
    # 融资相关
    'funding', 'fundraise', 'fundraising', 'investment', 'investor', 'venture capital',
    'series a', 'series b', 'series c', 'seed round', 'angel round', 'ipo',
    '融资', '投资', '融资轮次', 'a轮', 'b轮', 'c轮', '种子轮', '天使轮', '上市',
    '获得投资', '完成融资', '融资成功', '估值', '独角兽',
    
    # 具身智能公司（知名公司）
    'agility robotics', 'boston dynamics', 'tesla', 'tesla bot', 'optimus',
    'figure ai', '1x robotics', 'sanctuary ai', 'apptronik', 'halodi robotics',
    'limx dynamics', '逐际动力', '宇树科技', 'unitree', '小米', 'xiaomi',
    '优必选', 'ubtech', '达闼科技', 'cloudminds', '傅利叶智能', 'fourier intelligence',
    '智元机器人', 'agibot', '宇树科技', 'unitree', '追觅科技', 'dreame',
    '开普勒机器人', 'kepler', '星动纪元', '星动纪元', '智元机器人', 'agibot',
    '逐际动力', 'limx', 'gradmotion', 'grad motion',
    
    # 公司动态
    'company', 'startup', 'unicorn', 'valuation', 'revenue',
    '公司', '创业公司', '独角兽', '估值', '营收', '产品发布', '新品发布'
]

# 新技术关键词
NEW_TECH_KEYWORDS = [
    # 新技术突破
    'breakthrough', 'innovation', 'new technology', 'advancement', 'milestone',
    '突破', '创新', '新技术', '进展', '里程碑', '重大突破', '技术突破',
    
    # 产品发布
    'product launch', 'new product', 'release', 'announcement', 'unveil',
    '产品发布', '新品发布', '发布', '宣布', '推出', '亮相',
    
    # 技术特性
    'autonomous', 'intelligent', 'ai-powered', 'ml-powered', 'neural',
    'autonomous driving', 'self-driving', 'driverless',
    '自主', '智能', 'ai驱动', '机器学习驱动', '神经网络',
    '自动驾驶', '无人驾驶',
    
    # 应用场景
    'warehouse', 'logistics', 'manufacturing', 'healthcare', 'elderly care',
    'service', 'delivery', 'inspection', 'surveillance', 'security',
    '仓库', '物流', '制造', '医疗', '养老', '服务', '配送', '巡检', '安防'
]

# 综合关键词列表（用于搜索）
ALL_EMBODIED_KEYWORDS = (
    CORE_EMBODIED_KEYWORDS +
    ROBOTICS_KEYWORDS +
    RESEARCH_KEYWORDS +
    COMPANY_FUNDING_KEYWORDS +
    NEW_TECH_KEYWORDS
)

# 用于RSS过滤的关键词（更宽松，确保不遗漏，但避免误匹配）
RSS_FILTER_KEYWORDS = [
    # 核心词（必须包含）
    'embodied', 'robot', 'robotics', '具身', '机器人',
    # 研究方向（需要配合核心词使用）
    'perception', 'planning', 'manipulation', 'locomotion', 'learning',
    '感知', '规划', '操作', '移动', '学习',
    # 公司/融资（需要配合核心词使用）
    'funding', 'investment', 'startup', '融资', '投资', '公司',
    # 新技术（需要配合核心词使用）
    'breakthrough', 'innovation', 'new', '突破', '创新', '新技术',
    # AI相关（需要配合核心词使用）
    'ai', 'artificial intelligence', 'machine learning', 'deep learning',
    '人工智能', '机器学习', '深度学习'
]

# RSS过滤排除词（这些词出现时，必须同时有机器人核心词）
RSS_EXCLUDE_KEYWORDS = [
    '高铁', 'high-speed rail', 'railway', '铁路',
    '迪士尼', 'disney', 'disneyland',
    '十五五', '十四五', '十三五', '五年规划',
    '城市规划', '交通规划', '经济规划', '旅游规划',
    '海南', 'hainan', '上海', 'shanghai', '北京', 'beijing',
    '旅游', 'tourism', '主题公园', 'theme park',
    '地铁', 'subway', 'metro', '轨道交通',
    '基础设施建设', 'infrastructure', '建设', 'construction',
]

# 用于NewsAPI搜索的查询字符串
NEWSAPI_QUERIES = [
    # 核心查询
    'embodied AI OR embodied intelligence OR 具身智能',
    'robotics OR robot OR 机器人',
    'humanoid robot OR 人形机器人',
    # 研究方向
    'robot learning OR robot manipulation OR robot locomotion',
    '机器人学习 OR 机器人操作 OR 机器人移动',
    # 公司融资
    'robot startup funding OR 机器人公司融资',
    'robotics investment OR 机器人投资',
    # 新技术
    'robot breakthrough OR 机器人突破',
    'new robot technology OR 新机器人技术'
]

# 公司名称列表（用于匹配）
COMPANY_NAMES = [
    # 国外公司
    'agility robotics', 'boston dynamics', 'tesla', 'figure ai', '1x robotics',
    'sanctuary ai', 'apptronik', 'halodi robotics', 'unitree', 'gradmotion',
    # 国内公司
    'limx', '逐际动力', '宇树科技', 'unitree', '小米', 'xiaomi',
    '优必选', 'ubtech', '达闼科技', 'cloudminds', '傅利叶智能', 'fourier',
    '智元机器人', 'agibot', '追觅科技', 'dreame', '开普勒', 'kepler',
    '星动纪元', 'gradmotion'
]

def is_embodied_related(text: str, strict: bool = False) -> bool:
    """
    判断文本是否与具身智能相关（优化版，减少误匹配）
    
    Args:
        text: 文本内容（标题+描述）
        strict: 是否严格模式
    
    Returns:
        是否相关
    """
    text_lower = text.lower()
    
    if strict:
        # 严格模式：必须包含核心关键词
        for keyword in CORE_EMBODIED_KEYWORDS + ROBOTICS_KEYWORDS:
            if keyword.lower() in text_lower:
                return True
        return False
    
    # 宽松模式：必须包含核心词（机器人/具身）或特定组合
    # 核心词：必须包含机器人或具身相关词
    core_required_keywords = [
        # 英文核心词
        'robot', 'robotics', 'robotic', 'humanoid', 'manipulator', 'gripper',
        'embodied', 'embodied ai', 'embodied intelligence',
        # 中文核心词
        '机器人', '具身', '具身智能', '具身ai', '人形机器人', '机械臂', '抓取'
    ]
    
    # 检查是否包含核心词
    has_core_keyword = any(kw in text_lower for kw in core_required_keywords)
    
    # 检查是否包含已知的具身智能公司名称（即使没有明确提到"机器人"）
    has_company_name = any(company.lower() in text_lower for company in COMPANY_NAMES)
    
    # 如果包含公司名称，也认为相关（因为这些公司都是具身智能/机器人公司）
    if has_company_name:
        return True
    
    # 如果没有核心词，直接返回False（避免误匹配）
    if not has_core_keyword:
        return False
    
    # 排除明显不相关的词（除非同时包含机器人相关词）
    exclude_keywords = [
        # 电子设备
        '手机', 'mobile phone', 'iphone', 'android phone', 'smartphone',
        '电脑', 'computer', 'laptop', 'pc',
        # 智能家居/消费电子
        '智能家居', 'smart home', 'home automation',
        '智能音箱', 'smart speaker', 'alexa', 'siri',
        # 自动驾驶（非机器人）
        '自动驾驶', 'self-driving car', 'autonomous vehicle', 'driverless car',  # 除非明确提到机器人
        # AI芯片（非机器人）
        'ai芯片', 'ai chip', '芯片', 'chip',  # 除非明确提到机器人
        # 大模型/LLM（非机器人）
        'chatgpt', 'gpt', 'llm', '大模型', 'large language model',  # 除非明确提到机器人
        # 基础设施/交通（非机器人）
        '高铁', 'high-speed rail', 'railway', '铁路', '轨道交通',
        '地铁', 'subway', 'metro', '交通', 'transportation',
        '基础设施建设', 'infrastructure', '建设', 'construction',
        # 旅游/娱乐（非机器人）
        '迪士尼', 'disney', 'disneyland', '主题公园', 'theme park',
        '旅游', 'tourism', 'travel', '景点', 'attraction',
        # 规划/政策（非机器人，除非明确提到机器人）
        '十五五', '十四五', '十三五', '五年规划', '规划', 'planning',  # 除非明确提到机器人
        '海南', 'hainan', '上海', 'shanghai', '北京', 'beijing',  # 地名，除非明确提到机器人
        '政策', 'policy', '法规', 'regulation', '法律', 'law',
        # 经济/金融（非机器人）
        '经济发展', 'economic', 'gdp', '投资', 'investment',  # 除非是机器人公司融资
        '股票', 'stock', '股市', 'market', '金融', 'finance',
        # 其他不相关
        '医疗', 'healthcare', '教育', 'education', '农业', 'agriculture',
    ]
    
    has_exclude = any(kw in text_lower for kw in exclude_keywords)
    
    # 如果包含排除词，必须同时包含机器人核心词才认为相关
    if has_exclude:
        # 检查是否有明确的机器人上下文
        robot_context_keywords = [
            'robot', 'robotics', '机器人', 'embodied', '具身',
            'humanoid', '人形', 'manipulator', '机械臂'
        ]
        # 对于某些强排除词（如：高铁、迪士尼、规划等），需要更严格的检查
        strong_exclude_keywords = [
            '高铁', 'high-speed rail', 'railway', '铁路',
            '迪士尼', 'disney', 'disneyland',
            '十五五', '十四五', '十三五', '五年规划',
            '海南', 'hainan', '上海', 'shanghai', '北京', 'beijing',
            '旅游', 'tourism', '主题公园', 'theme park',
            '地铁', 'subway', 'metro', '轨道交通',
        ]
        has_strong_exclude = any(kw in text_lower for kw in strong_exclude_keywords)
        
        if has_strong_exclude:
            # 强排除词：必须明确包含机器人相关词才匹配（如"机器人路径规划"可以，但"城市规划"不行）
            robot_specific_keywords = [
                'robot', 'robotics', '机器人', 'embodied', '具身',
                'humanoid', '人形', 'manipulator', '机械臂',
                '机器人规划', 'robot planning', 'robotic planning'  # 明确的机器人规划
            ]
            if not any(kw in text_lower for kw in robot_specific_keywords):
                return False
        
        # 其他排除词：需要机器人上下文
        if not any(kw in text_lower for kw in robot_context_keywords):
            return False
    
    # 特殊处理：如果只有通用AI/ML关键词，需要同时有机器人上下文
    generic_ai_keywords = [
        'artificial intelligence', 'ai', '人工智能', '智能',
        'machine learning', 'ml', '机器学习', '深度学习', 'deep learning'
    ]
    
    has_generic_ai = any(kw in text_lower for kw in generic_ai_keywords)
    has_robot_context = any(kw in text_lower for kw in core_required_keywords)
    
    # 如果只有通用AI关键词，没有机器人上下文，不认为相关
    if has_generic_ai and not has_robot_context:
        return False
    
    # 特殊处理：自动驾驶相关，除非明确提到机器人
    if 'autonomous' in text_lower or '自主' in text_lower or '自动驾驶' in text_lower:
        if 'robot' not in text_lower and '机器人' not in text_lower and 'robotics' not in text_lower:
            # 可能是自动驾驶汽车，不是机器人
            if 'car' in text_lower or 'vehicle' in text_lower or '汽车' in text_lower or '车' in text_lower or 'robotaxi' in text_lower:
                return False
    
    # 特殊处理：Robotaxi（自动驾驶出租车），不是机器人
    if 'robotaxi' in text_lower:
        if 'robot' not in text_lower or 'robotics' not in text_lower:
            # Robotaxi是自动驾驶，不是机器人（除非明确提到机器人）
            return False
    
    # 特殊处理：通用商业/经济新闻，即使包含AI也不匹配
    business_keywords = [
        '商业', 'business', '公司', 'company', '行业', 'industry',
        '经济', 'economic', '市场', 'market', '投资', 'investment',
        '出海', '国际化', '全球化', 'global',
    ]
    has_business = any(kw in text_lower for kw in business_keywords)
    if has_business:
        # 如果是纯商业新闻（没有机器人核心词），不匹配
        if not has_core_keyword and not has_company_name:
            return False
    
    # 特殊处理：通用AI会议/论坛，除非明确提到机器人
    if 'ai' in text_lower or '人工智能' in text_lower:
        if '会议' in text_lower or '论坛' in text_lower or 'conference' in text_lower or 'forum' in text_lower:
            # AI会议/论坛，除非明确提到机器人，不匹配
            if not has_core_keyword and not has_company_name:
                return False
    
    # 如果通过了所有检查，且有核心词，认为相关
    return has_core_keyword

def get_search_queries() -> list:
    """
    获取用于搜索的查询字符串列表
    
    Returns:
        查询字符串列表
    """
    return NEWSAPI_QUERIES

def get_filter_keywords() -> list:
    """
    获取用于过滤的关键词列表
    
    Returns:
        关键词列表
    """
    return RSS_FILTER_KEYWORDS

