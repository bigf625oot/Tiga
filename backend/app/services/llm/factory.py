from agno.models.openai import OpenAIChat

from app.models.llm_model import LLMModel


class ModelFactory:
    """
    Factory to create Agno OpenAIChat instances from LLMModel configuration.
    Centralizes logic for role mapping, provider-specific adjustments, and fallback URLs.
    """

    @staticmethod
    def create_model(llm_model: LLMModel) -> OpenAIChat:
        api_key = llm_model.api_key or "dummy"
        base_url = llm_model.base_url

        # Standardize Base URLs for common providers if not explicitly set
        if not base_url:
            provider = (llm_model.provider or "").lower()
            if provider == "aliyun":
                base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            elif provider == "deepseek":
                base_url = "https://api.deepseek.com"
            elif provider == "openai":
                base_url = None  # Default OpenAI URL
            # Add more providers here as needed

        # Common Role Map (fixes compatibility for Aliyun/DeepSeek which dislike 'developer' role)
        role_map = {
            "system": "system",
            "developer": "system",
            "user": "user",
            "assistant": "assistant",
            "tool": "tool",
            "function": "function",
        }

        return OpenAIChat(id=llm_model.model_id, api_key=api_key, base_url=base_url, role_map=role_map)

    @staticmethod
    def is_reasoning_model(llm_model: LLMModel) -> bool:
        """
        Heuristic to check if a model supports native reasoning (e.g. R1).
        """
        mid = (llm_model.model_id or "").lower()
        return "reasoner" in mid or "r1" in mid

    @staticmethod
    def should_use_agno_reasoning(llm_model: LLMModel) -> bool:
        """
        Determine if we should enable Agno's manual reasoning (CoT).
        If the model does it natively (like DeepSeek R1), we usually disable Agno's reasoning
        to avoid double-reasoning or interference.
        """
        provider = (llm_model.provider or "").lower()
        base_url = (llm_model.base_url or "").lower()

        # DeepSeek models often handle reasoning natively or are fast enough
        if "deepseek" in provider or "deepseek" in base_url:
            return False

        return True
