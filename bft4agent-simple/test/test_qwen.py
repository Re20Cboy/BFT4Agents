"""
千问模型接口测试脚本

使用方法：
1. 设置环境变量（推荐）：
   export DASHSCOPE_API_KEY="your-api-key"

2. 或直接在代码中设置API Key和APP_ID

3. 运行测试：
   python test_qwen.py
"""

import os
from llm_modules import QwenLLM


def test_qwen_basic():
    """测试千问模型基本功能"""
    print("=" * 60)
    print("千问模型接口测试")
    print("=" * 60)

    # 方式1：从环境变量读取API Key（推荐）
    api_key = os.getenv("DASHSCOPE_API_KEY")

    # 方式2：直接设置（不推荐，仅用于测试）
    # api_key = "your-api-key-here"

    # 设置APP ID（请替换为你的实际APP ID）
    app_id = "your-app-id-here"

    # 检查配置
    if not api_key:
        print("\n[ERROR] 未找到API Key！")
        print("请设置环境变量 DASHSCOPE_API_KEY 或在代码中设置api_key")
        return False

    if app_id == "your-app-id-here":
        print("\n[ERROR] 请设置正确的APP ID！")
        print("在代码中修改 app_id 变量为你的实际应用ID")
        return False

    print(f"\n=== 配置信息 ===")
    print(f"API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else api_key}")
    print(f"APP ID: {app_id}")

    try:
        # 初始化千问模型（不启用思考模式）
        print("\n=== 初始化模型 ===")
        llm = QwenLLM(api_key=api_key, app_id=app_id, enable_thinking=False)
        print("✓ 模型初始化成功")

        # 健康检查
        print("\n=== 健康检查 ===")
        is_healthy = llm.health_check()
        if is_healthy:
            print("✓ API连接正常")
        else:
            print("✗ API连接失败")
            return False

        # 测试生成功能
        print("\n=== 测试生成功能 ===")
        test_question = "2 + 2 = ?"
        print(f"问题: {test_question}")

        reasoning, answer = llm.generate(test_question)

        print(f"\n推理过程:")
        for i, step in enumerate(reasoning, 1):
            print(f"  {i}. {step}")

        print(f"\n最终答案: {answer}")

        # 测试验证功能
        print("\n=== 测试验证功能 ===")
        test_proposal = {
            "task_id": test_question,
            "reasoning": reasoning,
            "answer": answer
        }

        validation = llm.validate(test_proposal)
        print(f"验证结果: {validation} ({'通过' if validation == 'Y' else '不通过'})")

        # 测试思考模式（可选）
        print("\n=== 测试思考模式 ===")
        try:
            llm_thinking = QwenLLM(
                api_key=api_key,
                app_id=app_id,
                enable_thinking=True
            )
            print("✓ 思考模式初始化成功")

            reasoning_t, answer_t = llm_thinking.generate(test_question)
            print(f"思考模式推理过程: {len(reasoning_t)}步")
            print(f"思考模式答案: {answer_t}")

        except Exception as e:
            print(f"⚠ 思考模式测试失败（可能模型不支持）: {e}")

        print("\n" + "=" * 60)
        print("✓ 所有测试完成")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_config():
    """使用配置文件测试"""
    print("\n\n" + "=" * 60)
    print("使用配置文件测试")
    print("=" * 60)

    from config import load_config
    from llm_new import LLMCaller

    try:
        # 加载配置
        config = load_config()

        # 检查千问配置
        qwen_config = config["llm_api_config"].get("qwen", {})
        api_key = qwen_config.get("api_key") or os.getenv("DASHSCOPE_API_KEY")
        app_id = qwen_config.get("app_id")

        if not api_key or not app_id:
            print("\n[ERROR] 配置文件中缺少千问配置！")
            print("请在config.py中配置qwen的api_key和app_id")
            return False

        print(f"\n配置: {config['llm_backend']}")
        print(f"APP ID: {app_id}")

        # 创建LLM调用器
        if config["llm_backend"] != "qwen":
            print("\n[INFO] 当前配置使用的不是qwen后端")
            print("将强制使用qwen进行测试...")

        llm_caller = LLMCaller(
            backend="qwen",
            api_key=api_key,
            app_id=app_id,
            enable_thinking=qwen_config.get("enable_thinking", False)
        )

        print("✓ LLM调用器创建成功")

        # 测试
        test_question = "3 + 5 = ?"
        print(f"\n问题: {test_question}")

        reasoning, answer = llm_caller.generate(test_question)
        print(f"推理过程: {reasoning}")
        print(f"答案: {answer}")

        print("\n✓ 配置文件测试完成")
        return True

    except Exception as e:
        print(f"\n[ERROR] 配置文件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("""
    千问模型接口测试

    测试前准备：
    1. 获取DashScope API Key：https://bailian.console.aliyun.com/
    2. 创建应用并获取APP ID
    3. 设置环境变量或修改代码中的配置
    """)

    # 运行基本测试
    success1 = test_qwen_basic()

    # 运行配置文件测试
    success2 = test_with_config()

    # 总结
    print("\n\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"基本测试: {'✓ 通过' if success1 else '✗ 失败'}")
    print(f"配置测试: {'✓ 通过' if success2 else '✗ 失败'}")
    print("=" * 60)

    if success1 or success2:
        print("\n✓ 千问模型接口集成成功！")
        print("\n使用方法：")
        print("1. 在config.py中设置llm_backend为'qwen'")
        print("2. 在config.py的llm_api_config.qwen中配置api_key和app_id")
        print("3. 运行主程序: python main.py")
    else:
        print("\n✗ 测试失败，请检查配置")
