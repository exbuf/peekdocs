"""Tests for docsearch.expr_parser — tokenizer, parser, evaluator, term extraction."""

import pytest

from docsearch.expr_parser import (
    AndNode,
    NotNode,
    OrNode,
    TermNode,
    Token,
    TokenType,
    evaluate_expression,
    extract_positive_terms,
    extract_terms,
    parse_expression,
    tokenize,
)


# ─── Tokenizer Tests ─────────────────────────────────────


class TestTokenize:
    def test_single_term(self):
        tokens = tokenize("budget")
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.TERM
        assert tokens[0].value == "budget"

    def test_and_expression(self):
        tokens = tokenize("bob AND amy")
        assert len(tokens) == 3
        assert tokens[0] == Token(TokenType.TERM, "bob")
        assert tokens[1] == Token(TokenType.AND, "AND")
        assert tokens[2] == Token(TokenType.TERM, "amy")

    def test_or_expression(self):
        tokens = tokenize("bob OR amy")
        assert tokens[1] == Token(TokenType.OR, "OR")

    def test_not_keyword(self):
        tokens = tokenize("NOT draft")
        assert tokens[0] == Token(TokenType.NOT, "NOT")
        assert tokens[1] == Token(TokenType.TERM, "draft")

    def test_parentheses(self):
        tokens = tokenize("(a OR b)")
        assert len(tokens) == 5
        assert tokens[0].type == TokenType.LPAREN
        assert tokens[4].type == TokenType.RPAREN

    def test_case_insensitive_keywords(self):
        for kw in ("and", "And", "AND", "aNd"):
            tokens = tokenize(f"a {kw} b")
            assert tokens[1].type == TokenType.AND

    def test_quoted_term(self):
        tokens = tokenize('"annual report" AND budget')
        assert len(tokens) == 3
        assert tokens[0] == Token(TokenType.TERM, "annual report")
        assert tokens[1].type == TokenType.AND
        assert tokens[2] == Token(TokenType.TERM, "budget")

    def test_quoted_keyword(self):
        """Quoting a keyword makes it a term."""
        tokens = tokenize('"AND" OR budget')
        assert tokens[0] == Token(TokenType.TERM, "AND")
        assert tokens[1].type == TokenType.OR

    def test_empty_expression(self):
        with pytest.raises(ValueError, match="Empty expression"):
            tokenize("")

    def test_whitespace_only(self):
        with pytest.raises(ValueError, match="Empty expression"):
            tokenize("   ")

    def test_unterminated_quote(self):
        with pytest.raises(ValueError, match="Unterminated quote"):
            tokenize('"hello world')

    def test_complex_expression(self):
        tokens = tokenize('(a AND b) OR (NOT "multi word")')
        types = [t.type for t in tokens]
        assert types == [
            TokenType.LPAREN, TokenType.TERM, TokenType.AND, TokenType.TERM,
            TokenType.RPAREN, TokenType.OR, TokenType.LPAREN, TokenType.NOT,
            TokenType.TERM, TokenType.RPAREN,
        ]
        assert tokens[8].value == "multi word"


# ─── Parser Tests ─────────────────────────────────────────


