"""Safe calculator tool for mathematical expressions.

This module provides a safe AST-based calculator that evaluates mathematical
expressions without using eval() or exec(). It only supports basic arithmetic
operations and numeric literals.

Key Classes:
    Calculator: Safe mathematical expression evaluator inheriting from ToolBase

Security:
    - Uses AST parsing (no eval/exec)
    - Only allows numeric operations
    - No variables, functions, or imports
    - Expression length limited
    - Division by zero protection

Usage:
    from src.agent.tools.calculator import Calculator

    calc = Calculator()
    result = calc(expression="2 + 3 * 4")
    print(result["result"])  # 14
"""

import ast
import operator
from typing import Dict, Any, Union

from src.agent.tools.base_tool import ToolBase
from src.shared.config import TIMEOUTS

# Safe operators for evaluation
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


class Calculator(ToolBase):
    """Safe mathematical expression evaluator.

    Inherits from ToolBase for standard error handling and result formatting.

    Supports: +, -, *, /, **, parentheses, and numbers.
    Does NOT allow: variables, function calls, imports, or any other Python code.

    Attributes:
        max_expression_length: Maximum allowed expression length (default: 500)

    Security Guarantees:
        - AST-based evaluation (no exec/eval)
        - Only numeric operations allowed
        - Division by zero protection
        - Expression length validation

    Examples:
        >>> calc = Calculator()
        >>> result = calc(expression="2 + 3 * 4")
        >>> result["result"]
        14

        >>> result = calc(expression="(100 / 5) ** 2")
        >>> result["result"]
        400.0
    """

    def __init__(self, max_expression_length: int = 500):
        """Initialize calculator with expression length limit.

        Args:
            max_expression_length: Maximum characters in expression (default: 500)
        """
        super().__init__(name="calculator", timeout=TIMEOUTS.get("calculator", 1))
        self.max_expression_length = max_expression_length

    def calculate(self, expression: str) -> Union[float, int]:
        """
        Safely evaluate a mathematical expression.

        Args:
            expression: Mathematical expression as string (e.g., "2 + 3 * 4")

        Returns:
            Result of the calculation

        Raises:
            ValueError: If expression is invalid or unsafe
        """
        # Validate length
        if len(expression) > self.max_expression_length:
            raise ValueError(
                f"Expression too long ({len(expression)} > {self.max_expression_length})"
            )

        # Remove whitespace
        expression = expression.strip()

        if not expression:
            raise ValueError("Empty expression")

        try:
            # Parse the expression
            tree = ast.parse(expression, mode='eval')

            # Evaluate safely
            result = self._eval_node(tree.body)

            return result

        except SyntaxError as e:
            raise ValueError(f"Invalid mathematical expression: {e}")
        except Exception as e:
            raise ValueError(f"Error evaluating expression: {e}")

    def _eval_node(self, node):
        """Recursively evaluate AST node."""
        if isinstance(node, ast.Num):
            # Number literal (int or float)
            return node.n

        elif isinstance(node, ast.Constant):
            # Constants in newer Python versions
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported constant type: {type(node.value)}")

        elif isinstance(node, ast.BinOp):
            # Binary operation (e.g., 2 + 3)
            if type(node.op) not in SAFE_OPERATORS:
                raise ValueError(f"Unsupported operation: {type(node.op).__name__}")

            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            operator_fn = SAFE_OPERATORS[type(node.op)]

            # Handle division by zero
            if isinstance(node.op, ast.Div) and right == 0:
                raise ValueError("Division by zero")

            return operator_fn(left, right)

        elif isinstance(node, ast.UnaryOp):
            # Unary operation (e.g., -5)
            if type(node.op) not in SAFE_OPERATORS:
                raise ValueError(f"Unsupported operation: {type(node.op).__name__}")

            operand = self._eval_node(node.operand)
            operator_fn = SAFE_OPERATORS[type(node.op)]
            return operator_fn(operand)

        else:
            raise ValueError(
                f"Unsupported expression type: {type(node).__name__}. "
                "Only basic arithmetic operations are allowed."
            )

    def get_tool_definition(self) -> Dict[str, Any]:
        """Get tool definition for LLM tool calling."""
        return {
            "name": "calculator",
            "description": (
                "Evaluates mathematical expressions. Supports basic arithmetic: "
                "addition (+), subtraction (-), multiplication (*), division (/), "
                "exponentiation (**), and parentheses. "
                "Use this for any calculations involving numbers."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": (
                            "The mathematical expression to evaluate. "
                            "Example: '(67000000 / 643801)' or '2023 - 1879'"
                        )
                    }
                },
                "required": ["expression"]
            }
        }

    def _execute_internal(self, expression: str) -> Union[float, int]:
        """Internal execution logic for calculator.

        Args:
            expression: Mathematical expression to evaluate

        Returns:
            Calculated result

        Raises:
            ValueError: If expression is invalid or unsafe

        Note:
            Error handling is managed by ToolBase.__call__()
        """
        return self.calculate(expression)
