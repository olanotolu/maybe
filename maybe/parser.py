"""Parser for Maybe: a tiny language where `feels`, `match`, and `while`
are decisions made by a one-pass option scorer (jevbetter)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Say:
    text: str


@dataclass
class IfFeels:
    question: str
    then: list = field(default_factory=list)
    otherwise: list = field(default_factory=list)


@dataclass
class WhileFeels:
    question: str
    body: list = field(default_factory=list)


@dataclass
class Match:
    question: str
    branches: list = field(default_factory=list)  # [(option_text, [stmts])]


_STRING = re.compile(
    r'''(?P<q>"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')'''
)


def _parse_string(text: str, pos: int = 0):
    while pos < len(text) and text[pos] in " \t":
        pos += 1
    match = _STRING.match(text, pos)
    if not match:
        raise SyntaxError(f"expected a quoted string in: {text!r}")
    raw = match.group("q")
    quote = raw[0]
    body = raw[1:-1]
    out = []
    i = 0
    while i < len(body):
        if body[i] == "\\" and i + 1 < len(body):
            nxt = body[i + 1]
            out.append({"n": "\n", "t": "\t", "\\": "\\"}.get(nxt, nxt))
            i += 2
        else:
            out.append(body[i])
            i += 1
    return "".join(out), match.end()


def _strip_comment(line: str) -> str:
    out = []
    i = 0
    quote = None
    while i < len(line):
        ch = line[i]
        if quote:
            out.append(ch)
            if ch == "\\" and i + 1 < len(line):
                out.append(line[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#":
            break
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def _lex_lines(source: str):
    lines = []
    for lineno, raw in enumerate(source.splitlines(), 1):
        if "\t" in raw and raw.strip():
            raise SyntaxError(f"line {lineno}: tabs are not allowed, use spaces")
        code = _strip_comment(raw)
        if not code.strip():
            continue
        indent = len(code) - len(code.lstrip(" "))
        lines.append((indent, code.strip(), lineno))
    return lines


class _Parser:
    def __init__(self, lines):
        self.lines = lines
        self.pos = 0

    def peek(self):
        return self.lines[self.pos] if self.pos < len(self.lines) else None

    def parse_block(self, parent_indent: int):
        stmts = []
        while (line := self.peek()) and line[0] > parent_indent:
            stmts.append(self.parse_stmt(line[0]))
        return stmts

    def expect_block(self, indent: int, what: str):
        nxt = self.peek()
        if nxt is None or nxt[0] <= indent:
            raise SyntaxError(f"line {nxt[2] if nxt else '?'}: expected a block after {what}")
        return self.parse_block(indent)

    def parse_stmt(self, indent: int):
        _, text, lineno = self.lines[self.pos]
        if text.startswith("say ") or text.startswith("say\t"):
            self.pos += 1
            value, end = _parse_string(text, 3)
            if text[end:].strip():
                raise SyntaxError(f"line {lineno}: unexpected text after say string")
            return Say(value)
        if text.startswith("if feels "):
            return self.parse_if(indent)
        if text.startswith("while feels "):
            return self.parse_while(indent)
        if text.startswith("match "):
            return self.parse_match(indent)
        if text.startswith("else:"):
            raise SyntaxError(f"line {lineno}: 'else' without 'if'")
        raise SyntaxError(f"line {lineno}: cannot parse: {text!r}")

    def _feels_question(self, text: str, lineno: int, keyword: str):
        rest = text[len(keyword):]
        question, end = _parse_string(rest)
        if rest[end:].strip() != ":":
            raise SyntaxError(f"line {lineno}: expected ':' after the question")
        return question

    def parse_if(self, indent: int):
        _, text, lineno = self.lines[self.pos]
        question = self._feels_question(text, lineno, "if feels ")
        self.pos += 1
        then = self.expect_block(indent, "'if feels'")
        otherwise = []
        nxt = self.peek()
        if nxt and nxt[0] == indent and nxt[1] == "else:":
            self.pos += 1
            otherwise = self.expect_block(indent, "'else'")
        return IfFeels(question, then, otherwise)

    def parse_while(self, indent: int):
        _, text, lineno = self.lines[self.pos]
        question = self._feels_question(text, lineno, "while feels ")
        self.pos += 1
        body = self.expect_block(indent, "'while feels'")
        return WhileFeels(question, body)

    def parse_match(self, indent: int):
        _, text, lineno = self.lines[self.pos]
        rest = text[len("match "):]
        question, end = _parse_string(rest)
        if rest[end:].strip() != ":":
            raise SyntaxError(f"line {lineno}: expected ':' after the match question")
        self.pos += 1
        branches = []
        while (nxt := self.peek()) and nxt[0] > indent:
            b_indent, b_text, b_lineno = nxt
            option, end = _parse_string(b_text)
            tail = b_text[end:].strip()
            if not tail.startswith("->"):
                raise SyntaxError(
                    f"line {b_lineno}: match branch needs '\"option\" ->'"
                )
            tail = tail[2:].strip()
            self.pos += 1
            if tail:
                # inline single statement, e.g.  "go north" -> say "You walk."
                if not (tail.startswith("say ") or tail.startswith("say\t")):
                    raise SyntaxError(
                        f"line {b_lineno}: inline branch must be a say statement"
                    )
                value, end = _parse_string(tail, 3)
                if tail[end:].strip():
                    raise SyntaxError(f"line {b_lineno}: unexpected text in branch")
                branches.append((option, [Say(value)]))
            else:
                body = self.expect_block(b_indent, "match branch")
                branches.append((option, body))
        if len(branches) < 2:
            raise SyntaxError(f"line {lineno}: match needs at least two branches")
        return Match(question, branches)


def parse(source: str) -> list:
    """Parse Maybe source into a list of statements."""
    lines = _lex_lines(source)
    parser = _Parser(lines)
    stmts = parser.parse_block(-1)
    if parser.pos != len(lines):
        _, text, lineno = lines[parser.pos]
        raise SyntaxError(f"line {lineno}: unexpected dedent near: {text!r}")
    return stmts
