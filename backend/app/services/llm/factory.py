"""
模型工厂类，用于根据提供程序名称动态加载模型类。
包含支持的模型提供程序列表。
"""
import importlib
import inspect
from typing import Optional, Type, Dict, Any
from agno.models.base import Model
from agno.models.openai import OpenAIChat
from app.models.llm_model import LLMModel


class ModelFactory:
    """
    模型工厂类，用于根据提供程序名称动态加载模型类。
    包含支持的模型提供程序列表。
    """

    # Map provider names (lowercase) to (module_name, class_name)
    PROVIDER_MAP = {
        "openai": ("agno.models.openai", "OpenAIChat"),
        "aliyun": ("agno.models.dashscope", "DashScope"),
        "dashscope": ("agno.models.dashscope", "DashScope"),
        "deepseek": ("agno.models.deepseek", "DeepSeek"),
        "anthropic": ("agno.models.anthropic", "Claude"),
        "claude": ("agno.models.anthropic", "Claude"),
        "google": ("agno.models.google", "Gemini"),
        "gemini": ("agno.models.google", "Gemini"),
        "ollama": ("agno.models.ollama", "Ollama"),
        "aws": ("agno.models.aws", "AwsBedrock"),
        "bedrock": ("agno.models.aws", "AwsBedrock"),
        "azure": ("agno.models.azure", "AzureOpenAI"),
        "mistral": ("agno.models.mistral", "Mistral"),
        "groq": ("agno.models.groq", "Groq"),
        "xai": ("agno.models.xai", "xAI"),
        "cohere": ("agno.models.cohere", "Cohere"),
        "perplexity": ("agno.models.perplexity", "Perplexity"),
        "together": ("agno.models.together", "Together"),
        "openrouter": ("agno.models.openrouter", "OpenRouter"),
        "nvidia": ("agno.models.nvidia", "Nvidia"),
        "fireworks": ("agno.models.fireworks", "Fireworks"),
        "vertexai": ("agno.models.vertexai", "VertexAI"),
        "siliconflow": ("agno.models.siliconflow", "Siliconflow"),
        "nebius": ("agno.models.nebius", "Nebius"),
    }

    @staticmethod
    def get_provider_configs() -> Dict[str, Any]:
        """
        Return the supported providers and their default configurations.
        Used by the frontend to populate dropdowns.
        """
        configs = {}
        
        # Deduplicate keys that map to the same provider (e.g. "aliyun" and "dashscope")
        # We prefer the more common name
        
        # Default known models for some providers (optional helper)
        default_models = {
            "openai": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            "aliyun": ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-vl-max"],
            "deepseek": ["deepseek-chat", "deepseek-reasoner"],
            "anthropic": ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229"],
            "google": ["gemini-1.5-pro", "gemini-1.5-flash"],
            "ollama": ["llama3", "mistral", "llava"],
            "azure": ["gpt-4"],
            "aws": ["anthropic.claude-3-sonnet-20240229-v1:0"],
            "nebius": ["black-forest-labs/flux-schnell", "stability-ai/sdxl"],
        }
        
        default_base_urls = {
            "openai": "https://api.openai.com/v1",
            "aliyun": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "deepseek": "https://api.deepseek.com",
            "anthropic": "https://api.anthropic.com/v1",
            "google": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "ollama": "http://localhost:11434/v1",
            "nebius": "https://api.studio.nebius.ai/v1/",
        }

        # Iterate over PROVIDER_MAP keys
        for key in ModelFactory.PROVIDER_MAP.keys():
            # Skip aliases that are less common if you want a cleaner list
            # For now, we include everything or filter duplicates
            
            configs[key] = {
                "label": key.capitalize(),
                "value": key,
                "models": default_models.get(key, []),
                "baseUrl": default_base_urls.get(key, "")
            }
            
        return configs

    @staticmethod
    def _get_model_class(provider: str) -> Optional[Type[Model]]:
        """Dynamically load the model class for the given provider."""
        provider = (provider or "").lower()
        
        # 1. Check strict mapping
        if provider in ModelFactory.PROVIDER_MAP:
            module_name, class_name = ModelFactory.PROVIDER_MAP[provider]
            try:
                module = importlib.import_module(module_name)
                return getattr(module, class_name)
            except (ImportError, AttributeError):
                # If specific provider SDK is missing, fallback will handle it
                pass
        
        return None

    @staticmethod
    def create_model(llm_model: LLMModel) -> Model:
        api_key = llm_model.api_key or "dummy"
        base_url = llm_model.base_url
        provider = (llm_model.provider or "").lower()
        model_id = llm_model.model_id

        # 1. Try to get specific class
        model_cls = ModelFactory._get_model_class(provider)
        
        # 2. Fallback logic: Default to OpenAIChat if class not found
        if not model_cls:
            model_cls = OpenAIChat

        # 3. Prepare arguments dynamically based on signature
        kwargs: Dict[str, Any] = {}
        
        # Common Role Map (fixes compatibility for Aliyun/DeepSeek which dislike 'developer' role)
        role_map = {
            "system": "system",
            "developer": "system",
            "user": "user",
            "assistant": "assistant",
            "tool": "tool",
            "function": "function",
        }

        # Inspect signature to see what arguments are supported
        try:
            sig = inspect.signature(model_cls)
        except ValueError:
             # Handle built-in classes or others where signature might fail
             sig = inspect.signature(model_cls.__init__)
             
        params = sig.parameters

        # Helper to safely add arg if supported
        def add_arg(name, value):
            if name in params:
                kwargs[name] = value

        # Always pass ID
        add_arg("id", model_id)
        
        # API Key
        add_arg("api_key", api_key)
        
        # Role Map
        add_arg("role_map", role_map)

        # Base URL Handling
        if base_url:
            add_arg("base_url", base_url)
        else:
            if "base_url" in params:
                if provider == "aliyun":
                    # Keep the original hardcoded URL for Aliyun
                    add_arg("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
                elif provider == "deepseek":
                    add_arg("base_url", "https://api.deepseek.com")
                elif provider == "openai":
                    add_arg("base_url", None)

        # 4. Handle Multimodal configurations
        # Some models require explicit enablement of multimodal features or specific modality settings
        
        # For Nebius (Image Generation) or others that use 'modalities' param
        if "modalities" in params:
             # If model_type implies image/video generation, we might want to set this.
             # But usually defaults are fine. If specific override is needed:
             pass

        # For Gemini (Google), 'response_modalities' controls output type (TEXT, IMAGE, etc.)
        if "response_modalities" in params and llm_model.model_type:
            # Map 'image' model type to Gemini's expected format if needed
            # Currently Gemini default is usually text, but if we wanted to enforce image output:
            # if llm_model.model_type == "image":
            #    kwargs["response_modalities"] = ["image"]
            pass

        # Instantiate
        return model_cls(**kwargs)

    @staticmethod
    def is_multimodal_model(llm_model: LLMModel) -> bool:
        """
        Check if the model is known to support multimodal inputs (Images, Video, etc.).
        """
        mid = (llm_model.model_id or "").lower()
        (llm_model.provider or "").lower()
        
        # Known multimodal models
        if "gpt-4o" in mid or "gpt-4-turbo" in mid or "gpt-4-vision" in mid:
            return True
        if "claude-3" in mid: # Sonnet, Opus support vision
            return True
        if "gemini" in mid: # Gemini 1.5 Pro/Flash support video/image
            return True
        if "qwen-vl" in mid or "llava" in mid:
            return True
            
        return False

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
        判断是否应该使用 Agno 的手动推理（CoT）。
        如果模型本身支持推理（如 DeepSeek R1），通常我们会禁用 Agno 的推理，
        以避免重复推理或干扰。
        """
        provider = (llm_model.provider or "").lower()
        base_url = (llm_model.base_url or "").lower()

        # DeepSeek models often handle reasoning natively or are fast enough
        if "deepseek" in provider or "deepseek" in base_url:
            return False

        return True
