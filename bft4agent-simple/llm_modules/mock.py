"""Mock LLM - 用于测试"""
import random
import time
from typing import Dict, Tuple
from .base import BaseLLM


class MockLLM(BaseLLM):
    def __init__(self, accuracy: float = 0.85):
        self.accuracy = accuracy

    def generate(self, question: str) -> Tuple[list, str]:
        time.sleep(random.uniform(0.1, 0.5))
        reasoning, answer = self._solve_math(question)

        # 调试输出
        print(f"[MockLLM.generate] 输入问题: {repr(question)}")
        print(f"[MockLLM.generate] 解析结果: reasoning={reasoning}, answer={answer}")

        if random.random() > self.accuracy:
            old_answer = answer
            answer = str(int(answer) + random.randint(1, 10))
            print(f"[MockLLM.generate] 模拟幻觉: {old_answer} -> {answer}")

        reasoning_steps = [
            "步骤1: 分析问题",
            f"步骤2: {reasoning}",
            f"步骤3: 得出答案 {answer}",
        ]
        return reasoning_steps, answer

    def validate(self, proposal: Dict) -> str:
        """
        Mock验证逻辑：模拟从幻觉、逻辑、意识形态角度验证

        关键修改：好节点会实际验证数学问题的答案是否正确
        """
        time.sleep(random.uniform(0.05, 0.2))

        answer = proposal.get("answer", "")
        reasoning = proposal.get("reasoning", [])
        task_content = proposal.get("task_content", "")  # 使用task_content而不是task_id

        # 基本验证规则
        if not answer or answer == "无":
            return "N"
        if not reasoning or len(reasoning) < 2:
            return "N"

        # 模拟验证：如果有明显错误则返回N
        if not answer.isdigit() and len(answer) > 20:  # 答案过长可能是幻觉
            return "N"

        # === 关键修改：好节点实际验证数学答案 ===
        # 尝试从task_content中提取数学问题并验证答案
        correct_answer = self._extract_and_validate_answer(task_content, answer)

        if not correct_answer:
            # 答案错误，返回N
            return "N"

        # 答案正确，返回Y
        return "Y"

    def _solve_math(self, question: str) -> Tuple[str, str]:
        """
        解析数学问题并计算答案

        支持两种格式：
        1. 纯数学表达式："2 + 2 = ?"
        2. 带system prompt的格式："你是一位数学专家...\n\n问题: 2 + 2 = ?"
        """
        try:
            # 提取数学表达式
            math_expr = None

            # 方法1：查找 "问题:" 或 "Question:" 后面的内容
            if "问题:" in question or "Question:" in question:
                # 分割字符串，取最后一部分（实际的问题）
                parts = question.split("问题:" if "问题:" in question else "Question:")
                if len(parts) > 1:
                    actual_question = parts[-1].strip()
                    # 提取等号前面的表达式
                    if "=" in actual_question:
                        expr = actual_question.split("=")[0].strip()
                        math_expr = expr

            # 方法2：如果没有标记，尝试直接从整个字符串中提取
            if math_expr is None and "=" in question:
                # 取最后一个等号前面的部分
                parts = question.rsplit("=", 1)
                if len(parts) > 1:
                    # 从这部分中提取数学表达式（找最后一个运算符后面的内容）
                    before_eq = parts[0].strip()
                    # 尝试从后往前找数字开始的位置
                    import re
                    # 匹配数学表达式（数字 运算符 数字）
                    match = re.search(r'(\d+(?:\.\d+)?\s*[+\-*/]\s*\d+(?:\.\d+)?)', before_eq)
                    if match:
                        math_expr = match.group(1)

            # 计算表达式
            if math_expr:
                result = eval(math_expr)
                return f"计算 {math_expr} = {result}", str(result)

        except Exception as e:
            print(f"[MockLLM._solve_math] 解析失败: {e}, question={repr(question)}")

        return "无法解析问题", "0"

    def _extract_and_validate_answer(self, task_id: str, proposed_answer: str) -> bool:
        """
        从task_id中提取数学问题并验证答案是否正确

        Args:
            task_id: 任务描述（可能包含数学问题）
            proposed_answer: leader提出的答案

        Returns:
            True if answer is correct, False otherwise
        """
        try:
            # 尝试从task_id中提取数学表达式（格式如 "2 + 2 = ?"）
            import re

            # 匹配数学表达式（支持 +, -, *, /）
            math_pattern = r'(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)'
            match = re.search(math_pattern, task_id)

            if match:
                # 提取操作数和运算符
                num1 = float(match.group(1))
                operator = match.group(2)
                num2 = float(match.group(3))

                # 计算正确答案
                if operator == '+':
                    correct_result = num1 + num2
                elif operator == '-':
                    correct_result = num1 - num2
                elif operator == '*':
                    correct_result = num1 * num2
                elif operator == '/':
                    correct_result = num1 / num2 if num2 != 0 else 0
                else:
                    return True  # 无法验证，默认通过

                # 比较答案（处理浮点数精度问题）
                try:
                    proposed_num = float(proposed_answer)
                    # 允许小的浮点数误差
                    is_correct = abs(proposed_num - correct_result) < 0.001

                    if not is_correct:
                        print(f"[验证] 答案错误: 预期 {correct_result}, 实际 {proposed_answer}")

                    return is_correct
                except ValueError:
                    # 无法转换为数字，答案格式错误
                    print(f"[验证] 答案格式错误: {proposed_answer}")
                    return False

            # 无法提取数学问题，默认通过
            return True

        except Exception as e:
            # 验证过程出错，保守策略：默认通过
            print(f"[验证] 验证过程出错: {e}")
            return True