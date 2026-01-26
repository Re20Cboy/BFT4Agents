"""
LLM配置测试脚本

用于快速测试LLM API配置是否正确
"""

import sys
from config import load_config
from llm_new import LLMCaller


def test_mock_llm():
    """测试Mock LLM"""
    print("\n=== 测试 Mock LLM ===")

    llm = LLMCaller(backend="mock", accuracy=0.9)

    # 测试生成
    reasoning, answer = llm.generate("2 + 2 = ?")
    print(f"✅ 生成测试:")
    print(f"   问题: 2 + 2 = ?")
    print(f"   推理: {reasoning[:2]}...")  # 只显示前两步
    print(f"   答案: {answer}")

    # 测试验证
    proposal = {
        "task_id": "test_001",
        "reasoning": ["步骤1: 分析问题", "步骤2: 计算 2 + 2 = 4"],
        "answer": "4",
    }
    decision = llm.validate(proposal)
    print(f"✅ 验证测试:")
    print(f"   决策: {decision}")

    # 健康检查
    is_healthy = llm.health_check()
    print(f"✅ 健康检查: {'通过' if is_healthy else '失败'}")

    return True


def test_zhipu_llm(api_key: str, model: str = "glm-4"):
    """测试智谱AI LLM"""
    print(f"\n=== 测试智谱AI LLM ({model}) ===")

    try:
        # 初始化
        llm = LLMCaller(backend="zhipu", api_key=api_key, model=model)
        print("✅ 初始化成功")

        # 健康检查
        print("⏳ 执行健康检查...")
        is_healthy = llm.health_check()
        if not is_healthy:
            print("❌ 健康检查失败 - 请检查API Key和网络连接")
            return False
        print("✅ 健康检查通过")

        # 测试生成
        print("\n⏳ 测试生成功能...")
        test_question = "2 + 2 = ?"
        reasoning, answer = llm.generate(test_question)

        print(f"✅ 生成测试:")
        print(f"   问题: {test_question}")
        print(f"   推理过程（前2步）:")
        for i, step in enumerate(reasoning[:2], 1):
            print(f"      {i}. {step}")
        if len(reasoning) > 2:
            print(f"      ...（共{len(reasoning)}步）")
        print(f"   答案: {answer}")

        # 测试验证
        print("\n⏳ 测试验证功能...")
        proposal = {
            "task_id": "math_001",
            "reasoning": reasoning,
            "answer": answer,
        }
        decision = llm.validate(proposal)

        print(f"✅ 验证测试:")
        print(f"   决策: {decision}")

        print("\n✅ 所有测试通过！")
        return True

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("   请运行: pip install zhipuai")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("  BFT4Agent - LLM配置测试工具")
    print("=" * 60)

    # 加载配置
    config = load_config()
    backend = config["llm_backend"]

    print(f"\n当前配置的后端: {backend}")

    if backend == "mock":
        # 测试Mock LLM
        success = test_mock_llm()

    elif backend == "zhipu":
        # 测试智谱AI
        api_config = config.get("llm_api_config", {}).get("zhipu", {})
        api_key = api_config.get("api_key", "")

        if not api_key or api_key == "your-zhipu-api-key":
            print("\n❌ 错误: 请先在config.py中配置你的智谱API Key")
            print("   步骤:")
            print("   1. 打开 config.py")
            print("   2. 在 llm_api_config.zhipu.api_key 中填入你的API Key")
            print("   3. 重新运行此脚本")
            sys.exit(1)

        model = api_config.get("model", "glm-4")
        success = test_zhipu_llm(api_key, model)

    elif backend == "openai":
        print("\n⚠️  OpenAI后端测试暂未实现")
        print("   如需测试，请参考智谱AI的测试方式")
        success = False

    else:
        print(f"\n⚠️  未知的后端类型: {backend}")
        success = False

    # 总结
    print("\n" + "=" * 60)
    if success:
        print("  ✅ 测试完成 - 配置正常！")
        print("  现在可以运行: python main.py")
    else:
        print("  ❌ 测试失败 - 请检查配置")
        print("  查看详细错误信息 above")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[中断] 用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
