"""Parser smoke tests for Maybe."""
import pytest

from maybe import parser as P


def test_say():
    stmts = P.parse('say "hello"\n')
    assert stmts == [P.Say("hello")]


def test_if_else():
    src = 'if feels "rain?":\n    say "wet"\nelse:\n    say "dry"\n'
    (stmt,) = P.parse(src)
    assert isinstance(stmt, P.IfFeels)
    assert stmt.question == "rain?"
    assert stmt.then == [P.Say("wet")]
    assert stmt.otherwise == [P.Say("dry")]


def test_while():
    src = 'while feels "more?":\n    say "again"\n'
    (stmt,) = P.parse(src)
    assert isinstance(stmt, P.WhileFeels)
    assert stmt.body == [P.Say("again")]


def test_match_inline_and_block():
    src = (
        'match "pick":\n'
        '    "a" -> say "A"\n'
        '    "b" ->\n'
        '        say "B1"\n'
        '        say "B2"\n'
    )
    (stmt,) = P.parse(src)
    assert isinstance(stmt, P.Match)
    assert stmt.question == "pick"
    assert stmt.branches[0] == ("a", [P.Say("A")])
    assert stmt.branches[1] == ("b", [P.Say("B1"), P.Say("B2")])


def test_match_needs_two_branches():
    with pytest.raises(SyntaxError):
        P.parse('match "pick":\n    "only" -> say "x"\n')


def test_comments_and_blanks():
    src = '# hi\n\nsay "x"  # trailing\n'
    assert P.parse(src) == [P.Say("x")]


def test_bad_syntax():
    with pytest.raises(SyntaxError):
        P.parse('say hello\n')
    with pytest.raises(SyntaxError):
        P.parse('if feels "x":\n')
