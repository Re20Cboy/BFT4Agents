"""
BFT4Agent Demo - 主入口

快速演示BFT4Agentconsensus流程
"""

import sys
import time
from config import load_config
from agents import create_agents
from network import Network
from consensus import BFT4Agent
from llm_new import LLMCaller


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_config(config):
    """打印config"""
    print("\n=== config ===")
    print(f"Agent数量: {config['num_agents']}")
    print(f"maliciousnode比例: {config['malicious_ratio']:.1%}")
    print(f"LLM后端: {config['llm_backend']}")
    print(f"networkdelay: {config['network_delay']} ms")
    print(f"法定人数比例: {config['quorum_ratio']:.1%}")


def main():
    """主函数"""
    print_header("BFT4Agent Demo - 简化原型")

    # 加载config
    config = load_config()
    print_config(config)

    # 创建LLM
    print(f"\n[init] 创建LLM ({config['llm_backend']})...")

    # 准备LLM配置参数
    backend = config["llm_backend"]
    llm_kwargs = {}

    if backend == "mock":
        llm_kwargs["accuracy"] = config.get("mock_accuracy", 0.85)
    else:
        # 从配置中获取对应后端的API配置
        api_config = config.get("llm_api_config", {}).get(backend, {})
        if api_config:
            # 根据不同后端添加不同的配置参数
            if backend == "openai":
                llm_kwargs["api_key"] = api_config.get("api_key", "")
                if api_config.get("base_url"):
                    llm_kwargs["base_url"] = api_config["base_url"]
                llm_kwargs["model"] = api_config.get("model", "gpt-3.5-turbo")

            elif backend == "zhipu":
                llm_kwargs["api_key"] = api_config.get("api_key", "")
                llm_kwargs["model"] = api_config.get("model", "glm-4")

            elif backend == "qwen":
                import os
                llm_kwargs["api_key"] = api_config.get("api_key") or os.getenv("DASHSCOPE_API_KEY")
                llm_kwargs["app_id"] = api_config.get("app_id", "")
                llm_kwargs["enable_thinking"] = api_config.get("enable_thinking", False)

            elif backend == "custom":
                llm_kwargs["api_key"] = api_config.get("api_key", "")
                llm_kwargs["base_url"] = api_config.get("base_url", "")
                llm_kwargs["model"] = api_config.get("model", "custom-model")

            elif backend in ["tongyi", "wenxin", "xunfei", "claude"]:
                # 其他后端的配置参数
                for key, value in api_config.items():
                    llm_kwargs[key] = value

    llm = LLMCaller(backend=backend, **llm_kwargs)

    # 创建Agent
    num_malicious = int(config["num_agents"] * config["malicious_ratio"])
    print(f"[init] 创建 {config['num_agents']} 个Agent ({num_malicious} 个malicious)...")

    # 获取角色配置
    role_configs = config.get("agent_roles", [])
    random_assignment = config.get("assign_roles_randomly", True)

    agents = create_agents(
        num_agents=config["num_agents"],
        malicious_ratio=config["malicious_ratio"],
        llm_caller=llm,
        role_configs=role_configs,
        random_assignment=random_assignment,
    )

    # 打印Agent信息
    print("\n=== Agent列表 ===")
    for agent in agents:
        malicious_flag = " [malicious]" if agent.is_malicious else ""
        specialty_name = agent.role_config.get("name", "通用")
        specialty = f"- {specialty_name}" if agent.role_config else ""
        print(f"  {agent.id}: {specialty}, rep={agent.reputation:.2f}{malicious_flag}")

    # 创建network
    print(f"\n[init] 创建P2Pnetwork...")
    network = Network(
        delay_range=config["network_delay"], packet_loss=config.get("packet_loss", 0.01)
    )

    # registernode
    for agent in agents:
        network.register(agent)

    # 创建BFT实例
    print(f"[init] initBFT4Agent协议...")
    bft = BFT4Agent(
        agents=agents,
        network=network,
        timeout=config["timeout"],
        max_retries=config["max_retries"],
    )

    # 运行示例task
    print_header("开始consensus流程")

    # 检查是否使用单任务模式
    single_task_mode = config.get("single_task_mode", False)

    if single_task_mode:
        # 单任务模式（用于测试）
        print("\n[INFO] 使用单任务模式进行测试")
        tasks = [
            {"content": "2 + 2 = ?", "type": "math"},
        ]
    else:
        # 多任务模式（默认）
        tasks = [
            {"content": "2 + 2 = ?", "type": "math"},
            {"content": "23 * 47 = ?", "type": "math"},
            {"content": "144 / 12 = ?", "type": "math"},
        ]

    results = []

    for i, task in enumerate(tasks, 1):
        print(f"\n{'=' * 60}")
        print(f"  Task {i}/{len(tasks)}: {task['content']}")
        print(f"{'=' * 60}")

        result = bft.run(task)
        results.append(result)

        time.sleep(0.2)  # task间暂停

    # statsresult
    print_header("experimentresultstats")

    success_count = sum(1 for r in results if r["success"])
    total_time = sum(r["total_time"] for r in results)
    total_view_changes = sum(r["view_changes"] for r in results)

    print(f"总task数: {len(results)}")
    print(f"success: {success_count} ({success_count/len(results):.1%})")
    print(f"failed: {len(results) - success_count}")
    print(f"总time: {total_time:.2f}秒")
    print(f"平均time: {total_time/len(results):.2f}秒")
    print(f"总viewchange: {total_view_changes}次")

    # BFTstats
    stats = bft.get_stats()
    print(f"\n=== BFT协议stats ===")
    for key, value in stats.items():
        print(f"{key}: {value}")

    # networkstats
    net_stats = network.get_stats()
    print(f"\n=== networkstats ===")
    for key, value in net_stats.items():
        print(f"{key}: {value}")

    print("\n" + "=" * 60)
    print("  Democomplete!")
    print("=" * 60)

    return results


if __name__ == "__main__":
    try:
        results = main()
    except KeyboardInterrupt:
        print("\n\n[中断] 用户取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
