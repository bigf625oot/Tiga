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
from app.core.config import settings


class ModelFactory:
    """
    模型工厂类，用于根据提供程序名称动态加载模型类。
    """

    @staticmethod
    def get_provider_configs() -> Dict[str, Any]:
        """
        Return the supported providers and their default configurations.
        Used by the frontend to populate dropdowns.
        """
        configs = {}
        providers_cfg = settings.LLM_PROVIDERS_CONFIG
        class_map = providers_cfg.get("class_map", {})
        default_models = providers_cfg.get("default_models", {})
        default_base_urls = providers_cfg.get("default_base_urls", {})

        for key in class_map.keys():
            # Skip aliases for a cleaner list if desired, but here we include all
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
        class_map = settings.LLM_PROVIDERS_CONFIG.get("class_map", {})
        
        if provider in class_map:
            module_name, class_name = class_map[provider]
            try:
                module = importlib.import_module(module_name)
                return getattr(module, class_name)
            except (ImportError, AttributeError):
                # If specific provider SDK is missing, fallback will handle it
                pass
        
        return None

    @staticmethod
    def resolve_default_llm_model(settings_obj) -> LLMModel:
        """
        根据 settings 解析默认的 LLMModel 对象。
        """
        provider = settings_obj.DEFAULT_LLM_PROVIDER
        model_id = settings_obj.DEFAULT_LLM_MODEL_ID
        api_key = getattr(settings_obj, f"{provider.upper()}_API_KEY", None) or settings_obj.OPENAI_API_KEY
        
        return LLMModel(
            model_id=model_id,
            provider=provider,
            api_key=api_key or "dummy",
        )

    @staticmethod
    def resolve_llm_model_from_id(model_id: str, settings_obj) -> LLMModel:
        """
        根据 model_id 和 settings 尝试构建一个 LLMModel 对象。
        """
        mid_lower = model_id.lower()
        provider = settings_obj.DEFAULT_LLM_PROVIDER
        
        # Heuristic: try to match provider from config keys
        class_map = settings_obj.LLM_PROVIDERS_CONFIG.get("class_map", {})
        for p in class_map.keys():
            if p in mid_lower:
                provider = p
                break
        
        api_key = getattr(settings_obj, f"{provider.upper()}_API_KEY", None) or settings_obj.OPENAI_API_KEY
        
        return LLMModel(
            model_id=model_id,
            provider=provider,
            api_key=api_key or "dummy",
        )

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
        role_map = settings.LLM_PROVIDERS_CONFIG.get("role_map", {})

        # Inspect signature to see what arguments are supported
        try:
            sig = inspect.signature(model_cls)
        except ValueError:
             # Handle built-in classes or others where signature might fail
             sig = inspect.signature(model_cls.__init__)
             
        params = sig.parameters

        # Helper to safely add arg if supported
        def add_arg(name, value):
            if name in params and value is not None:
                kwargs[name] = value

        # --- Essential Config ---
        add_arg("id", model_id)
        add_arg("api_key", api_key)
        add_arg("role_map", role_map)
        
        # --- Inference Parameters ---
        add_arg("temperature", llm_model.temperature)
        add_arg("top_p", llm_model.top_p)
        add_arg("max_tokens", llm_model.max_output_tokens)
        
        # --- Base URL Handling ---
        if base_url:
            add_arg("base_url", base_url)
        else:
            default_urls = settings.LLM_PROVIDERS_CONFIG.get("default_base_urls", {})
            if "base_url" in params and provider in default_urls:
                add_arg("base_url", default_urls[provider])

        # --- Extra Params (JSON) ---
        if llm_model.extra_params:
            for k, v in llm_model.extra_params.items():
                if k in params:
                    kwargs[k] = v

        # Instantiate
        return model_cls(**kwargs)

    @staticmethod
    def is_multimodal_model(llm_model: LLMModel) -> bool:
        """
        Check if the model supports multimodal inputs.
        """
        return bool(llm_model.supports_vision)

    @staticmethod
    def is_reasoning_model(llm_model: LLMModel) -> bool:
        """
        Check if the model supports native reasoning.
        """
        return bool(llm_model.supports_reasoning)

    @staticmethod
    def should_use_agno_reasoning(llm_model: LLMModel) -> bool:
        """
        判断是否应该使用 Agno 的手动推理（CoT）。
        """
        return bool(llm_model.use_agno_cot)