class TestParseExpression:
    def test_single_term(self):
        ast = parse_expression("budget")
        assert ast == TermNode("budget")

    def test_and(self):
        ast = parse_expression("a AND b")
        assert ast == AndNode(TermNode("a"), TermNode("b"))

    def test_or(self):
        ast = parse_expression("a OR b")
        assert ast == OrNode(TermNode("a"), TermNode("b"))

    def test_not(self):
        ast = parse_expression("NOT a")
        assert ast == NotNode(TermNode("a"))

    def test_precedence_and_over_or(self):
        """a OR b AND c → OR(a, AND(b, c))"""
        ast = parse_expression("a OR b AND c")
        assert isinstance(ast, OrNode)
        assert ast.left == TermNode("a")
        assert isinstance(ast.right, AndNode)
        assert ast.right.left == TermNode("b")
        assert ast.right.right == TermNode("c")

    def test_parentheses_override_precedence(self):
        """(a OR b) AND c → AND(OR(a, b), c)"""
        ast = parse_expression("(a OR b) AND c")
        assert isinstance(ast, AndNode)
        assert isinstance(ast.left, OrNode)
        assert ast.right == TermNode("c")

    def test_complex_grouped(self):
        """(a AND b) OR (c AND d)"""
        ast = parse_expression("(a AND b) OR (c AND d)")
        assert isinstance(ast, OrNode)
        assert ast.left == AndNode(TermNode("a"), TermNode("b"))
        assert ast.right == AndNode(TermNode("c"), TermNode("d"))

    def test_double_not(self):
        ast = parse_expression("NOT NOT a")
        assert ast == NotNode(NotNode(TermNode("a")))

    def test_not_with_and(self):
        """a AND NOT b"""
        ast = parse_expression("a AND NOT b")
        assert isinstance(ast, AndNode)
        assert ast.left == TermNode("a")
        assert ast.right == NotNode(TermNode("b"))

    def test_not_group(self):
        """NOT (a OR b)"""
        ast = parse_expression("NOT (a OR b)")
        assert isinstance(ast, NotNode)
        assert isinstance(ast.child, OrNode)

    def test_chained_or(self):
        """a OR b OR c → OR(OR(a, b), c)"""
        ast = parse_expression("a OR b OR c")
        assert isinstance(ast, OrNode)
        assert isinstance(ast.left, OrNode)
        assert ast.right == TermNode("c")

    def test_chained_and(self):
        """a AND b AND c → AND(AND(a, b), c)"""
        ast = parse_expression("a AND b AND c")
        assert isinstance(ast, AndNode)
        assert isinstance(ast.left, AndNode)
        assert ast.right == TermNode("c")

    def test_quoted_multi_word_term(self):
        ast = parse_expression('"annual report" AND budget')
        assert isinstance(ast, AndNode)
        assert ast.left == TermNode("annual report")
        assert ast.right == TermNode("budget")

    def test_deeply_nested(self):
        """((a AND b) OR (c AND d)) AND NOT e"""
        ast = parse_expression("((a AND b) OR (c AND d)) AND NOT e")
        assert isinstance(ast, AndNode)
        assert isinstance(ast.left, OrNode)
        assert isinstance(ast.right, NotNode)

    # Error cases

    def test_error_adjacent_terms(self):
        with pytest.raises(ValueError, match="Missing operator"):
            parse_expression("a b")

    def test_error_unmatched_open_paren(self):
        with pytest.raises(ValueError, match="Missing closing parenthesis"):
            parse_expression("(a AND b")

    def test_error_unmatched_close_paren(self):
        with pytest.raises(ValueError, match="Unexpected token"):
            parse_expression("a AND b)")

    def test_error_leading_and(self):
        with pytest.raises(ValueError, match="Unexpected operator"):
            parse_expression("AND b")

    def test_error_trailing_and(self):
        with pytest.raises(ValueError, match="Unexpected end"):
            parse_expression("a AND")

    def test_error_leading_or(self):
        with pytest.raises(ValueError, match="Unexpected operator"):
            parse_expression("OR b")

    def test_error_empty_parens(self):
        with pytest.raises(ValueError, match="Unexpected closing parenthesis"):
            parse_expression("()")

    def test_error_term_then_paren_no_operator(self):
        with pytest.raises(ValueError, match="Missing operator"):
            parse_expression("a (b OR c)")

    def test_error_paren_then_term_no_operator(self):
        with pytest.raises(ValueError, match="Missing operator"):
            parse_expression("(a OR b) c")


# ─── Evaluator Tests ─────────────────────────────────────


