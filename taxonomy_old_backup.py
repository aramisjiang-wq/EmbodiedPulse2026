"""
论文标签体系统一配置与工具函数（三层标签）。

- 设计：一级=层（感知/决策/运动/操作），二级=方向，三级=具体标签
- 规范化输出：使用“Layer/Sub/Leaf” 作为存储键，示例：Perception/2D/2D detector
"""
from collections import OrderedDict, defaultdict
from typing import Dict, List, Set, Tuple

# 结构定义（按展示顺序）
TAXONOMY_TREE = [
    {
        "key": "Perception",
        "display": "感知层",
        "children": [
            {
                "key": "2D",
                "display": "2D",
                "leaves": [
                    ("Perception/2D/General", "2D通用"),
                    ("Perception/2D/2D detector", "2D检测"),
                    ("Perception/2D/2D mask", "2D分割"),
                    ("Perception/2D/VLM detection/caption", "VLM检测/描述"),
                ],
            },
            {
                "key": "3D",
                "display": "3D",
                "leaves": [
                    ("Perception/3D/General", "3D通用"),
                    ("Perception/3D/point cloud", "点云"),
                    ("Perception/3D/voxel", "体素"),
                    ("Perception/3D/3DGS", "3DGS"),
                    ("Perception/3D/affordance", "可操作性"),
                ],
            },
            {
                "key": "Generation",
                "display": "生成",
                "leaves": [
                    ("Perception/Generation/General", "生成通用"),
                    ("Perception/Generation/image/video generation", "图像/视频生成"),
                ],
            },
            {
                "key": "Understanding",
                "display": "理解",
                "leaves": [
                    ("Perception/Understanding/General", "理解通用"),
                    ("Perception/Understanding/scene understanding", "场景理解"),
                    ("Perception/Understanding/understanding and generation", "理解与生成"),
                ],
            },
        ],
    },
    {
        "key": "Decision",
        "display": "决策层",
        "children": [
            {
                "key": "Reasoning",
                "display": "推理",
                "leaves": [
                    ("Decision/Reasoning/General", "推理通用"),
                    ("Decision/Reasoning/CoT", "思维链推理"),
                ],
            },
            {
                "key": "GraphModeling",
                "display": "图建模",
                "leaves": [
                    ("Decision/GraphModeling/General", "图建模通用"),
                    ("Decision/GraphModeling/semantic", "语义图"),
                ],
            },
            {
                "key": "History",
                "display": "记忆",
                "leaves": [
                    ("Decision/History/General", "记忆通用"),
                    ("Decision/History/memory bank", "记忆库"),
                ],
            },
        ],
    },
    {
        "key": "Movement",
        "display": "运动层",
        "children": [
            {
                "key": "WholeBody",
                "display": "全身控制",
                "leaves": [
                    ("Movement/WholeBody/General", "全身控制通用"),
                    ("Movement/WholeBody/Humanoid", "人形机器人"),
                    ("Movement/WholeBody/Loco-Manipulation", "移动操作一体化"),
                    ("Movement/WholeBody/Retarget", "运动重定向"),
                    ("Movement/WholeBody/RL", "强化学习"),
                ],
            },
            {
                "key": "Locomotion",
                "display": "移动",
                "leaves": [
                    ("Movement/Locomotion/General", "移动通用"),
                    ("Movement/Locomotion/Bipedal", "双足/Bipedal"),
                    ("Movement/Locomotion/quadruped", "四足机器人"),
                ],
            },
        ],
    },
    {
        "key": "Operation",
        "display": "操作层",
        "children": [
            {
                "key": "Teleoperation",
                "display": "遥操作",
                "leaves": [
                    ("Operation/Teleoperation/General", "遥操作通用"),
                    ("Operation/Teleoperation/VR", "VR"),
                    ("Operation/Teleoperation/gello", "外骨骼"),
                    ("Operation/Teleoperation/UMI", "UMI"),
                ],
            },
            {
                "key": "Grasp",
                "display": "抓取",
                "leaves": [
                    ("Operation/Grasp/General", "抓取通用"),
                    ("Operation/Grasp/Dexterous hands", "灵巧手"),
                    ("Operation/Grasp/SimtoReal", "Sim-to-Real"),
                ],
            },
            {
                "key": "Bimanual",
                "display": "双手",
                "leaves": [
                    ("Operation/Bimanual/General", "双手通用"),
                    ("Operation/Bimanual/VLM planning", "VLM规划"),
                ],
            },
            {
                "key": "VLA",
                "display": "VLA",
                "leaves": [
                    ("Operation/VLA/General", "VLA通用"),
                    ("Operation/VLA/Lightweight", "轻量化"),
                ],
            },
            {
                "key": "Policy",
                "display": "策略",
                "leaves": [
                    ("Operation/Policy/General", "策略通用"),
                    ("Operation/Policy/IL", "模仿学习"),
                    ("Operation/Policy/RL", "强化学习"),
                    ("Operation/Policy/Autogressive", "自回归策略"),
                ],
            },
            {
                "key": "Benchmark",
                "display": "基准",
                "leaves": [
                    ("Operation/Benchmark/General", "基准通用"),
                    ("Operation/Benchmark/Libero", "Libero"),
                    ("Operation/Benchmark/maniskill", "ManiSkill"),
                ],
            },
        ],
    },
]


