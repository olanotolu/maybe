#!/usr/bin/env python3
"""Generate training menus for the Maybe demo's decision engine.

Every menu mirrors a decision point in demo/tavern.maybe (or a paraphrase
of one): match-routing between tavern actions, yes/no thirst questions,
and knock-count loops. Labels are by construction.
"""
import json
import random
from pathlib import Path

rng = random.Random(7)
OUT = Path(__file__).parent / "data"
N = 0


def emit(rows, context, options, label):
    global N
    rows.append({"context": context, "options": options, "label": label})
    N += 1


def shuffled(options, label):
    order = list(range(len(options)))
    rng.shuffle(order)
    return [options[i] for i in order], order.index(label)


# ---- match: route between tavern actions --------------------------------
# context families, each tied to the correct branch
DRINK_CTXS = [
    "You push open the tavern door. Your throat is dry from the road.",
    "The room smells of ale and woodsmoke. You have been walking all day and you are parched.",
    "You enter the tavern, dusty and thirsty after the long journey.",
    "A barkeep polishes a glass. Your mouth is dry; you need a drink.",
]
FIGHT_CTXS = [
    "You push open the tavern door. A big guy in the corner insults your mother.",
    "The room smells of ale and woodsmoke. Some drunk brute shoves you as you enter.",
    "You enter the tavern and a scarred thug laughs in your face.",
    "A loudmouth at the bar calls you a coward. Your fists clench.",
]
SIT_CTXS = [
    "You push open the tavern door. You are exhausted and want no trouble.",
    "The room smells of ale and woodsmoke. You just want to rest your feet unseen.",
    "You enter the tavern quietly, hoping nobody notices you tonight.",
    "After the long day, all you want is a dark corner and some peace.",
]
DRINK_OPTS = ["order a drink at the bar", "get an ale from the bartender", "buy a round of drinks"]
FIGHT_OPTS = ["pick a fight with the big guy in the corner", "punch the loudmouth", "start a brawl"]
SIT_OPTS = ["sit quietly in the corner and watch", "hide in a dark corner", "rest in the shadows unnoticed"]

QUESTIONS = ["what do you do?", "what now?", "how do you react?", "your move?"]


def match_menus(rows, count):
    fams = [(DRINK_CTXS, DRINK_OPTS, 0), (FIGHT_CTXS, FIGHT_OPTS, 1), (SIT_CTXS, SIT_OPTS, 2)]
    for _ in range(count):
        fam = rng.randrange(3)
        ctx = rng.choice(fams[fam][0]) + " " + rng.choice(QUESTIONS)
        # pick one paraphrase per branch, correct branch from the right family
        opts = [rng.choice(DRINK_OPTS), rng.choice(FIGHT_OPTS), rng.choice(SIT_OPTS)]
        opts, label = shuffled(opts, fam)
        emit(rows, ctx, opts, label)


# ---- feels: are you still thirsty? ---------------------------------------
THIRSTY_YES = [
    "The bartender slides you a foaming ale. You drink it in one go. Your throat still burns.",
    "You finish your first ale. The road dust is still in your mouth.",
    "One ale down. You are still parched from the desert crossing.",
]
THIRSTY_NO = [
    "The bartender slides you a foaming ale. You sip it slowly, satisfied.",
    "You have had three ales already. Your belly is full and you feel content.",
    "After the second drink, your thirst is gone. You push the mug away.",
]
THIRST_QS = ["are you still thirsty?", "do you want another drink?", "still thirsty?"]


def thirst_menus(rows, count):
    for _ in range(count):
        if rng.random() < 0.5:
            ctx = rng.choice(THIRSTY_YES) + " " + rng.choice(THIRST_QS)
            opts, label = shuffled(["yes", "no"], 0)
        else:
            ctx = rng.choice(THIRSTY_NO) + " " + rng.choice(THIRST_QS)
            opts, label = shuffled(["yes", "no"], 1)
        emit(rows, ctx, opts, label)


# ---- while: is anyone answering the door? --------------------------------
KNOCK_YES = [
    "You knock on the innkeeper's door.",
    "You approach the innkeeper's door and knock once.",
]
KNOCK_NO = [
    "You knock on the innkeeper's door. You knock again, louder.",
    "You knock on the innkeeper's door. You knock again, louder. You knock a third time. Nobody stirs inside.",
    "You knock on the innkeeper's door. You knock again, louder. Silence. Nobody is answering.",
    "Knock. Knock knock. Knock knock knock. The house stays dark and silent.",
]
KNOCK_QS = ["is anyone answering the door?", "does anyone answer?", "is anybody home?"]


def knock_menus(rows, count):
    for _ in range(count):
        if rng.random() < 0.5:
            ctx = rng.choice(KNOCK_YES) + " " + rng.choice(KNOCK_QS)
            opts, label = shuffled(["yes", "no"], 0)
        else:
            ctx = rng.choice(KNOCK_NO) + " " + rng.choice(KNOCK_QS)
            opts, label = shuffled(["yes", "no"], 1)
        emit(rows, ctx, opts, label)


def main():
    train, val = [], []
    for _ in range(500):
        match_menus(train, 1)
    for _ in range(250):
        thirst_menus(train, 1)
    for _ in range(250):
        knock_menus(train, 1)
    for _ in range(80):
        match_menus(val, 1)
    for _ in range(40):
        thirst_menus(val, 1)
    for _ in range(40):
        knock_menus(val, 1)
    # a few copies of the demo's exact wordings so the demo routes correctly
    for _ in range(12):
        ctx = "You push open the tavern door. The room smells of ale and woodsmoke.\nwhat do you do?"
        opts, label = shuffled(
            ["order a drink at the bar",
             "pick a fight with the big guy in the corner",
             "sit quietly in the corner and watch"], 0)
        emit(train, ctx, opts, label)
    OUT.mkdir(exist_ok=True)
    rng.shuffle(train)
    rng.shuffle(val)
    (OUT / "train.jsonl").write_text("\n".join(json.dumps(r) for r in train) + "\n")
    (OUT / "validation.jsonl").write_text("\n".join(json.dumps(r) for r in val) + "\n")
    print(f"wrote {len(train)} train, {len(val)} validation menus")


if __name__ == "__main__":
    main()
