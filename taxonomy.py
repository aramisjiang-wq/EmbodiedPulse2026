"""
论文标签体系统一配置与工具函数（新版本 - 扁平化结构）

基于图片中的标签体系定义：
- 6大分类：感知与理解、决策、运动控制、操作与交互、学习与算法、基准
- 扁平化标签结构，每个标签包含：中文术语、英文术语、检索词
"""
from collections import OrderedDict
from typing import Dict, List, Tuple

# 新标签体系定义（基于图片内容 - 扩充版）
# 格式：{标签键: (中文术语, 英文术语, [检索词列表])}
NEW_TAXONOMY = {
    # 1. 感知与理解（Perception & Understanding）
    "Perception/2D Perception": ("2D感知", "2D Perception", [
        "2d perception", "visual perception", "scene perception", 
        "image understanding", "visual understanding", "rgb image",
        "camera", "visual observation", "visual input"
    ]),
    "Perception/3D Perception": ("3D感知", "3D Perception", [
        "3d perception", "3d vision", "depth perception", "spatial perception",
        "3d understanding", "volumetric", "depth estimation", "stereo vision",
        "depth map", "depth sensing", "3d sensing", "rgbd"
    ]),
    "Perception/Object Detection": ("目标检测", "Object Detection", [
        "detect", "detection", "object detection", "object recognition",
        "object tracking", "tracking", "mot", "multi-object tracking"
    ]),
    "Perception/Instance Segmentation": ("实例分割", "Instance Segmentation", [
        "segment", "segmentation", "instance segmentation", "semantic segmentation",
        "panoptic segmentation", "mask"
    ]),
    "Perception/Vision-Language Model": ("视觉语言模型", "Vision-Language Model", [
        "vision language model", "vlm", "vision language", "multimodal",
        "visual language", "clip", "blip", "vision-language", "vqa",
        "visual question answering", "visual grounding", "grounding",
        "foundation model", "large vision-language model", "lvlm",
        "multimodal model", "vision-language understanding"
    ]),
    "Perception/Image Captioning": ("图像描述生成", "Image Captioning", [
        "caption", "captioning", "image captioning", "image description",
        "visual description"
    ]),
    "Perception/Point Cloud": ("点云表示", "Point Cloud", [
        "point cloud", "pointcloud", "lidar", "3d point", "point net",
        "pointnet", "point cloud processing", "point cloud learning",
        "point cloud segmentation", "point-based", "lidar perception"
    ]),
    "Perception/Voxel Representation": ("体素表示", "Voxel Representation", [
        "voxel", "volumetric representation", "voxel grid", "voxelization",
        "occupancy grid", "3d voxel", "voxel-based", "volumetric",
        "occupancy map"
    ]),
    "Perception/3D Scene Understanding": ("三维场景理解", "3D Scene Understanding", [
        "3d scene", "scene understanding", "scene reconstruction", "3dgs",
        "gaussian splatting", "nerf", "scene representation", "spatial understanding",
        "scene modeling", "3d reconstruction", "spatial intelligence",
        "world model", "3d understanding", "spatial representation",
        "scene perception", "environment understanding", "spatial mapping",
        "world modeling"
    ]),
    "Perception/Affordance Generation": ("可操作性", "Affordance Generation", [
        "affordance", "affordance prediction", "affordance detection",
        "graspability"
    ]),
    "Perception/Image Video Generation": ("图像视频生成", "Image/Video Generation", [
        "image generation", "video generation", "image synthesis",
        "video synthesis", "diffusion", "gan", "text to image",
        "text to video", "video diffusion", "stable diffusion",
        "generative adversarial"
    ]),
    "Perception/Generative Models": ("生成模型", "Generative Models", [
        "generative model", "generative", "generation", "synthesis",
        "transformer", "llm", "large language model", "gpt", "language model"
    ]),
    "Perception/Semantic Understanding": ("语义理解", "Semantic Understanding", [
        "semantic understanding", "semantic", "semantic reasoning",
        "semantic analysis"
    ]),
    
    # 2. 决策（Decision Making）
    "Decision/Graph Modeling": ("图建模", "Graph Modeling", [
        "graph modeling", "graph neural", "gnn", "knowledge graph",
        "scene graph", "graph network", "graph representation",
        "graph-based", "graph structure"
    ]),
    "Decision/Historical Modeling": ("历史信息建模", "Historical Modeling", [
        "history modeling", "historical", "memory", "temporal modeling",
        "memory bank", "episodic", "memory network", "temporal history",
        "experience replay", "historical information", "past experience",
        "recurrent", "lstm", "temporal reasoning", "sequential memory",
        "memory replay", "temporal context"
    ]),
    "Decision/Chain of Thought": ("思维链", "Chain of Thought", [
        "chain of thought", "cot", "reasoning chain", "step by step",
        "reasoning process", "thought process", "step-by-step reasoning"
    ]),
    "Decision/Task Planning": ("任务规划", "Task Planning", [
        "planning", "task planning", "motion planning", "path planning",
        "trajectory planning", "navigation", "task decomposition",
        "hierarchical planning", "task execution", "long-horizon",
        "multi-step", "sequential decision", "autonomous navigation",
        "task and motion planning", "tamp"
    ]),
    
    # 3. 运动控制（Motion Control）
    "Motion Control/Whole-Body Control": ("全身控制", "Whole-Body Control", [
        "whole body control", "whole-body", "full body control",
        "coordinated control", "whole-body coordination", "full-body motion",
        "whole body motion", "full body", "coordinated movement",
        "humanoid motion", "humanoid control", "multi-limb", "coordination"
    ]),
    "Motion Control/Locomotion Control": ("腿式运动控制", "Locomotion Control", [
        "locomotion", "walking", "legged", "gait", "bipedal locomotion",
        "quadrupedal locomotion", "navigation control"
    ]),
    "Motion Control/Humanoid Robot": ("人形机器人", "Humanoid Robot", [
        "humanoid", "humanoid robot", "bipedal robot", "human-like robot",
        "anthropomorphic"
    ]),
    "Motion Control/Quadruped Robot": ("四足机器人", "Quadruped Robot", [
        "quadruped", "quadrupedal", "four-legged", "legged robot"
    ]),
    "Motion Control/Mobile Manipulation": ("移动操作", "Mobile Manipulation", [
        "mobile manipulation", "mobile manipulator", "loco-manipulation",
        "navigation and manipulation"
    ]),
    "Motion Control/Motion Retargeting": ("动作重定向", "Motion Retargeting", [
        "retargeting", "motion retargeting", "motion transfer",
        "motion mapping"
    ]),
    
    # 4. 操作与交互（Operation & Interaction）
    "Operation/Teleoperation": ("遥操作", "Teleoperation", [
        "teleoperation", "remote control", "remote operation", "tele-operation",
        "human robot interaction", "hri", "telerobotics", "remote manipulation",
        "teleoperator", "remote robot", "shared autonomy", "haptic",
        "human-in-the-loop", "bilateral control", "virtual reality robot",
        "vr robot", "ar robot"
    ]),
    "Operation/Grasp": ("抓取", "Grasp", [
        "grasp", "grasping", "grip", "pick and place", "object manipulation",
        "manipulation", "manipulate", "robotic manipulation", "arm manipulation",
        "pick", "place", "tool use", "tool manipulation", "object interaction",
        "pick-and-place", "robot manipulation", "vision-based manipulation",
        "visual manipulation", "6dof", "6-dof", "grasp detection",
        "grasp planning", "grasp synthesis", "grasp prediction"
    ]),
    "Operation/Bimanual Manipulation": ("双手操作", "Bimanual Manipulation", [
        "bimanual", "dual arm", "dual-arm", "two-arm", "two-handed",
        "coordinated manipulation", "bilateral", "two arms"
    ]),
    "Operation/Dexterous Hands": ("灵巧手", "Dexterous Hands", [
        "dexterous", "dexterous hand", "dextrous", "dexterous manipulation",
        "fine manipulation", "finger manipulation", "hand manipulation",
        "in-hand", "finger gaiting"
    ]),
    "Operation/Vision-Language-Action Models": ("视觉语言动作模型", "Vision-Language-Action Models", [
        "vision language action", "vla", "embodied agent", "embodied ai",
        "multimodal agent", "vision-language-action", "embodied intelligence",
        "autonomous agent", "intelligent agent", "vision-language model for",
        "vlm for robot", "foundation model for robot", "multimodal for robot"
    ]),
    "Operation/Policy": ("策略", "Policy", [
        "policy", "control policy", "behavior policy", "visuomotor policy",
        "robot policy", "end-to-end policy", "neural policy", "learned policy",
        "controller", "control", "visuomotor", "sensorimotor",
        "action prediction"
    ]),
    
    # 5. 学习与算法（Learning & Algorithms）
    "Learning/Reinforcement Learning": ("强化学习", "Reinforcement Learning", [
        "reinforcement learning", "rl", "deep reinforcement learning",
        "deep rl", "q-learning", "actor-critic", "ppo", "sac", "td3",
        "reward", "markov decision", "mdp", "value function", "off-policy",
        "on-policy", "model-free", "model-based rl", "reinforcement",
        "reward function", "reward shaping"
    ]),
    "Learning/Imitation Learning": ("模仿学习", "Imitation Learning", [
        "imitation learning", "il", "behavioral cloning", "learning from demonstration",
        "demonstration learning", "behavior cloning", "lfd", "inverse reinforcement",
        "learning from human", "expert demonstration", "learning from data",
        "demonstration data"
    ]),
    "Learning/Lightweight Model": ("轻量化模型", "Lightweight Model", [
        "lightweight", "efficient", "compression", "quantization",
        "pruning", "distillation", "model compression", "efficient model",
        "low-latency", "real-time", "edge deployment"
    ]),
    
    # 6. 基准（Benchmark）
    "Benchmark/Benchmark": ("评测基准", "Benchmark", [
        "embodied benchmark"
    ]),
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


# ===== 兼容旧版API的函数 =====
def split_leaf_key(leaf: str) -> Tuple[str, str, str]:
    """
    兼容函数：拆分标签键（新版为扁平化结构）
    
    Args:
        leaf: 标签键
    
    Returns:
        (分类, 标签, 标签键)
    """
    if not leaf or leaf == UNCATEGORIZED_KEY:
        return (UNCATEGORIZED_KEY, UNCATEGORIZED_KEY, UNCATEGORIZED_KEY)
    
    if '/' in leaf:
        parts = leaf.split('/')
        if len(parts) >= 2:
            return (parts[0], parts[1], leaf)
    
    return (UNCATEGORIZED_KEY, UNCATEGORIZED_KEY, leaf)


def build_nested_from_flat(flat: Dict[str, any]) -> Dict[str, Dict[str, any]]:
    """
    兼容函数：将扁平的标签数据转为按分类嵌套的结构
    
    Args:
        flat: {标签键: 值} 的扁平字典
    
    Returns:
        {分类: {标签: 值}} 的嵌套字典
    """
    nested = {}
    for tag_key, value in flat.items():
        category = get_category_from_tag(tag_key)
        if category not in nested:
            nested[category] = {}
        nested[category][tag_key] = value
    return nested
