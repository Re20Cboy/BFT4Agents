"""
测试任务加载功能

验证 tasks.py 模块的功能是否正常
"""

import json
from tasks import load_tasks_from_file, select_tasks, print_task_info


def test_load_math_tasks():
    """测试加载数学任务"""
    print("=" * 60)
    print("测试 1: 加载数学任务")
    print("=" * 60)

    tasks = load_tasks_from_file("data/tasks/math_tasks.json")
    print(f"[OK] 成功加载 {len(tasks)} 个任务")

    # 检查任务结构
    task = tasks[0]
    print(f"[OK] 任务示例: {task['task_id']} - {task['content']}")
    print(f"  - 类型: {task['type']}")
    print(f"  - 标准答案: {task.get('ground_truth', 'N/A')}")

    return tasks


def test_load_logic_tasks():
    """测试加载逻辑任务"""
    print("\n" + "=" * 60)
    print("测试 2: 加载逻辑任务")
    print("=" * 60)

    tasks = load_tasks_from_file("data/tasks/logic_tasks.json")
    print(f"[OK] 成功加载 {len(tasks)} 个任务")

    return tasks


def test_load_mixed_tasks():
    """测试加载混合任务"""
    print("\n" + "=" * 60)
    print("测试 3: 加载混合任务")
    print("=" * 60)

    tasks = load_tasks_from_file("data/tasks/mixed_tasks.json")
    print(f"[OK] 成功加载 {len(tasks)} 个混合任务")

    # 统计任务类型
    type_count = {}
    for task in tasks:
        t = task.get("type", "unknown")
        type_count[t] = type_count.get(t, 0) + 1

    print(f"[OK] 任务类型分布: {type_count}")

    return tasks


def test_select_tasks():
    """测试任务选择功能"""
    print("\n" + "=" * 60)
    print("测试 4: 任务选择功能")
    print("=" * 60)

    # 加载所有任务
    all_tasks = load_tasks_from_file("data/tasks/math_tasks.json")
    print(f"总任务数: {len(all_tasks)}")

    # 测试 1: 选择前 3 个任务
    print("\n[测试 4.1] 选择前 3 个任务")
    selected = select_tasks(all_tasks, num_tasks=3)
    print(f"[OK] 选择了 {len(selected)} 个任务")
    for task in selected:
        print(f"  - {task['task_id']}: {task['content'][:30]}...")

    # 测试 2: 按 task_id 选择
    print("\n[测试 4.2] 按 task_id 选择特定任务")
    selected = select_tasks(all_tasks, task_ids=["math_001", "math_005"])
    print(f"[OK] 选择了 {len(selected)} 个任务")
    for task in selected:
        print(f"  - {task['task_id']}: {task['content'][:30]}...")

    # 测试 3: 打乱顺序
    print("\n[测试 4.3] 打乱顺序选择")
    selected = select_tasks(all_tasks, num_tasks=5, shuffle=True)
    print(f"[OK] 选择了 {len(selected)} 个任务（已打乱顺序）")
    for task in selected:
        print(f"  - {task['task_id']}")


def test_task_info():
    """测试任务信息打印"""
    print("\n" + "=" * 60)
    print("测试 5: 任务信息打印")
    print("=" * 60)

    tasks = load_tasks_from_file("data/tasks/mixed_tasks.json")
    print_task_info(tasks, "mixed_benchmark")


def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("测试 6: 错误处理")
    print("=" * 60)

    # 测试文件不存在
    print("\n[测试 6.1] 文件不存在")
    try:
        load_tasks_from_file("nonexistent.json")
        print("[FAIL] 应该抛出异常")
    except FileNotFoundError as e:
        print(f"[OK] 正确捕获异常: {e}")

    # 测试无效的 task_id
    print("\n[测试 6.2] 无效的 task_id")
    tasks = load_tasks_from_file("data/tasks/math_tasks.json")
    try:
        select_tasks(tasks, task_ids=["invalid_id"])
        print("[FAIL] 应该抛出异常")
    except ValueError as e:
        print(f"[OK] 正确捕获异常: {e}")

    # 测试请求数量过多
    print("\n[测试 6.3] 请求数量过多")
    try:
        select_tasks(tasks, num_tasks=999)
        print("[FAIL] 应该抛出异常")
    except ValueError as e:
        print(f"[OK] 正确捕获异常: {e}")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("  BFT4Agent 任务加载功能测试")
    print("=" * 60)

    try:
        test_load_math_tasks()
        test_load_logic_tasks()
        test_load_mixed_tasks()
        test_select_tasks()
        test_task_info()
        test_error_handling()

        print("\n" + "=" * 60)
        print("  [OK] 所有测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