class TestEvaluateExpression:
    def _literal_match(self, term, text):
        return term.lower() in text.lower()

    def test_term_match(self):
        ast = TermNode("hello")
        assert evaluate_expression(ast, "hello world", self._literal_match)

    def test_term_no_match(self):
        ast = TermNode("goodbye")
        assert not evaluate_expression(ast, "hello world", self._literal_match)

    def test_and_both_present(self):
        ast = AndNode(TermNode("hello"), TermNode("world"))
        assert evaluate_expression(ast, "hello world", self._literal_match)

    def test_and_one_missing(self):
        ast = AndNode(TermNode("hello"), TermNode("goodbye"))
        assert not evaluate_expression(ast, "hello world", self._literal_match)

    def test_or_one_present(self):
        ast = OrNode(TermNode("hello"), TermNode("goodbye"))
        assert evaluate_expression(ast, "hello world", self._literal_match)

    def test_or_none_present(self):
        ast = OrNode(TermNode("foo"), TermNode("bar"))
        assert not evaluate_expression(ast, "hello world", self._literal_match)

    def test_not_absent(self):
        ast = NotNode(TermNode("goodbye"))
        assert evaluate_expression(ast, "hello world", self._literal_match)

    def test_not_present(self):
        ast = NotNode(TermNode("hello"))
        assert not evaluate_expression(ast, "hello world", self._literal_match)

    def test_complex_expression(self):
        """(budget AND revenue) OR (cost AND profit)"""
        ast = OrNode(
            AndNode(TermNode("budget"), TermNode("revenue")),
            AndNode(TermNode("cost"), TermNode("profit")),
        )
        assert evaluate_expression(ast, "The budget and revenue report", self._literal_match)
        assert evaluate_expression(ast, "cost and profit analysis", self._literal_match)
        assert not evaluate_expression(ast, "budget and cost only", self._literal_match)

    def test_and_not(self):
        """budget AND NOT draft"""
        ast = AndNode(TermNode("budget"), NotNode(TermNode("draft")))
        assert evaluate_expression(ast, "budget report final", self._literal_match)
        assert not evaluate_expression(ast, "budget draft report", self._literal_match)

    def test_double_not(self):
        ast = NotNode(NotNode(TermNode("hello")))
        assert evaluate_expression(ast, "hello world", self._literal_match)
        assert not evaluate_expression(ast, "goodbye world", self._literal_match)

    def test_or_groups_with_and(self):
        """(budget OR revenue) AND (cost OR profit)"""
        ast = AndNode(
            OrNode(TermNode("budget"), TermNode("revenue")),
            OrNode(TermNode("cost"), TermNode("profit")),
        )
        assert evaluate_expression(ast, "revenue and cost report", self._literal_match)
        assert evaluate_expression(ast, "budget profit analysis", self._literal_match)
        assert not evaluate_expression(ast, "revenue analysis only", self._literal_match)

    def test_case_insensitive(self):
        ast = TermNode("Hello")
        assert evaluate_expression(ast, "HELLO WORLD", self._literal_match)

    def test_end_to_end_parsed(self):
        """Full pipeline: parse then evaluate."""
        ast = parse_expression("(bob AND amy) OR (fred AND wilma)")
        assert evaluate_expression(ast, "bob met amy at the park", self._literal_match)
        assert evaluate_expression(ast, "fred and wilma were there", self._literal_match)
        assert not evaluate_expression(ast, "bob and fred went home", self._literal_match)


# ─── Term Extraction Tests ───────────────────────────────


class TestExtractTerms:
    def test_single_term(self):
        ast = TermNode("hello")
        assert extract_terms(ast) == ["hello"]

    def test_and_terms(self):
        ast = AndNode(TermNode("a"), TermNode("b"))
        assert extract_terms(ast) == ["a", "b"]

    def test_or_terms(self):
        ast = OrNode(TermNode("a"), TermNode("b"))
        assert extract_terms(ast) == ["a", "b"]

    def test_not_term_included(self):
        """extract_terms includes terms inside NOT."""
        ast = AndNode(TermNode("a"), NotNode(TermNode("b")))
        assert extract_terms(ast) == ["a", "b"]

    def test_duplicates_removed(self):
        ast = OrNode(TermNode("a"), TermNode("a"))
        assert extract_terms(ast) == ["a"]

    def test_complex(self):
        ast = parse_expression("(a AND b) OR (c AND NOT d)")
        assert extract_terms(ast) == ["a", "b", "c", "d"]

    def test_order_preserved(self):
        ast = parse_expression("z OR a AND m")
        assert extract_terms(ast) == ["z", "a", "m"]


class TestExtractPositiveTerms:
    def test_no_negation(self):
        ast = AndNode(TermNode("a"), TermNode("b"))
        assert extract_positive_terms(ast) == ["a", "b"]

    def test_not_excluded(self):
        ast = AndNode(TermNode("a"), NotNode(TermNode("b")))
        assert extract_positive_terms(ast) == ["a"]

    def test_all_negated(self):
        ast = NotNode(OrNode(TermNode("a"), TermNode("b")))
        assert extract_positive_terms(ast) == []

    def test_mixed(self):
        ast = parse_expression("(a AND b) OR NOT (c AND d)")
        terms = extract_positive_terms(ast)
        assert "a" in terms
        assert "b" in terms
        assert "c" not in terms
        assert "d" not in terms
