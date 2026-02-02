"""Safe calculator tool implementation."""

import ast
import operator
import math
import logging
from typing import Dict, Any, Union

from src.agent.tools.base import BaseTool, RateLimiter, RateLimiters
from src.shared.models import ToolMode

logger = logging.getLogger(__name__)


# Safe operators for evaluation
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Safe functions
SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "exp": math.exp,
}

# Safe constants
SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "inf": math.inf,
}


class CalculatorTool(BaseTool):
    """
    Safe mathematical expression evaluator.

    Supports basic arithmetic, common math functions, and constants.
    Uses AST parsing to prevent code injection attacks.
    """

    TOOL_NAME = "calculator"
    TOOL_DESCRIPTION = (
        "Evaluates mathematical expressions safely. Supports basic arithmetic "
        "(+, -, *, /, **, %, //), math functions (sqrt, log, sin, cos, tan, abs, round), "
        "and constants (pi, e). Use this for any calculations involving numbers, "
        "percentages, or mathematical operations."
    )
    TOOL_MODE = ToolMode.CORE
    DEFAULT_TIMEOUT = 1.0  # Calculator should be instant
    MAX_RETRIES = 0  # No retries needed for local computation
    CACHE_TTL = 86400.0  # Cache calculation results

    RATE_LIMIT_RPS = 1000.0  # Effectively unlimited
    RATE_LIMIT_BURST = 100

    def __init__(
        self,
        max_expression_length: int = 500,
        max_result_value: float = 1e308,
        **kwargs
    ):
        """
        Initialize calculator tool.

        Args:
            max_expression_length: Maximum expression length to evaluate
            max_result_value: Maximum allowed result value
            **kwargs: Additional BaseTool arguments
        """
        # Override with unlimited rate limiter
        if "rate_limiter" not in kwargs:
            kwargs["rate_limiter"] = RateLimiters.unlimited()

        super().__init__(**kwargs)

        self.max_expression_length = max_expression_length
        self.max_result_value = max_result_value

    def _execute(self, expression: str) -> Dict[str, Any]:
        """
        Evaluate a mathematical expression.

        Args:
            expression: Mathematical expression to evaluate

        Returns:
            Dictionary with calculation result
        """
        # Validate input
        if not expression or not expression.strip():
            return {
                "success": False,
                "error": "Empty expression",
                "expression": expression
            }

        expression = expression.strip()

        # Check length
        if len(expression) > self.max_expression_length:
            return {
                "success": False,
                "error": f"Expression too long ({len(expression)} > {self.max_expression_length})",
                "expression": expression[:100] + "..."
            }

        try:
            # Preprocess expression
            processed = self._preprocess_expression(expression)

            # Parse the expression
            tree = ast.parse(processed, mode='eval')

            # Evaluate safely
            result = self._eval_node(tree.body)

            # Validate result
            if result is None:
                return {
                    "success": False,
                    "error": "Expression evaluated to None",
                    "expression": expression
                }

            if isinstance(result, (int, float)):
                # Check for overflow
                if abs(result) > self.max_result_value:
                    return {
                        "success": False,
                        "error": f"Result too large (>{self.max_result_value})",
                        "expression": expression
                    }

                # Check for NaN/Inf
                if math.isnan(result):
                    return {
                        "success": False,
                        "error": "Result is undefined (NaN)",
                        "expression": expression
                    }

                if math.isinf(result):
                    return {
                        "success": True,
                        "result": "infinity" if result > 0 else "-infinity",
                        "expression": expression,
                        "note": "Result is infinite"
                    }

            # Round very small numbers to zero
            if isinstance(result, float) and abs(result) < 1e-15:
                result = 0.0

            return {
                "success": True,
                "result": result,
                "expression": expression
            }

        except ZeroDivisionError:
            return {
                "success": False,
                "error": "Division by zero is undefined",
                "expression": expression
            }
        except ValueError as e:
            error_msg = str(e)
            if "math domain" in error_msg.lower():
                return {
                    "success": False,
                    "error": "Mathematical domain error (e.g., sqrt of negative number)",
                    "expression": expression
                }
            return {
                "success": False,
                "error": f"Invalid expression: {error_msg}",
                "expression": expression
            }
        except SyntaxError as e:
            return {
                "success": False,
                "error": f"Syntax error in expression: {e}",
                "expression": expression
            }
        except Exception as e:
            logger.error(f"Calculator error: {e}")
            return {
                "success": False,
                "error": f"Evaluation error: {str(e)}",
                "expression": expression
            }

    def _preprocess_expression(self, expression: str) -> str:
        """Preprocess expression to handle common variations."""
        # Replace common text representations
        replacements = {
            "×": "*",
            "÷": "/",
            "^": "**",
            "√": "sqrt",
        }
        for old, new in replacements.items():
            expression = expression.replace(old, new)

        return expression

    def _eval_node(self, node) -> Union[int, float]:
        """Recursively evaluate AST node."""
        # Number literal
        if isinstance(node, ast.Num):
            return node.n

        # Constant (Python 3.8+)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported constant type: {type(node.value)}")

        # Binary operation
        if isinstance(node, ast.BinOp):
            if type(node.op) not in SAFE_OPERATORS:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")

            left = self._eval_node(node.left)
            right = self._eval_node(node.right)

            # Special handling for division by zero
            if isinstance(node.op, (ast.Div, ast.FloorDiv)) and right == 0:
                raise ZeroDivisionError()

            # Special handling for power (prevent huge computations)
            if isinstance(node.op, ast.Pow):
                if isinstance(right, (int, float)) and abs(right) > 1000:
                    raise ValueError("Exponent too large (max 1000)")

            return SAFE_OPERATORS[type(node.op)](left, right)

        # Unary operation
        if isinstance(node, ast.UnaryOp):
            if type(node.op) not in SAFE_OPERATORS:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")

            operand = self._eval_node(node.operand)
            return SAFE_OPERATORS[type(node.op)](operand)

        # Function call
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls are allowed")

            func_name = node.func.id.lower()

            if func_name not in SAFE_FUNCTIONS:
                raise ValueError(
                    f"Unknown function: {func_name}. "
                    f"Allowed: {', '.join(SAFE_FUNCTIONS.keys())}"
                )

            # Evaluate arguments
            args = [self._eval_node(arg) for arg in node.args]

            # Call function
            return SAFE_FUNCTIONS[func_name](*args)

        # Variable name (for constants)
        if isinstance(node, ast.Name):
            name = node.id.lower()
            if name in SAFE_CONSTANTS:
                return SAFE_CONSTANTS[name]
            raise ValueError(
                f"Unknown variable: {node.id}. "
                f"Allowed constants: {', '.join(SAFE_CONSTANTS.keys())}"
            )

        raise ValueError(
            f"Unsupported expression type: {type(node).__name__}. "
            "Only arithmetic operations, math functions, and constants are allowed."
        )

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": (
                        "The mathematical expression to evaluate. "
                        "Examples: '(67000000 / 643801)', '2023 - 1879', "
                        "'sqrt(144)', 'log10(1000)', '15 * 1.08'"
                    )
                }
            },
            "required": ["expression"]
        }

    @staticmethod
    def is_available() -> bool:
        """Calculator is always available."""
        return True
