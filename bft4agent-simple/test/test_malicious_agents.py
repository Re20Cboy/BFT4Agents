"""
测试恶意agent的协同行为

场景设置：
- 7个agent节点
- 2个恶意节点（agent_1和agent_2）
- 测试不同情况下的恶意行为
"""

import sys
from config import load_config
from agents import create_agents
from network import Network
from consensus import BFT4Agent
from llm_new import LLMCaller


def test_malicious_leader():
    """测试场景1：恶意agent作为leader"""
    print("\n" + "=" * 80)
    print("  测试场景1: 恶意agent作为leader")
    print("=" * 80)

    # 创建7个agent，其中2个恶意
    agents = create_agents(
        num_agents=7,
        malicious_ratio=2/7,  # 约28.6%
        llm_caller=LLMCaller(backend="mock"),
        role_configs=[],
        random_assignment=False,
    )

    # 打印agent信息
    print("\n=== Agent列表 ===")
    for agent in agents:
        malicious_flag = " [MALICIOUS]" if agent.is_malicious else ""
        print(f"  {agent.id}: {agent.specialty}{malicious_flag}")
        if agent.is_malicious:
            print(f"    └─ 恶意同伙: {agent.malicious_peers}")

    # 创建网络
    network = Network(delay_range=(10, 50))
    for agent in agents:
        network.register(agent)

    # 创建BFT实例
    bft = BFT4Agent(agents=agents, network=network)

    # 运行测试任务
    task = {"content": "2 + 2 = ?", "type": "math"}
    result = bft.run(task)

    print("\n=== 测试结果 ===")
    print(f"Success: {result['success']}")
    print(f"决策: {result.get('decision', 'N/A')}")
    print(f"答案: {result.get('answer', 'N/A')}")
    print(f"视图切换: {result['view_changes']}次")

    return result


def test_honest_leader_malicious_backup():
    """测试场景2：诚实leader，恶意backup作为反对者"""
    print("\n" + "=" * 80)
    print("  测试场景2: 诚实leader + 恶意backup反对")
    print("=" * 80)

    # 创建7个agent，其中2个恶意，确保agent_3（诚实）作为leader
    agents = create_agents(
        num_agents=7,
        malicious_ratio=2/7,
        llm_caller=LLMCaller(backend="mock"),
        role_configs=[],
        random_assignment=False,
    )

    # 打印agent信息
    print("\n=== Agent列表 ===")
    for agent in agents:
        malicious_flag = " [MALICIOUS]" if agent.is_malicious else ""
        print(f"  {agent.id}: {agent.specialty}{malicious_flag}")
        if agent.is_malicious:
            print(f"    └─ 恶意同伙: {agent.malicious_peers}")

    # 创建网络
    network = Network(delay_range=(10, 50))
    for agent in agents:
        network.register(agent)

    # 创建BFT实例，强制指定agent_3为leader（视图2）
    bft = BFT4Agent(agents=agents, network=network)
    bft.current_view = 2  # agent_3作为leader

    # 运行测试任务
    task = {"content": "5 + 3 = ?", "type": "math"}
    result = bft.run(task)

    print("\n=== 测试结果 ===")
    print(f"Success: {result['success']}")
    print(f"决策: {result.get('decision', 'N/A')}")
    print(f"答案: {result.get('answer', 'N/A')}")
    print(f"视图切换: {result['view_changes']}次")

    return result


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("  恶意Agent协同行为测试")
    print("=" * 80)

    # 测试场景1
    result1 = test_malicious_leader()

    # 测试场景2
    result2 = test_honest_leader_malicious_backup()

    # 总结
    print("\n" + "=" * 80)
    print("  测试总结")
    print("=" * 80)
    print(f"\n场景1（恶意leader）:")
    print(f"  - 共识是否成功: {result1['success']}")
    print(f"  - 视图切换次数: {result1['view_changes']}")

    print(f"\n场景2（诚实leader + 恶意backup）:")
    print(f"  - 共识是否成功: {result2['success']}")
    print(f"  - 视图切换次数: {result2['view_changes']}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[中断] 用户取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
