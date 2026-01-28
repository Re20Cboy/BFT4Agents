"""
任务加载与管理模块

提供从 JSON 文件加载任务的功能
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Optional


def load_tasks_from_file(file_path: str) -> List[Dict]:
    """
    从 JSON 文件加载任务列表

    Args:
        file_path: 任务文件路径（相对于项目根目录或绝对路径）

    Returns:
        任务列表

    Raises:
        FileNotFoundError: 文件不存在
        json.JSONDecodeError: JSON 格式错误
    """
    path = Path(file_path)

    # 如果是相对路径，尝试从 data/tasks/ 目录加载
    if not path.is_absolute():
        # 先尝试直接路径
        if path.exists():
            full_path = path
        else:
            # 尝试从 data/tasks/ 目录加载
            full_path = Path("data/tasks") / path
            if not full_path.exists():
                raise FileNotFoundError(f"任务文件不存在: {file_path}")
    else:
        full_path = path

    with open(full_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 检查数据格式
    if "tasks" in data:
        # 标准格式：{"dataset_name": ..., "tasks": [...]}
        return data["tasks"]
    elif isinstance(data, list):
        # 简化格式：直接是任务列表
        return data
    else:
        raise ValueError(f"不支持的任务文件格式: {file_path}")


def select_tasks(
    tasks: List[Dict],
    num_tasks: Optional[int] = None,
    shuffle: bool = False,
    task_ids: Optional[List[str]] = None
) -> List[Dict]:
    """
    从任务列表中选择任务

    Args:
        tasks: 完整任务列表
        num_tasks: 选择任务数量（None 表示全部）
        shuffle: 是否打乱顺序
        task_ids: 指定要选择的任务 ID 列表（优先级高于 num_tasks）

    Returns:
        选中的任务列表
    """
    if task_ids:
        # 按 task_id 筛选
        task_id_set = set(task_ids)
        selected = [t for t in tasks if t.get("task_id") in task_id_set]
        if not selected:
            raise ValueError(f"未找到指定的任务 ID: {task_ids}")
        return selected

    if num_tasks is None:
        # 返回全部任务
        selected = tasks
    else:
        # 随机选择指定数量
        if num_tasks > len(tasks):
            raise ValueError(f"请求数量 {num_tasks} 超过任务总数 {len(tasks)}")
        selected = random.sample(tasks, num_tasks)

    if shuffle:
        random.shuffle(selected)

    return selected


def print_task_info(tasks: List[Dict], dataset_name: str = "unknown"):
    """打印任务信息"""
    print(f"\n=== 任务集信息 ===")
    print(f"数据集: {dataset_name}")
    print(f"任务总数: {len(tasks)}")
    print(f"任务类型分布:")

    # 统计任务类型
    type_count = {}
    for task in tasks:
        task_type = task.get("type", "unknown")
        type_count[task_type] = type_count.get(task_type, 0) + 1

    for task_type, count in sorted(type_count.items()):
        print(f"  - {task_type}: {count} 个")


class TaskLoader:
    """任务加载器类（更高级的接口）"""

    def __init__(self, config: Dict):
        """
        初始化任务加载器

        Args:
            config: 配置字典（从 config.yaml 加载）
        """
        self.config = config
        self.task_config = config.get("tasks", {})

    def load(self) -> List[Dict]:
        """
        根据配置加载任务

        Returns:
            任务列表
        """
        # 获取任务文件路径
        file_path = self.task_config.get("file", "data/tasks/math_tasks.json")

        # 加载任务
        all_tasks = load_tasks_from_file(file_path)

        # 打印任务信息
        dataset_name = self.task_config.get("dataset_name", "unknown")
        print_task_info(all_tasks, dataset_name)

        # 选择任务
        num_tasks = self.task_config.get("num_tasks")
        shuffle = self.task_config.get("shuffle", False)
        task_ids = self.task_config.get("task_ids")

        selected_tasks = select_tasks(
            all_tasks,
            num_tasks=num_tasks,
            shuffle=shuffle,
            task_ids=task_ids
        )

        print(f"\n[INFO] 已选择 {len(selected_tasks)} 个任务用于本次实验")

        # 打印任务列表（前5个）
        for i, task in enumerate(selected_tasks[:5], 1):
            task_id = task.get("task_id", f"task_{i}")
            content = task.get("content", "")[:50]  # 只显示前50字符
            print(f"  {i}. [{task_id}] {content}...")

        if len(selected_tasks) > 5:
            print(f"  ... 还有 {len(selected_tasks) - 5} 个任务")

        return selected_tasks
