import pytest

from plotter.parser import (
    lex,
    parse,
    Atom,
    Token,
    TokenType,
    InfixExpression,
    FunctionExpression,
)


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("+", [Token(type=TokenType.OPERATOR, value="+")]),
        ("x", [Token(type=TokenType.VARIABLE, value="x")]),
        (".", [Token(type=TokenType.ERROR, value="number after dot was expected")]),
        ("1.", [Token(type=TokenType.ERROR, value="number after dot was expected")]),
        (".1", [Token(type=TokenType.FLOAT, value=".1")]),
        ("3.14", [Token(type=TokenType.FLOAT, value="3.14")]),
        (
            "2 + 3",
            [
                Token(type=TokenType.FLOAT, value="2"),
                Token(type=TokenType.OPERATOR, value="+"),
                Token(type=TokenType.FLOAT, value="3"),
            ],
        ),
        (
            "x - 4.5",
            [
                Token(type=TokenType.VARIABLE, value="x"),
                Token(type=TokenType.OPERATOR, value="-"),
                Token(type=TokenType.FLOAT, value="4.5"),
            ],
        ),
        (
            "x - 4.5 * 2.34 + 5.2",
            [
                Token(type=TokenType.VARIABLE, value="x"),
                Token(type=TokenType.OPERATOR, value="-"),
                Token(type=TokenType.FLOAT, value="4.5"),
                Token(type=TokenType.OPERATOR, value="*"),
                Token(type=TokenType.FLOAT, value="2.34"),
                Token(type=TokenType.OPERATOR, value="+"),
                Token(type=TokenType.FLOAT, value="5.2"),
            ],
        ),
        (
            "(x - 4.5) * (2.34 + 5.2)",
            [
                Token(type=TokenType.SEPARATOR, value="("),
                Token(type=TokenType.VARIABLE, value="x"),
                Token(type=TokenType.OPERATOR, value="-"),
                Token(type=TokenType.FLOAT, value="4.5"),
                Token(type=TokenType.SEPARATOR, value=")"),
                Token(type=TokenType.OPERATOR, value="*"),
                Token(type=TokenType.SEPARATOR, value="("),
                Token(type=TokenType.FLOAT, value="2.34"),
                Token(type=TokenType.OPERATOR, value="+"),
                Token(type=TokenType.FLOAT, value="5.2"),
                Token(type=TokenType.SEPARATOR, value=")"),
            ],
        ),
        (
            "sin(x) * 2.0",
            [
                Token(type=TokenType.FUNCTION, value="sin"),
                Token(type=TokenType.SEPARATOR, value="("),
                Token(type=TokenType.VARIABLE, value="x"),
                Token(type=TokenType.SEPARATOR, value=")"),
                Token(type=TokenType.OPERATOR, value="*"),
                Token(type=TokenType.FLOAT, value="2.0"),
            ],
        ),
        (
            "3.14 * coz(x)",
            [
                Token(type=TokenType.FLOAT, value="3.14"),
                Token(type=TokenType.OPERATOR, value="*"),
                Token(type=TokenType.ERROR, value="unknown function name 'coz'"),
            ],
        ),
        (
            "3.14 * cos(2.4 * x) ^ 0.5",
            [
                Token(type=TokenType.FLOAT, value="3.14"),
                Token(type=TokenType.OPERATOR, value="*"),
                Token(type=TokenType.FUNCTION, value="cos"),
                Token(type=TokenType.SEPARATOR, value="("),
                Token(type=TokenType.FLOAT, value="2.4"),
                Token(type=TokenType.OPERATOR, value="*"),
                Token(type=TokenType.VARIABLE, value="x"),
                Token(type=TokenType.SEPARATOR, value=")"),
                Token(type=TokenType.OPERATOR, value="^"),
                Token(type=TokenType.FLOAT, value="0.5"),
            ],
        ),
    ],
)
def test_lexer(expression, expected):
    assert list(lex(expression)) == expected


