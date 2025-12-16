"""
论文标签体系统一配置与工具函数（新版本 - 扁平化结构）

基于图片中的标签体系定义：
- 6大分类：感知层、决策层、运动层、操作层、学习与算法、基准
- 扁平化标签结构，每个标签包含：中文术语、英文术语、检索词
"""
from collections import OrderedDict
from typing import Dict, List, Tuple

# 新标签体系定义（基于图片内容）
# 格式：{标签键: (中文术语, 英文术语, [检索词列表])}
NEW_TAXONOMY = {
    # 1. 感知层（Perception Layer）
    "Perception/2D Perception": ("2D感知", "2D Perception", ["perception"]),
    "Perception/3D Perception": ("3D感知", "3D Perception", ["3d perception"]),
    "Perception/Object Detection": ("目标检测", "Object Detection", ["detect"]),
    "Perception/Instance Segmentation": ("实例分割", "Instance Segmentation", ["segment"]),
    "Perception/Vision-Language Model": ("视觉语言模型", "Vision-Language Model", ["vision language model"]),
    "Perception/Image Captioning": ("图像描述生成", "Image Captioning", ["caption"]),
    "Perception/Point Cloud": ("点云表示", "Point Cloud", ["point cloud"]),
    "Perception/Voxel Representation": ("体素表示", "Voxel Representation", ["voxel"]),
    "Perception/3D Scene Understanding": ("三维场景理解", "3D Scene Understanding", ["point cloud", "3DGS", "voxel"]),
    "Perception/Affordance Generation": ("可操作性", "Affordance Generation", ["affordance"]),
    "Perception/Image Video Generation": ("图像视频生成", "Image/Video Generation", ["image generation", "video generation"]),
    "Perception/Generative Models": ("生成模型", "Generative Models", ["generative models"]),
    "Perception/Semantic Understanding": ("语义理解", "Semantic Understanding", ["semantic understanding"]),
    "Perception/Graph Modeling": ("图建模", "Graph Modeling", ["graph"]),
    "Perception/Historical Modeling": ("历史信息建模", "Historical Modeling", ["history modeling"]),
    "Perception/Chain of Thought": ("思维链", "Chain of Thought", ["chain of thought"]),
    
    # 2. 决策层（Decision Layer）
    "Decision/Task Planning": ("任务规划", "Task Planning", ["planning"]),
    "Decision/Whole-Body Control": ("全身控制", "Whole-Body Control", ["whole body control"]),
    
    # 3. 运动层（Motion Control Layer）
    "Motion Control/Locomotion Control": ("腿式运动控制", "Locomotion Control", ["locomotion"]),
    "Motion Control/Humanoid Robot": ("人形机器人", "Humanoid Robot", ["humanoid"]),
    "Motion Control/Quadruped Robot": ("四足机器人", "Quadruped Robot", ["quadruped"]),
    "Motion Control/Mobile Manipulation": ("移动操作", "Mobile Manipulation", ["mobile manipulation"]),
    "Motion Control/Motion Retargeting": ("动作重定向", "Motion Retargeting", ["retargeting"]),
    "Motion Control/Teleoperation": ("遥操作", "Teleoperation", ["teleoperation"]),
    
    # 4. 操作层（Operation Layer）
    "Operation/Grasp": ("抓取", "Grasp", ["grasp"]),
    "Operation/Bimanual Manipulation": ("双手操作", "Bimanual Manipulation", ["bimanual"]),
    "Operation/Dexterous Hands": ("灵巧手", "Dexterous Hands", ["dexterous"]),
    "Operation/Vision-Language-Action Models": ("视觉语言动作模型", "Vision-Language-Action Models", ["vision language action"]),
    "Operation/Policy": ("策略", "Policy", ["policy"]),
    
    # 5. 学习与算法（Learning & Algorithms）
    "Learning/Reinforcement Learning": ("强化学习", "Reinforcement Learning", ["reinforcement learning"]),
    "Learning/Imitation Learning": ("模仿学习", "Imitation Learning", ["imitation learning"]),
    "Learning/Lightweight Model": ("轻量化模型", "Lightweight Model", ["lightweight"]),
    
    # 6. 基准（Benchmark）
    "Benchmark/Benchmark": ("评测基准", "Benchmark", ["embodied benchmark"]),
}

# 分类显示名称
CATEGORY_DISPLAY_NAMES = {
    "Perception": "感知层",
    "Decision": "决策层",
    "Motion Control": "运动层",
    "Operation": "操作层",
    "Learning": "学习与算法",
    "Benchmark": "基准",
}

