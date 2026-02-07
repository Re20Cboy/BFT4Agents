"""
容错边界测试实验模块

实验目标：
- 测试BFT4Agent协议在面对刁钻问题时的容错边界
- 验证诚实LLM agent出错时，系统是否能达成共识
- 分别测试Leader诚实和恶意两种场景
"""

from .experiment import FaultToleranceExperiment

__all__ = ['FaultToleranceExperiment']
