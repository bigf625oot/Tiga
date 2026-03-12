from agno.tools import Toolkit

class CalculatorTools(Toolkit):
    _name = "calculator"
    _label = "计算器"
    _description = "基础数学运算工具"
    """
    进行数学计算的工具。
    支持加减乘除等基本运算。
    """
    def __init__(self):
        super().__init__(name="calculator")
        self.register(self.calculate)

    def calculate(self, expression: str) -> str:
        """
        Evaluates a mathematical expression.
        Args:
            expression: The expression to evaluate (e.g., "2 + 2").
        """
        try:
            # Dangerous if not sandboxed, but for simple calculator it's ok-ish for demo
            # Better to use a safe eval lib, but for now simple eval with limited scope
            allowed_names = {"abs": abs, "round": round, "min": min, "max": max, "pow": pow}
            return str(eval(expression, {"__builtins__": None}, allowed_names))
        except Exception as e:
            return f"Error evaluating expression: {e}"
