"""
千问模型单任务测试脚本

快速测试千问模型在BFT4Agent系统中的集成效果
"""

import os
import sys
from config import load_config
from agents import create_agents
from network import Network
from consensus import BFT4Agent
from llm_new import LLMCaller


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_qwen_single_task():
    """测试千问模型的单任务BFT共识"""

    print_header("千问模型单任务BFT测试")

    # 加载配置
    config = load_config()

    # 强制使用千问模型
    config["llm_backend"] = "qwen"
    config["single_task_mode"] = True  # 单任务模式

    # 减少agent数量以加快测试
    config["num_agents"] = 5
    config["malicious_ratio"] = 0.2  # 1/5 = 20%

    print("\n=== 测试配置 ===")
    print(f"LLM后端: {config['llm_backend']}")
    print(f"Agent数量: {config['num_agents']}")
    print(f"恶意节点比例: {config['malicious_ratio']:.1%}")
    print(f"任务模式: 单任务")

    # 获取千问配置
    qwen_config = config["llm_api_config"].get("qwen", {})

    # 优先使用配置文件中的API Key，其次使用环境变量
    api_key = qwen_config.get("api_key", "")
    if not api_key or api_key.strip() == "":
        api_key = os.getenv("DASHSCOPE_API_KEY", "")

    app_id = qwen_config.get("app_id", "")

    # 调试信息：显示配置来源
    print(f"\n=== 配置读取调试信息 ===")
    print(f"从配置文件读取的 api_key: {qwen_config.get('api_key', 'None')}")
    print(f"从环境变量读取的 api_key: {os.getenv('DASHSCOPE_API_KEY', 'None')}")
    print(f"最终使用的 api_key: {api_key[:10]}...{api_key[-4:] if api_key and len(api_key) > 14 else 'None'}")
    print(f"从配置文件读取的 app_id: {app_id}")

    # 检查配置
    if not api_key or api_key.strip() == "":
        print("\n[ERROR] 未找到API Key！")
        print("请设置环境变量 DASHSCOPE_API_KEY")
        print("或在 config.py 中配置 qwen.api_key")
        return False

    if not app_id or app_id.strip() == "":
        print("\n[ERROR] 未找到APP ID！")
        print("请在 config.py 中配置 qwen.app_id")
        return False

    print(f"\n=== 千问配置 ===")
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    print(f"APP ID: {app_id}")
    print(f"思考模式: {qwen_config.get('enable_thinking', False)}")

    try:
        # 创建LLM
        print("\n[1/5] 初始化千问模型...")
        llm = LLMCaller(
            backend="qwen",
            api_key=api_key,
            app_id=app_id,
            enable_thinking=qwen_config.get("enable_thinking", False)
        )
        print("✓ 千问模型初始化成功")

        # 健康检查
        print("\n[2/5] API健康检查...")
        if llm.health_check():
            print("✓ API连接正常")
        else:
            print("✗ API连接失败")
            return False

        # 创建Agents
        print("\n[3/5] 创建Agents...")
        role_configs = config.get("agent_roles", [])
        random_assignment = config.get("assign_roles_randomly", True)

        agents = create_agents(
            num_agents=config["num_agents"],
            malicious_ratio=config["malicious_ratio"],
            llm_caller=llm,
            role_configs=role_configs,
            random_assignment=random_assignment,
        )

        num_malicious = sum(1 for a in agents if a.is_malicious)
        print(f"✓ 创建了 {len(agents)} 个Agent（{num_malicious} 个恶意）")

        # 显示Agent的专业领域分配
        print("\n=== Agent专业领域 ===")
        for agent in agents:
            malicious_flag = " [恶意]" if agent.is_malicious else ""
            specialty_name = agent.role_config.get("name", "通用")
            print(f"  {agent.id}: {specialty_name}{malicious_flag}")

        # 创建网络
        print("\n[4/5] 创建P2P网络...")
        network = Network(
            delay_range=config["network_delay"],
            packet_loss=config.get("packet_loss", 0.01)
        )

        for agent in agents:
            network.register(agent)

        print("✓ P2P网络创建成功")

        # 创建BFT实例
        print("\n[5/5] 初始化BFT4Agent协议...")
        bft = BFT4Agent(
            agents=agents,
            network=network,
            timeout=config["timeout"],
            max_retries=config["max_retries"],
        )
        print("✓ BFT协议初始化成功")

        # 运行单任务测试
        print_header("开始BFT共识测试")

        task = {"content": "2 + 2 = ?", "type": "math"}

        print(f"\n任务: {task['content']}")
        print("开始共识...\n")

        result = bft.run(task)

        # 显示结果
        print_header("测试结果")

        if result["success"]:
            print(f"✓ 共识成功！")
            print(f"\n最终答案: {result.get('answer', 'N/A')}")
            print(f"总耗时: {result['total_time']:.2f} 秒")
            print(f"视图切换次数: {result['view_changes']}")
            print(f"投票统计: {result.get('votes', 'N/A')}")

            # 显示提案详情
            if "proposal" in result:
                proposal = result["proposal"]
                print(f"\n=== 提案详情 ===")
                print(f"提案者: {proposal.get('leader', 'N/A')}")
                print(f"推理过程:")
                for i, step in enumerate(proposal.get('reasoning', []), 1):
                    print(f"  {i}. {step}")
        else:
            print(f"✗ 共识失败")
            print(f"失败原因: {result.get('error', 'Unknown')}")

        # 显示统计信息
        print("\n=== BFT统计 ===")
        stats = bft.get_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

        print("\n=== 网络统计 ===")
        net_stats = network.get_stats()
        for key, value in net_stats.items():
            print(f"{key}: {value}")

        print("\n" + "=" * 70)
        print("✓ 测试完成！")
        print("=" * 70)

        return result["success"]

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_qwen_api_only():
    """仅测试千问API（不涉及BFT）- 参考官方示例"""

    print_header("千问API快速测试")

    # 获取配置
    from config import load_config
    config = load_config()
    qwen_config = config["llm_api_config"].get("qwen", {})

    # 优先从配置文件读取，其次从环境变量读取
    api_key = qwen_config.get("api_key", "")
    if not api_key or api_key.strip() == "":
        api_key = os.getenv("DASHSCOPE_API_KEY", "")

    app_id = qwen_config.get("app_id", "")

    # 显示配置信息
    print("\n=== 配置信息 ===")
    print(f"API Key: {api_key[:10]}...{api_key[-4:] if api_key and len(api_key) > 14 else 'None'}")
    print(f"APP ID: {app_id}")

    if not api_key or api_key.strip() == "":
        print("\n[ERROR] 未找到API Key！")
        print("请设置环境变量 DASHSCOPE_API_KEY")
        print("或在 config.py 中配置 qwen.api_key")
        return False

    if not app_id or app_id.strip() == "":
        print("\n[ERROR] 未找到APP ID！")
        print("请在 config.py 中配置 qwen.app_id")
        return False

    try:
        from http import HTTPStatus
        from dashscope import Application

        print("\n=== 测试1: 基础问答 ===")
        print("问题: 你是谁？")

        response = Application.call(
            api_key=api_key,
            app_id=app_id,
            prompt='你是谁？'
        )

        if response.status_code != HTTPStatus.OK:
            print(f"\n✗ API调用失败")
            print(f"request_id={response.request_id}")
            print(f"code={response.status_code}")
            print(f"message={response.message}")
            print(f"请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code")
            return False

        print(f"\n✓ 回答: {response.output.text}")

        print("\n=== 测试2: 数学计算 ===")
        question = "2 + 2 = ？请直接给出答案。"
        print(f"问题: {question}")

        response = Application.call(
            api_key=api_key,
            app_id=app_id,
            prompt=question
        )

        if response.status_code != HTTPStatus.OK:
            print(f"\n✗ API调用失败")
            print(f"code={response.status_code}")
            print(f"message={response.message}")
            return False

        print(f"\n✓ 回答: {response.output.text}")

        print("\n=== 测试3: 推理问题 ===")
        question = "请说明：为什么1+1=2？"
        print(f"问题: {question}")

        response = Application.call(
            api_key=api_key,
            app_id=app_id,
            prompt=question
        )

        if response.status_code != HTTPStatus.OK:
            print(f"\n✗ API调用失败")
            print(f"code={response.status_code}")
            print(f"message={response.message}")
            return False

        print(f"\n✓ 回答: {response.output.text[:200]}...")  # 只显示前200字符

        print("\n" + "=" * 70)
        print("✓ 所有API测试通过！")
        print("=" * 70)
        return True

    except ImportError:
        print("\n[ERROR] 未安装 dashscope 库")
        print("请运行: pip install dashscope")
        return False
    except Exception as e:
        print(f"\n[ERROR] API测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("""
    千问模型单任务测试

    测试模式：
    1. 仅API测试（快速验证千问API是否可用）
    2. 完整BFT测试（测试千问在BFT系统中的完整流程）
    """)

    import argparse

    parser = argparse.ArgumentParser(description="千问模型测试")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["api", "bft"],
        default="api",
        help="测试模式：api=仅测试API，bft=完整BFT测试"
    )

    args = parser.parse_args()

    if args.mode == "api":
        success = test_qwen_api_only()
    else:
        success = test_qwen_single_task()

    sys.exit(0 if success else 1)
