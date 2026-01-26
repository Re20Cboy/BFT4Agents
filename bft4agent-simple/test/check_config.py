"""
快速检查 config.py 配置是否正确
"""

from config import load_config
import os

def main():
    print("=" * 70)
    print("  配置检查工具")
    print("=" * 70)

    # 加载配置
    config = load_config()

    print("\n=== 基本配置 ===")
    print(f"LLM后端: {config['llm_backend']}")
    print(f"单任务模式: {config.get('single_task_mode', False)}")

    print("\n=== 千问配置 ===")
    qwen_config = config.get("llm_api_config", {}).get("qwen", {})

    api_key_from_config = qwen_config.get("api_key", "")
    app_id_from_config = qwen_config.get("app_id", "")
    api_key_from_env = os.getenv("DASHSCOPE_API_KEY", "")

    print(f"配置文件中的 api_key: '{api_key_from_config}'")
    print(f"配置文件中的 app_id: '{app_id_from_config}'")
    print(f"环境变量中的 api_key: '{api_key_from_env}'")

    # 确定最终使用的值
    final_api_key = api_key_from_config if api_key_from_config and api_key_from_config.strip() else api_key_from_env
    final_app_id = app_id_from_config

    print(f"\n最终使用的 api_key: '{final_api_key[:10]}...{final_api_key[-4:] if final_api_key and len(final_api_key) > 14 else 'None'}'")
    print(f"最终使用的 app_id: '{final_app_id}'")

    # 验证配置
    print("\n=== 配置验证 ===")

    if not final_api_key or final_api_key.strip() == "":
        print("❌ API Key 未配置！")
        print("\n解决方法（任选其一）：")
        print("1. 在 config.py 中设置：")
        print('   "qwen": {"api_key": "sk-xxx", "app_id": "your-app-id"}')
        print("\n2. 设置环境变量（PowerShell）：")
        print('   $env:DASHSCOPE_API_KEY="sk-xxx"')
        print("\n3. 设置环境变量（CMD）：")
        print('   set DASHSCOPE_API_KEY=sk-xxx')
        return False
    else:
        print("✅ API Key 已配置")

    if not final_app_id or final_app_id.strip() == "":
        print("❌ APP ID 未配置！")
        print("\n解决方法：")
        print("在 config.py 中设置：")
        print('   "qwen": {"app_id": "your-app-id"}')
        return False
    else:
        print("✅ APP ID 已配置")

    # 尝试导入千问模块
    print("\n=== 模块检查 ===")
    try:
        from llm_modules import QwenLLM
        print("✅ QwenLLM 模块导入成功")
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        print("\n解决方法：")
        print("pip install dashscope")
        return False

    # 尝试初始化
    print("\n=== 初始化测试 ===")
    try:
        llm = QwenLLM(
            api_key=final_api_key,
            app_id=final_app_id,
            enable_thinking=False
        )
        print("✅ QwenLLM 初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False

    # 健康检查
    print("\n=== API连接测试 ===")
    try:
        is_healthy = llm.health_check()
        if is_healthy:
            print("✅ API连接正常")
        else:
            print("❌ API连接失败")
            return False
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

    print("\n" + "=" * 70)
    print("✅ 所有检查通过！可以运行测试了")
    print("=" * 70)
    print("\n运行测试命令：")
    print("  python test_qwen_single_task.py --mode api")

    return True


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
