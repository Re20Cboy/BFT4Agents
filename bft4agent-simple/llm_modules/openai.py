"""OpenAI GPT模型"""
from typing import Dict, Tuple
from .base import BaseLLM


class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str, base_url: str = None, model: str = "gpt-3.5-turbo"):
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
            self.model = model
        except ImportError:
            raise ImportError("pip install openai")

    def generate(self, question: str) -> Tuple[list, str]:
        prompt = f"""请解决以下问题，展示推理过程:
问题: {question}
请按格式回答:
推理步骤1: ...
推理步骤2: ...
最终答案: ...
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            content = response.choices[0].message.content

            reasoning, answer = [], ""
            for line in content.split("\n"):
                line = line.strip()
                if "推理步骤" in line or "步骤" in line:
                    reasoning.append(line)
                elif "最终答案" in line or "答案" in line:
                    answer = line.split(":")[-1].strip() if ":" in line else line

            if not reasoning:
                reasoning = [content]
            return reasoning, answer
        except Exception as e:
            print(f"[ERROR] OpenAI API: {e}")
            return ["API调用失败"], "Error"

    def validate(self, proposal: Dict) -> str:
        prompt = f"""从是否存在幻觉、是否符合逻辑、是否有意识形态错误角度来简洁快速验证提案:
问题: {proposal.get('task_id', '未知')}
推理: {proposal.get('reasoning', [])}
答案: {proposal.get('answer', '无')}
请只回答: Y 或 N
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=10
            )
            content = response.choices[0].message.content.strip().upper()
            # 只返回Y或N，如果格式错误则默认N
            return "Y" if "Y" in content else "N" if "N" in content else "N"
        except:
            return "N"

    def health_check(self) -> bool:
        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "健康检查"}],
                max_tokens=10
            )
            return True
        except:
            return False