# 构建显示映射和顺序
def _build_display_maps():
    """构建标签显示映射和顺序"""
    display = OrderedDict()
    order = []
    alias_map = {}
    
    for tag_key, (chinese, english, keywords) in NEW_TAXONOMY.items():
        # 显示格式：中文术语 / 英文术语
        display[tag_key] = f"{chinese} / {english}"
        order.append(tag_key)
        
        # 别名映射：支持中文、英文、关键词匹配
        alias_map[chinese.lower()] = tag_key
        alias_map[english.lower()] = tag_key
        alias_map[tag_key.lower()] = tag_key
        
        # 关键词别名
        for keyword in keywords:
            alias_map[keyword.lower()] = tag_key
        
        # 分类别名（映射到分类下的第一个标签）
        category = tag_key.split('/')[0]
        if category not in alias_map:
            alias_map[category.lower()] = tag_key
    
    return display, order, alias_map

CATEGORY_DISPLAY, CATEGORY_ORDER, _ALIAS_LOOKUP = _build_display_maps()

# 未分类标签
UNCATEGORIZED_KEY = "Uncategorized"
UNCATEGORIZED_KEYS = {"", "none", "null", "uncategorized", "unknown", "其它", "其他", "未分类"}


def normalize_category(category: str) -> str:
    """
    归一化标签到新标签键
    
    Args:
        category: 输入的标签字符串
    
    Returns:
        规范化后的标签键，未匹配返回 'Uncategorized'
    """
    if category is None:
        return UNCATEGORIZED_KEY
    
    raw = str(category).strip()
    if not raw or raw.lower() in UNCATEGORIZED_KEYS:
        return UNCATEGORIZED_KEY
    
    # 直接匹配
    if raw in CATEGORY_DISPLAY:
        return raw
    
    # 尝试规范化格式匹配
    normalized = raw.replace(" ", "").replace("_", "/")
    if normalized in CATEGORY_DISPLAY:
        return normalized
    
    # 别名匹配
    folded = raw.lower()
    if folded in _ALIAS_LOOKUP:
        return _ALIAS_LOOKUP[folded]
    
    # 部分匹配（查找包含关键词的标签）
    for tag_key, (chinese, english, keywords) in NEW_TAXONOMY.items():
        if folded in chinese.lower() or folded in english.lower():
            return tag_key
        for keyword in keywords:
            if folded in keyword.lower():
                return tag_key
    
    return UNCATEGORIZED_KEY


def display_category(category: str) -> str:
    """
    返回标签显示名称（中文 / 英文）
    
    Args:
        category: 标签键
    
    Returns:
        显示名称
    """
    if not category or category == UNCATEGORIZED_KEY:
        return "未分类 / Uncategorized"
    return CATEGORY_DISPLAY.get(category, category)


def get_category_meta() -> Dict:
    """
    提供前端/接口的标签元数据
    
    Returns:
        包含标签顺序、显示名称、检索词的字典
    """
    return {
        "order": CATEGORY_ORDER,
        "display": CATEGORY_DISPLAY,
        "taxonomy": NEW_TAXONOMY,
        "categories": CATEGORY_DISPLAY_NAMES,
        "uncategorized": UNCATEGORIZED_KEY,
    }


def get_search_keywords(tag_key: str) -> List[str]:
    """
    获取标签对应的检索词列表
    
    Args:
        tag_key: 标签键
    
    Returns:
        检索词列表
    """
    if tag_key in NEW_TAXONOMY:
        return NEW_TAXONOMY[tag_key][2]  # 返回检索词列表
    return []


def get_category_from_tag(tag_key: str) -> str:
    """
    从标签键提取分类
    
    Args:
        tag_key: 标签键（格式：分类/标签）
    
    Returns:
        分类名称
    """
    if '/' in tag_key:
        return tag_key.split('/')[0]
    return UNCATEGORIZED_KEY


def build_category_tree() -> Dict:
    """
    构建分类树结构（用于前端显示）
    
    Returns:
        嵌套的分类树
    """
    tree = {}
    for tag_key, (chinese, english, keywords) in NEW_TAXONOMY.items():
        category = get_category_from_tag(tag_key)
        if category not in tree:
            tree[category] = {
                "display": CATEGORY_DISPLAY_NAMES.get(category, category),
                "tags": []
            }
        tree[category]["tags"].append({
            "key": tag_key,
            "display": f"{chinese} / {english}",
            "chinese": chinese,
            "english": english,
            "keywords": keywords
        })
    return tree
