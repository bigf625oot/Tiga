
try:
    import lightrag.prompt as _lp
    print("Keys in PROMPTS:", list(_lp.PROMPTS.keys()))
except ImportError:
    print("Could not import lightrag.prompt")
except Exception as e:
    print(f"Error: {e}")
