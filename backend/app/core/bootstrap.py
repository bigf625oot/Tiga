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

