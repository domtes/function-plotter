# Parsing is the process of turning a sequence
# of tokens into a tree representation:
#
#                             Add
#                  Parser     / \
#  "1 + 2 * 3"    ------->   1  Mul
#                               / \
#                              2   3
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
import math
import operator

# The first step is to generate a list of tokens.
# Tokens are the supported symbol classes, they have a type tag


class TokenType(Enum):
    ERROR = -1
    OPERATOR = 0
    VARIABLE = 1
    SEPARATOR = 2
    FLOAT = 3
    FUNCTION = 4
    CONSTANT = 5


# The token can optionally capture a string value.
# This will be used later by the parser to build the synctatic tree.


@dataclass
class Token:
    type: TokenType
    value: str | None = None


operators: set[str] = {"+", "-", "*", "/", "^"}
functions: set[str] = {"abs", "cos", "sin", "tan", "atan", "exp", "ln", "log"}
separators: set[str] = {"(", ")"}
variables: set[str] = {"x"}
constants: set[str] = {"e", "pi"}


# The lexer is a generator function that yields token as it scans the input string
def lex(input: str) -> Iterator[Token]:
    i = 0

    while i < len(input):
        char = input[i]

        # whitespace
        if char.isspace():
            i += 1
            continue

        # separators
        if char in separators:
            yield Token(type=TokenType.SEPARATOR, value=char)
            i += 1
            continue

        # operators
        if char in operators:
            yield Token(type=TokenType.OPERATOR, value=char)
            i += 1
            continue

        # variables
        if char in variables:
            yield Token(type=TokenType.VARIABLE, value=char)
            i += 1
            continue

        # functions and constants
        if char.isalpha():
            j = i + 1
            while j < len(input) and input[j].isalpha():
                j += 1

            name = input[i:j]
            if name in constants:
                yield Token(type=TokenType.CONSTANT, value=name)
                i = j
                continue

            if name not in functions:
                yield Token(
                    type=TokenType.ERROR, value=f"unknown function name '{name}'"
                )
                return

            yield Token(type=TokenType.FUNCTION, value=name)

            i = j
            continue

        # float numbers
        if (
            char.isdigit()
            or (char == ".")
            or (
                (char == "+" and input[i + 1].isdigit())
                or (char == "-" and input[i + 1].isdigit())
            )
        ):
            j = i + 1

            has_dot = char == "."
            while j < len(input) and (input[j].isdigit() or input[j] == "."):
                has_dot = has_dot or input[j] == "."
                j += 1

            if has_dot:
                if input[j - 1] == ".":
                    yield Token(
                        type=TokenType.ERROR, value="number after dot was expected"
                    )
                    return

            yield Token(type=TokenType.FLOAT, value=input[i:j])
            i = j
            continue

        yield Token(type=TokenType.ERROR, value="not an accepted character")
        return


class Expression(ABC):
    @abstractmethod
    def eval(self, x: float) -> float:
        pass


@dataclass
class Atom(Expression):
    token: Token

    _constants = {
        "pi": math.pi,
        "e": math.e,
    }

    def eval(self, x: float) -> float:
        if self.token.type == TokenType.VARIABLE:
            return x
        if self.token.type == TokenType.FLOAT:
            return float(self.token.value or 0)
        if self.token.type == TokenType.CONSTANT:
            return self._constants[self.token.value]
        return 0.0


@dataclass
class FunctionExpression(Expression):
    function: str
    argument: Expression

    _funcs = {
        "abs": abs,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "atan": math.atan,
        "exp": math.exp,
        "ln": math.log,
        "log": math.log10,
    }

    def eval(self, x: float) -> float:
        func = self._funcs.get(self.function)
        if not func:
            raise ValueError(f"Unknown function {self.function}")
        return func(x)


@dataclass
class InfixExpression(Expression):
    operator: str
    lvalue: Expression
    rvalue: Expression

    _ops = {
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.truediv,
        "^": operator.pow,
    }

    _binding_power = {
        "+": (1, 2),
        "-": (1, 2),
        "*": (3, 4),
        "/": (3, 4),
        "^": (4, 5),
    }

    # Prefix binding power for unary minus (lower than ^, so -2^3 = -(2^3))
    _prefix_binding_power = {"-": 3}

    def eval(self, x: float) -> float:
        op_func = self._ops.get(self.operator)
        if not op_func:
            raise ValueError(f"Unknown operator {self.operator}")
        return op_func(self.lvalue.eval(x), self.rvalue.eval(x))


class Parser:
    def __init__(self, tokens: Iterator[Token]):
        self.tokens = deque(tokens)

    def peek(self) -> Token | None:
        return self.tokens[0] if self.tokens else None

    def consume(self) -> Token:
        return self.tokens.popleft()

    def _parse_expression_bp(self, min_bp: int) -> Expression:
        token = self.consume()

        if token.type == TokenType.SEPARATOR and token.value == "(":
            lhs = self._parse_expression_bp(0)
            self.consume()  # consume closing ')'
        elif token.type == TokenType.FUNCTION and token.value is not None:
            self.consume()  # consume opening '('
            argument = self._parse_expression_bp(0)
            self.consume()  # consume closing ')'
            lhs = FunctionExpression(function=token.value, argument=argument)
        elif token.type == TokenType.OPERATOR and token.value == "-":
            # Unary minus: desugar to 0 - operand
            prefix_bp = InfixExpression._prefix_binding_power["-"]
            operand = self._parse_expression_bp(prefix_bp)
            lhs = InfixExpression(
                operator="-",
                lvalue=Atom(Token(type=TokenType.FLOAT, value="0")),
                rvalue=operand,
            )
        else:
            lhs = Atom(token)

        while True:
            op = self.peek()
            if op is None or op.value is None:
                break

            if op.type != TokenType.OPERATOR:
                break

            l_bp, r_bp = InfixExpression._binding_power[op.value]
            if l_bp < min_bp:
                break

            self.consume()

            rhs = self._parse_expression_bp(r_bp)
            lhs = InfixExpression(operator=op.value, lvalue=lhs, rvalue=rhs)

        return lhs

    def parse_expression(self) -> Expression:
        return self._parse_expression_bp(min_bp=0)


def parse(expression: str) -> Expression:
    return Parser(lex(expression)).parse_expression()


def eval_in_range(
    expression: str, start: float, stop: float, increment: float
) -> tuple[list[float], list[float]]:
    if stop < start:
        raise ValueError("range must be provided in crescent order")

    parsed_expression = parse(expression)

    n = 1
    x = start
    domain = []
    values = []
    while x < stop:
        domain.append(x)
        values.append(parsed_expression.eval(x))
        x += increment
        n += 1

    return domain, values
