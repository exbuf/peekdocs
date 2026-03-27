"""Boolean expression parser for docsearch.

Parses expressions like:
    (bob AND amy) OR (fred AND wilma)
    budget AND NOT draft
    (budget OR revenue) AND (cost OR profit)

Grammar (standard boolean precedence: NOT > AND > OR):
    expression  := or_expr
    or_expr     := and_expr (OR and_expr)*
    and_expr    := not_expr (AND not_expr)*
    not_expr    := NOT not_expr | primary
    primary     := LPAREN expression RPAREN | TERM
"""

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Union


# ─── AST Node Types ──────────────────────────────────────


@dataclass
class TermNode:
    """Leaf node: a single search term."""
    value: str


@dataclass
class AndNode:
    """Binary AND: both children must match."""
    left: 'ExprNode'
    right: 'ExprNode'


@dataclass
class OrNode:
    """Binary OR: either child must match."""
    left: 'ExprNode'
    right: 'ExprNode'


@dataclass
class NotNode:
    """Unary NOT: child must not match."""
    child: 'ExprNode'


ExprNode = Union[TermNode, AndNode, OrNode, NotNode]


# ─── Tokenizer ───────────────────────────────────────────


class TokenType(Enum):
    TERM = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    LPAREN = auto()
    RPAREN = auto()


@dataclass
class Token:
    type: TokenType
    value: str


_KEYWORDS = {"AND": TokenType.AND, "OR": TokenType.OR, "NOT": TokenType.NOT}


def tokenize(expression):
    """Tokenize a boolean expression string into a list of Tokens.

    Raises ValueError on empty expression or unterminated quotes.
    """
    if not expression or not expression.strip():
        raise ValueError("Empty expression.")

    tokens = []
    i = 0
    s = expression
    n = len(s)

    while i < n:
        ch = s[i]

        # Skip whitespace
        if ch.isspace():
            i += 1
            continue

        # Parentheses
        if ch == '(':
            tokens.append(Token(TokenType.LPAREN, '('))
            i += 1
            continue
        if ch == ')':
            tokens.append(Token(TokenType.RPAREN, ')'))
            i += 1
            continue

        # Quoted string
        if ch == '"':
            j = s.index('"', i + 1) if '"' in s[i + 1:] else -1
            if j == -1:
                raise ValueError(f"Unterminated quote starting at position {i}.")
            tokens.append(Token(TokenType.TERM, s[i + 1:j]))
            i = j + 1
            continue

        # Word (keyword or term)
        j = i
        while j < n and not s[j].isspace() and s[j] not in '()"':
            j += 1
        word = s[i:j]
        upper = word.upper()
        if upper in _KEYWORDS:
            tokens.append(Token(_KEYWORDS[upper], upper))
        else:
            tokens.append(Token(TokenType.TERM, word))
        i = j

    return tokens


# ─── Recursive-Descent Parser ────────────────────────────


def parse_expression(expression):
    """Parse a boolean expression string into an AST.

    Raises ValueError on syntax errors.
    """
    tokens = tokenize(expression)
    ast, pos = _parse_or(tokens, 0)
    if pos < len(tokens):
        raise ValueError(
            f"Unexpected token '{tokens[pos].value}' at position {pos}."
        )
    return ast


def _parse_or(tokens, pos):
    """or_expr := and_expr (OR and_expr)*"""
    left, pos = _parse_and(tokens, pos)
    while pos < len(tokens) and tokens[pos].type == TokenType.OR:
        pos += 1  # consume OR
        right, pos = _parse_and(tokens, pos)
        left = OrNode(left, right)
    return left, pos


def _parse_and(tokens, pos):
    """and_expr := not_expr (AND not_expr)*"""
    left, pos = _parse_not(tokens, pos)
    while pos < len(tokens) and tokens[pos].type == TokenType.AND:
        pos += 1  # consume AND
        right, pos = _parse_not(tokens, pos)
        left = AndNode(left, right)
    return left, pos