def _build_leaf_maps():
    display = OrderedDict()
    order: List[str] = []
    alias_map: Dict[str, str] = {}

    for layer in TAXONOMY_TREE:
        for sub in layer["children"]:
            for leaf_key, leaf_display in sub["leaves"]:
                display[leaf_key] = f"{layer['display']}/{sub['display']}/{leaf_display}"
                order.append(leaf_key)
                # 显式别名：叶子中文、英文、二级、一级都可映射到“General”
                alias_map[leaf_key.casefold()] = leaf_key
                alias_map[leaf_display.casefold()] = leaf_key
                alias_map[f"{sub['display']} {leaf_display}".casefold()] = leaf_key
                alias_map[f"{layer['display']} {sub['display']} {leaf_display}".casefold()] = leaf_key
                # 二级、一级通配到 General
                general_leaf = f"{layer['key']}/{sub['key']}/General"
                alias_map[sub["display"].casefold()] = general_leaf
                alias_map[sub["key"].casefold()] = general_leaf
                alias_map[layer["display"].casefold()] = general_leaf
                alias_map[layer["key"].casefold()] = general_leaf

    # 旧标签兼容映射
    old_aliases = {
        "perception": "Perception/2D/General",
        "perception-2d": "Perception/2D/General",
        "perception-3d": "Perception/3D/General",
        "vlm": "Perception/2D/VLM detection/caption",
        "planning": "Decision/Reasoning/General",
        "rl/il": "Operation/Policy/RL",
        "manipulation": "Operation/Grasp/General",
        "locomotion": "Movement/Locomotion/General",
        "dexterous": "Operation/Grasp/Dexterous hands",
        "vla": "Operation/VLA/General",
        "humanoid": "Movement/WholeBody/Humanoid",
        "tron": "Movement/Locomotion/Bipedal",
        "bipedal": "Movement/Locomotion/Bipedal",
    }
    alias_map.update(old_aliases)
    return display, order, alias_map


CATEGORY_DISPLAY, CATEGORY_ORDER, _ALIAS_LOOKUP = _build_leaf_maps()
UNCATEGORIZED_KEYS = {"", "none", "null", "uncategorized", "unknown", "其它", "其他"}


def normalize_category(category: str) -> str:
    """归一化标签到三级叶子键，未匹配返回 'Uncategorized'"""
    if category is None:
        return "Uncategorized"
    raw = str(category).strip()
    if raw.casefold() in UNCATEGORIZED_KEYS:
        return "Uncategorized"

    # 直接匹配
    if raw in CATEGORY_DISPLAY:
        return raw

    key = raw.replace(" ", "").replace("_", "/")
    if key in CATEGORY_DISPLAY:
        return key

    folded = raw.casefold()
    if folded in _ALIAS_LOOKUP:
        return _ALIAS_LOOKUP[folded]

    return "Uncategorized"


def category_match_db_filter(target_new: str) -> List[str]:
    """可用于数据库过滤的候选（旧别名+自身）"""
    candidates = {target_new}
    for alias, mapped in _ALIAS_LOOKUP.items():
        if mapped == target_new:
            candidates.add(alias)
    return sorted(candidates)


def display_category(category: str) -> str:
    """返回标签中文显示（层/方向/标签），未匹配回退原值/未分类"""
    if not category:
        return "未分类"
    return CATEGORY_DISPLAY.get(category, category)


def get_category_meta() -> Dict:
    """提供前端/接口的标签元数据（含树、顺序、显示名）"""
    return {
        "order": CATEGORY_ORDER,
        "display": CATEGORY_DISPLAY,
        "tree": TAXONOMY_TREE,
        "uncategorized": "Uncategorized",
    }


def split_leaf_key(leaf: str) -> Tuple[str, str, str]:
    """
    拆分叶子键为 (level1, level2, leaf)
    """
    if not leaf or leaf == "Uncategorized":
        return ("Uncategorized", "Uncategorized", "Uncategorized")
    parts = leaf.split("/")
    if len(parts) < 3:
        return ("Uncategorized", "Uncategorized", leaf)
    return parts[0], parts[1], leaf


def build_nested_from_flat(flat: Dict[str, any]) -> Dict[str, Dict[str, Dict[str, any]]]:
    """
    将扁平的 {leaf: value} 转为 {level1:{level2:{leaf:value}}}
    """
    nested: Dict[str, Dict[str, Dict[str, any]]] = {}
    for leaf, value in flat.items():
        l1, l2, leaf_key = split_leaf_key(leaf)
        nested.setdefault(l1, {}).setdefault(l2, {})[leaf_key] = value
    return nested


