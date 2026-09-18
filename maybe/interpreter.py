"""Tree-walking interpreter for Maybe.

The program's story (everything `say` has printed so far) becomes the
context for every decision, so choices stay coherent with what happened.
"""

from __future__ import annotations

from . import parser as P


class Interpreter:
    def __init__(self, decider, max_loop: int = 8, echo: bool = True) -> None:
        self.decider = decider
        self.max_loop = max_loop
        self.echo = echo
        self.story: list[str] = []

    # -- context ------------------------------------------------------
    def context(self) -> str:
        return "\n".join(self.story)

    # -- run ----------------------------------------------------------
    def run(self, stmts: list) -> None:
        for stmt in stmts:
            if isinstance(stmt, P.Say):
                self.do_say(stmt)
            elif isinstance(stmt, P.IfFeels):
                self.do_if(stmt)
            elif isinstance(stmt, P.WhileFeels):
                self.do_while(stmt)
            elif isinstance(stmt, P.Match):
                self.do_match(stmt)
            else:  # pragma: no cover
                raise TypeError(f"unknown statement: {stmt!r}")

    def do_say(self, stmt: P.Say) -> None:
        print(stmt.text)
        self.story.append(stmt.text)

    def _ask(self, question: str):
        answer, p_yes = self.decider.feels(self.context(), question)
        if self.echo:
            print(f'  ~ feels "{question}" -> {"yes" if answer else "no"} ({p_yes:.2f})')
        return answer

    def do_if(self, stmt: P.IfFeels) -> None:
        self.run(stmt.then if self._ask(stmt.question) else stmt.otherwise)

    def do_while(self, stmt: P.WhileFeels) -> None:
        for _ in range(self.max_loop):
            if not self._ask(stmt.question):
                return
            self.run(stmt.body)
        if self.echo:
            print(f"  ~ while stopped after {self.max_loop} iterations")

    def do_match(self, stmt: P.Match) -> None:
        options = [option for option, _ in stmt.branches]
        best, probs = self.decider.decide(
            f"{self.context()}\n{stmt.question}", options
        )
        if self.echo:
            detail = ", ".join(f"{o[:28]} {p:.2f}" for o, p in zip(options, probs))
            print(f'  ~ match "{stmt.question}" -> "{options[best][:40]}" [{detail}]')
        self.run(stmt.branches[best][1])
