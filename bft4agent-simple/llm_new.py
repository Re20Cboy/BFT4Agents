"""LLM统一调用接口"""
from typing import Dict, Tuple
from llm_modules import MockLLM, ZhipuLLM, OpenAILLM, QwenLLM, CustomLLM


class LLMCaller:
    def __init__(self, backend: str = "mock", **kwargs):
        self.backend = backend.lower()
        self.llm = self._create_llm(backend, **kwargs)

    def _create_llm(self, backend: str, **kwargs):
        backend = backend.lower()

        if backend == "mock":
            return MockLLM(accuracy=kwargs.get("accuracy", 0.85))

        elif backend == "zhipu":
            api_key = kwargs.get("api_key")
            if not api_key:
                raise ValueError("Zhipu requires api_key")
            return ZhipuLLM(api_key=api_key, model=kwargs.get("model", "glm-4.7"))

        elif backend == "openai":
            api_key = kwargs.get("api_key")
            if not api_key:
                raise ValueError("OpenAI requires api_key")
            return OpenAILLM(
                api_key=api_key,
                base_url=kwargs.get("base_url"),
                model=kwargs.get("model", "gpt-3.5-turbo")
            )

        elif backend == "qwen":
            api_key = kwargs.get("api_key")
            app_id = kwargs.get("app_id")
            if not app_id:
                raise ValueError("Qwen requires app_id")
            return QwenLLM(
                api_key=api_key,
                app_id=app_id,
                enable_thinking=kwargs.get("enable_thinking", False)
            )

        elif backend == "custom":
            api_key = kwargs.get("api_key")
            base_url = kwargs.get("base_url")
            if not api_key or not base_url:
                raise ValueError("Custom requires api_key and base_url")
            return CustomLLM(
                api_key=api_key,
                base_url=base_url,
                model=kwargs.get("model", "custom-model")
            )

        else:
            raise ValueError(f"Unknown backend: {backend}")

    def generate(self, question: str) -> Tuple[list, str]:
        return self.llm.generate(question)

    def validate(self, proposal: Dict) -> str:
        return self.llm.validate(proposal)

    def health_check(self) -> bool:
        return self.llm.health_check()