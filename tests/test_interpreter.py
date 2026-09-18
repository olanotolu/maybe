"""Interpreter tests for Maybe, using a stub decider (no torch needed)."""

from maybe import parser as P
from maybe.interpreter import Interpreter


class StubDecider:
    """Scripted answers: feels -> bool, decide -> winning option index."""

    def __init__(self, feels_answers=(), match_winners=()):
        self.feels_answers = list(feels_answers)
        self.match_winners = list(match_winners)
        self.questions = []

    def feels(self, context, question):
        self.questions.append(("feels", question, context))
        answer = self.feels_answers.pop(0)
        return answer, 0.9 if answer else 0.1

    def decide(self, context, options):
        self.questions.append(("decide", options, context))
        winner = self.match_winners.pop(0)
        probs = [0.05] * len(options)
        probs[winner] = 0.9
        return winner, probs


def run(src, decider):
    interp = Interpreter(decider, echo=False)
    interp.run(P.parse(src))
    return interp


def test_say_builds_story():
    interp = run('say "hi"\nsay "there"\n', StubDecider())
    assert interp.story == ["hi", "there"]


def test_if_takes_then_branch():
    interp = run('if feels "q?":\n  say "yes-branch"\nelse:\n  say "no-branch"\n',
                 StubDecider(feels_answers=[True]))
    assert interp.story == ["yes-branch"]


def test_if_takes_else_branch():
    interp = run('if feels "q?":\n  say "yes-branch"\nelse:\n  say "no-branch"\n',
                 StubDecider(feels_answers=[False]))
    assert interp.story == ["no-branch"]


def test_while_loops_until_false():
    interp = run('while feels "more?":\n  say "again"\n',
                 StubDecider(feels_answers=[True, True, False]))
    assert interp.story == ["again", "again"]


def test_while_respects_max_loop():
    interp = run('while feels "more?":\n  say "again"\n',
                 StubDecider(feels_answers=[True] * 20))
    interp2 = Interpreter(StubDecider(feels_answers=[True] * 20),
                          echo=False, max_loop=3)
    interp2.run(P.parse('while feels "more?":\n  say "again"\n'))
    assert interp2.story == ["again"] * 3


def test_match_routes_to_winner():
    src = ('match "pick":\n'
           '  "go north" -> say "north"\n'
           '  "go south" -> say "south"\n')
    interp = run(src, StubDecider(match_winners=[1]))
    assert interp.story == ["south"]


def test_context_feeds_decisions():
    decider = StubDecider(feels_answers=[True])
    interp = run('say "it is raining"\nif feels "wet?":\n  say "yes"\n', decider)
    kind, question, context = decider.questions[0]
    assert kind == "feels"
    assert "it is raining" in context