@pytest.mark.parametrize(
    "expression, expected",
    argvalues=[
        ("3.14", Atom(Token(type=TokenType.FLOAT, value="3.14"))),
        (
            "2 + 2",
            InfixExpression(
                operator="+",
                lvalue=Atom(token=Token(type=TokenType.FLOAT, value="2")),
                rvalue=Atom(token=Token(type=TokenType.FLOAT, value="2")),
            ),
        ),
        (
            "2 + 3 * 4 + 5",
            InfixExpression(
                operator="+",
                lvalue=InfixExpression(
                    operator="+",
                    lvalue=Atom(Token(type=TokenType.FLOAT, value="2")),
                    rvalue=InfixExpression(
                        operator="*",
                        lvalue=Atom(Token(type=TokenType.FLOAT, value="3")),
                        rvalue=Atom(Token(type=TokenType.FLOAT, value="4")),
                    ),
                ),
                rvalue=Atom(Token(type=TokenType.FLOAT, value="5")),
            ),
        ),
        (
            "(2 + 3) * (4 + 5)",
            InfixExpression(
                operator="*",
                lvalue=InfixExpression(
                    operator="+",
                    lvalue=Atom(Token(type=TokenType.FLOAT, value="2")),
                    rvalue=Atom(Token(type=TokenType.FLOAT, value="3")),
                ),
                rvalue=InfixExpression(
                    operator="+",
                    lvalue=Atom(Token(type=TokenType.FLOAT, value="4")),
                    rvalue=Atom(Token(type=TokenType.FLOAT, value="5")),
                ),
            ),
        ),
        (
            "sin(x) + cos(x)",
            InfixExpression(
                operator="+",
                lvalue=FunctionExpression(
                    function="sin",
                    argument=Atom(token=Token(type=TokenType.VARIABLE, value="x")),
                ),
                rvalue=FunctionExpression(
                    function="cos",
                    argument=Atom(token=Token(type=TokenType.VARIABLE, value="x")),
                ),
            ),
        ),
    ],
)
def test_parser(expression, expected):
    assert parse(expression) == expected


# Helper to create the desugared unary minus AST (0 - operand)
def _neg(operand):
    return InfixExpression(
        operator="-",
        lvalue=Atom(Token(type=TokenType.FLOAT, value="0")),
        rvalue=operand,
    )


@pytest.mark.parametrize(
    "expression, expected",
    argvalues=[
        # Simple unary minus: -x => 0 - x
        (
            "-x",
            _neg(Atom(Token(type=TokenType.VARIABLE, value="x"))),
        ),
        # Double negation: --x => 0 - (0 - x)
        (
            "--x",
            _neg(_neg(Atom(Token(type=TokenType.VARIABLE, value="x")))),
        ),
        # Subtract a negative: 1 - -2 => 1 - (0 - 2)
        (
            "1 - -2",
            InfixExpression(
                operator="-",
                lvalue=Atom(Token(type=TokenType.FLOAT, value="1")),
                rvalue=_neg(Atom(Token(type=TokenType.FLOAT, value="2"))),
            ),
        ),
        # Negate function result: -sin(x) => 0 - sin(x)
        (
            "-sin(x)",
            _neg(
                FunctionExpression(
                    function="sin",
                    argument=Atom(Token(type=TokenType.VARIABLE, value="x")),
                )
            ),
        ),
        # Precedence: -2^3 should be -(2^3), not (-2)^3
        # With binding power 3, unary minus binds looser than ^ (4,5)
        (
            "-2^3",
            _neg(
                InfixExpression(
                    operator="^",
                    lvalue=Atom(Token(type=TokenType.FLOAT, value="2")),
                    rvalue=Atom(Token(type=TokenType.FLOAT, value="3")),
                )
            ),
        ),
        # Explicit parens: (-2)^3 groups the negation first
        (
            "(-2)^3",
            InfixExpression(
                operator="^",
                lvalue=_neg(Atom(Token(type=TokenType.FLOAT, value="2"))),
                rvalue=Atom(Token(type=TokenType.FLOAT, value="3")),
            ),
        ),
    ],
)
def test_unary_minus(expression, expected):
    assert parse(expression) == expected


@pytest.mark.parametrize(
    "expression, x, expected",
    [
        ("-x", 5, -5),
        ("--x", 5, 5),
        ("1 - -2", 0, 3),
        ("-2^3", 0, -8),  # -(2^3) = -8
        ("(-2)^3", 0, -8),  # (-2)^3 = -8
        ("-2^2", 0, -4),  # -(2^2) = -4
        ("(-2)^2", 0, 4),  # (-2)^2 = 4
    ],
)
def test_unary_minus_eval(expression, x, expected):
    assert parse(expression).eval(x) == expected
