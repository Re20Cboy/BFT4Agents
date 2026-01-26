"""阿里云千问模型"""
import os
from typing import Dict, Tuple
from .base import BaseLLM


class QwenLLM(BaseLLM):
    def __init__(self, api_key: str = None, app_id: str = None, enable_thinking: bool = False):
        """
        初始化千问模型

        Args:
            api_key: DashScope API Key，如不提供则从环境变量DASHSCOPE_API_KEY读取
            app_id: 百炼应用ID
            enable_thinking: 是否启用思考模式（用于深度思考模型）
        """
        try:
            import dashscope
            self.dashscope = dashscope
        except ImportError:
            raise ImportError("请先安装dashscope SDK: pip install dashscope")

        # API Key优先使用传入参数，否则从环境变量读取
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("请提供api_key或设置环境变量DASHSCOPE_API_KEY")

        self.app_id = app_id
        if not self.app_id:
            raise ValueError("请提供app_id（百炼应用ID）")

        self.enable_thinking = enable_thinking

    def generate(self, question: str) -> Tuple[list, str]:
        """
        生成推理过程和答案

        Args:
            question: 用户问题

        Returns:
            (推理过程列表, 最终答案)
        """
        prompt = f"""请解决以下问题，并展示简明的推理过程:
问题: {question}

请按格式回答:
推理步骤1: ...
推理步骤2: ...
...
最终答案: ...
"""

        try:
            from http import HTTPStatus

            # 构建请求参数
            kwargs = {
                "api_key": self.api_key,
                "app_id": self.app_id,
                "prompt": prompt,
            }

            # 如果启用思考模式，添加相关参数
            if self.enable_thinking:
                kwargs["parameters"] = {
                    "enable_thinking": True,
                    "has_thoughts": True
                }

            # 调用千问API
            response = self.dashscope.Application.call(**kwargs)

            # 检查响应状态
            if response.status_code != HTTPStatus.OK:
                print(f"[ERROR] Qwen API: {response.message}")
                print(f"请求ID: {response.request_id}")
                print(f"错误码: {response.code}")
                return ["API调用失败"], "Error"

            # 获取回复内容
            content = response.output.text

            # 如果启用思考模式且有思考过程，优先使用思考过程
            if self.enable_thinking and response.output.thoughts:
                reasoning = [thought.get("content", "") for thought in response.output.thoughts]
            else:
                # 解析推理过程和答案
                reasoning = []
                for line in content.split("\n"):
                    line = line.strip()
                    if "推理步骤" in line or "步骤" in line or "Reasoning" in line.lower():
                        reasoning.append(line)

            # 提取最终答案
            answer = ""
            for line in content.split("\n"):
                line = line.strip()
                if "最终答案" in line or "答案" in line or "Answer" in line.lower():
                    answer = line.split(":")[-1].strip() if ":" in line else line
                    break

            # 如果没有找到答案，使用整个内容作为答案
            if not answer:
                answer = content

            # 如果没有推理过程，使用整个内容作为推理
            if not reasoning:
                reasoning = [content]

            return reasoning, answer

        except Exception as e:
            print(f"[ERROR] Qwen API: {e}")
            return ["API调用失败"], "Error"

    def validate(self, proposal: Dict) -> str:
        """
        验证提案，返回Y或N

        Args:
            proposal: 提案内容，包含task_id, reasoning, answer等字段

        Returns:
            "Y" 表示通过，"N" 表示不通过
        """
        prompt = f"""从是否存在幻觉、是否符合逻辑、是否有意识形态错误角度来简洁快速验证提案:

问题: {proposal.get('task_id', '未知')}
推理: {proposal.get('reasoning', [])}
答案: {proposal.get('answer', '无')}

请只回答: Y 或 N
"""

        try:
            from http import HTTPStatus

            response = self.dashscope.Application.call(
                api_key=self.api_key,
                app_id=self.app_id,
                prompt=prompt
            )

            if response.status_code != HTTPStatus.OK:
                return "N"

            content = response.output.text.strip().upper()

            # 只返回Y或N，如果格式错误则默认N
            if "Y" in content:
                return "Y"
            elif "N" in content:
                return "N"
            else:
                return "N"

        except Exception as e:
            print(f"[ERROR] Qwen API validation: {e}")
            return "N"

    def health_check(self) -> bool:
        """
        健康检查，测试API是否可用

        Returns:
            True表示API可用，False表示不可用
        """
        try:
            from http import HTTPStatus

            response = self.dashscope.Application.call(
                api_key=self.api_key,
                app_id=self.app_id,
                prompt="健康检查"
            )

            return response.status_code == HTTPStatus.OK

        except Exception as e:
            print(f"[ERROR] Qwen health check: {e}")
            return False