def _parse_not(tokens, pos):
    """not_expr := NOT not_expr | primary"""
    if pos < len(tokens) and tokens[pos].type == TokenType.NOT:
        pos += 1  # consume NOT
        child, pos = _parse_not(tokens, pos)
        return NotNode(child), pos
    return _parse_primary(tokens, pos)


def _parse_primary(tokens, pos):
    """primary := LPAREN expression RPAREN | TERM"""
    if pos >= len(tokens):
        raise ValueError("Unexpected end of expression.")

    tok = tokens[pos]

    if tok.type == TokenType.LPAREN:
        pos += 1  # consume (
        node, pos = _parse_or(tokens, pos)
        if pos >= len(tokens) or tokens[pos].type != TokenType.RPAREN:
            raise ValueError("Missing closing parenthesis.")
        pos += 1  # consume )
        # Check for adjacent term without operator
        if pos < len(tokens) and tokens[pos].type == TokenType.TERM:
            raise ValueError(
                f"Missing operator before '{tokens[pos].value}'. "
                "Use AND or OR between terms."
            )
        return node, pos

    if tok.type == TokenType.TERM:
        pos += 1
        # Check for adjacent term without operator
        if pos < len(tokens) and tokens[pos].type == TokenType.TERM:
            raise ValueError(
                f"Missing operator between '{tok.value}' and '{tokens[pos].value}'. "
                "Use AND or OR between terms."
            )
        # Check for adjacent ( without operator
        if pos < len(tokens) and tokens[pos].type == TokenType.LPAREN:
            raise ValueError(
                f"Missing operator after '{tok.value}'. "
                "Use AND or OR before '('."
            )
        return TermNode(tok.value), pos

    if tok.type == TokenType.RPAREN:
        raise ValueError("Unexpected closing parenthesis.")

    if tok.type in (TokenType.AND, TokenType.OR):
        raise ValueError(f"Unexpected operator '{tok.value}' without left operand.")

    raise ValueError(f"Unexpected token '{tok.value}'.")


# ─── AST Evaluator ───────────────────────────────────────


def evaluate_expression(ast, text, match_func):
    """Evaluate an AST against a text string.

    Args:
        ast: The parsed expression tree.
        text: The text to match against.
        match_func: Callable(term, text) -> bool. Determines if a single
                    term matches the text.

    Returns:
        True if the expression matches the text.
    """
    if isinstance(ast, TermNode):
        return match_func(ast.value, text)
    elif isinstance(ast, AndNode):
        return (evaluate_expression(ast.left, text, match_func)
                and evaluate_expression(ast.right, text, match_func))
    elif isinstance(ast, OrNode):
        return (evaluate_expression(ast.left, text, match_func)
                or evaluate_expression(ast.right, text, match_func))
    elif isinstance(ast, NotNode):
        return not evaluate_expression(ast.child, text, match_func)
    else:
        raise TypeError(f"Unknown AST node type: {type(ast)}")


# ─── Term Extraction ─────────────────────────────────────


def extract_terms(ast):
    """Extract all unique term values from an AST, in order of appearance."""
    seen = set()
    result = []

    def _walk(node):
        if isinstance(node, TermNode):
            if node.value not in seen:
                seen.add(node.value)
                result.append(node.value)
        elif isinstance(node, NotNode):
            _walk(node.child)
        else:  # AndNode, OrNode
            _walk(node.left)
            _walk(node.right)

    _walk(ast)
    return result


def extract_positive_terms(ast):
    """Extract term values from non-negated positions (for highlighting).

    Terms inside NOT subtrees are excluded.
    """
    seen = set()
    result = []

    def _walk(node, negated=False):
        if isinstance(node, TermNode):
            if not negated and node.value not in seen:
                seen.add(node.value)
                result.append(node.value)
        elif isinstance(node, NotNode):
            _walk(node.child, negated=True)
        else:  # AndNode, OrNode
            _walk(node.left, negated)
            _walk(node.right, negated)

    _walk(ast)
    return result
