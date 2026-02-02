"""Safe calculator tool for mathematical expressions."""

import ast
import operator
from typing import Dict, Any, Union

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


class Calculator:
    """
    Safe mathematical expression evaluator.

    Supports: +, -, *, /, **, parentheses, and numbers.
    Does NOT allow: variables, function calls, imports, or any other Python code.
    """

    def __init__(self, max_expression_length: int = 500):
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

    def __call__(self, expression: str) -> Dict[str, Any]:
        """
        Execute the calculator tool.

        Args:
            expression: Mathematical expression to evaluate

        Returns:
            Dictionary with result or error
        """
        try:
            result = self.calculate(expression)
            return {
                "success": True,
                "result": result,
                "expression": expression
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "expression": expression
            }
