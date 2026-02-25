# src/infrastructure/llm/calc.py
"""
Safe evaluator for mathematical expressions.
Used by the calculate_expression tool to prevent code injection.
"""

import ast
import operator as op
import math
from typing import Any
import re


ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.FloorDiv: op.floordiv,
}

ALLOWED_UNARY = {
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}

ALLOWED_NAMES = {
    'abs': abs,
    'round': round,
    'min': min,
    'max': max,
    'sum': sum,
    'pow': pow,
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'asin': math.asin,
    'acos': math.acos,
    'atan': math.atan,
    'log': math.log,
    'log10': math.log10,
    'exp': math.exp,
    'pi': math.pi,
    'e': math.e,
}


def safe_eval(expression: str) -> Any:
    """
    Evaluate a mathematical expression safely.

    Supported:
    - Basic arithmetic: + - * / ** % //
    - Parentheses
    - Selected math functions & constants (sin, cos, sqrt, pi, e, ...)
    - No variable assignment, no function definitions, no imports, no __builtins__

    Raises:
        ValueError, TypeError, SyntaxError on invalid/unsafe input
    """
    def _evaluate(node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.BinOp):
            left = _evaluate(node.left)
            right = _evaluate(node.right)
            op_type = type(node.op)
            if op_type not in ALLOWED_OPERATORS:
                raise TypeError(f"Operator not allowed: {op_type.__name__}")
            return ALLOWED_OPERATORS[op_type](left, right)

        if isinstance(node, ast.UnaryOp):
            operand = _evaluate(node.operand)
            op_type = type(node.op)
            if op_type not in ALLOWED_UNARY:
                raise TypeError(f"Unary operator not allowed: {op_type.__name__}")
            return ALLOWED_UNARY[op_type](operand)

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise TypeError("Only simple named function calls allowed")
            name = node.func.id
            if name not in ALLOWED_NAMES:
                raise ValueError(f"Function not allowed: {name}")
            args = [_evaluate(arg) for arg in node.args]
            return ALLOWED_NAMES[name](*args)

        if isinstance(node, ast.Name):
            if node.id in ALLOWED_NAMES:
                return ALLOWED_NAMES[node.id]
            raise NameError(f"Undefined name: {node.id}")

        raise TypeError(f"Unsupported node type: {type(node).__name__}")

    try:
        tree = ast.parse(expression.strip(), mode='eval')
        return _evaluate(tree.body)
    except SyntaxError as e:
        raise SyntaxError(f"Syntax error in expression: {e}")
    except Exception as e:
        raise type(e)(f"Evaluation failed: {e}")


#------------------
def extract_math_from_text(text: str) -> str | None:
    """
    Extract the first plausible math expression from natural language input.
    """

    pattern = r"[a-zA-Z0-9_+\-*/().^% ]+"
    matches = re.findall(pattern, text)

    if not matches:
        return None

    candidates = []

    for m in matches:
        stripped = m.strip().rstrip("?.!,")

        if len(stripped) < 3:
            continue

        # Must have balanced parentheses
        if stripped.count("(") != stripped.count(")"):
            continue

        # MUST contain a digit OR operator
        has_digit = any(c.isdigit() for c in stripped)
        has_operator = any(op in stripped for op in "+-*/^%")

        if not (has_digit or has_operator):
            continue

        candidates.append(stripped)

    if not candidates:
        return None

    return max(candidates, key=len)
#------------------


# Quick self-test when running the file directly
if __name__ == "__main__":
    examples = [
        "2 + 3 * 4",
        "sin(pi / 2) + sqrt(16)",
        "what is (45 * 2.3 + 17) / 9 ?",
        "2 ** 10",
        "invalid javascript here",
    ]

    for ex in examples:
        try:
            expr = extract_math_from_text(ex)
            if expr:
                result = safe_eval(expr)
                print(f"Input: {ex!r:40} → {expr!r:20} → {result}")
            else:
                print(f"Input: {ex!r:40} → No expression found")
        except Exception as e:
            print(f"Input: {ex!r:40} → Error: {e}")