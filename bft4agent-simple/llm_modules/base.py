"""LLM基类"""
from abc import ABC, abstractmethod
from typing import Dict, Tuple


class BaseLLM(ABC):
    @abstractmethod
    def generate(self, question: str) -> Tuple[list, str]:
        """生成推理过程和答案"""
        pass

    @abstractmethod
    def validate(self, proposal: Dict) -> str:
        """验证提案，返回Y/N"""
        pass

    def health_check(self) -> bool:
        """健康检查"""
        return True