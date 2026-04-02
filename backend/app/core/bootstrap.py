"""
系统启动补丁模块
处理所有必要的系统补丁、模块别名和环境设置
在导入任何其他应用模块或第三方库之前调用
"""
import sys
import asyncio


def apply_patches():
    """
    应用所有必要的启动补丁和配置
    必须在导入任何其他应用模块或第三方库之前调用
    """
    _patch_duckduckgo()
    _setup_asyncio()
    _patch_agno_json()


def _patch_agno_json():
    """
    修复 agno 在解析带有 <think> 标签的 JSON 时报错的问题
    """
    try:
        import re
        import agno.utils.string as agno_string

        if getattr(agno_string, "_is_patched_for_think_tags", False):
            return

        original_clean_json = agno_string._clean_json_content

        def _patched_clean_json_content(content: str) -> str:
            # 剥离 <think>...</think> 标签，支持 DeepSeek 等推理模型的输出
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            # 兼容某些模型可能输出的 <thought> / <thinking> 标签
            content = re.sub(r'<thought>.*?</thought>', '', content, flags=re.DOTALL).strip()
            content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL).strip()
            return original_clean_json(content)

        agno_string._clean_json_content = _patched_clean_json_content
        agno_string._is_patched_for_think_tags = True
    except ImportError:
        pass


def _patch_duckduckgo():
    """
    修复 duckduckgo_search 导入问题
    当只安装了 duckduckgo_search 而不是 ddgs 时，某些库会报错
    """
    try:
        import duckduckgo_search

        sys.modules["ddgs"] = duckduckgo_search
    except ImportError:
        pass


def _setup_asyncio():
    """
    Configure asyncio event loop policies and patches.
    """
    # Set Windows Event Loop Policy to avoid "RuntimeError: Event loop is closed" or anyio issues
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Patch asyncio to allow nested event loops (fixes "NoEventLoopError" in some environments)
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass

