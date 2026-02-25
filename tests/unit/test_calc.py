import pytest
from src.infrastructure.llm.calc import safe_eval, extract_math_from_text


def test_safe_eval_basic():
    assert safe_eval("2 + 3 * 4") == 14
    assert safe_eval("(10 - 2) ** 3") == 512
    assert safe_eval("sin(pi / 2) + sqrt(16)") == pytest.approx(5.0)


def test_safe_eval_disallowed():
    # Your safe_eval raises SyntaxError for "import os" — that's fine
    # We just want to confirm it DOES raise something
    with pytest.raises((SyntaxError, TypeError, ValueError)):
        safe_eval("import os")


def test_extract_math():
    expr1 = extract_math_from_text("what is 45*2 + 17?")
    assert expr1 and "45*2 + 17" in expr1

    expr2 = extract_math_from_text("sin(pi/4)")
    assert expr2 and "sin(pi/4)" in expr2

    expr3 = extract_math_from_text("calculate 2 ** 10")
    assert expr3 and "2 ** 10" in expr3

    assert extract_math_from_text("hello world") is None