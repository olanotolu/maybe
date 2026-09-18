"""Maybe: a tiny language where control flow is a decision.

    say "hello"                 print text (becomes decision context)
    if feels "is it raining?":  AI if statement
        ...
    else:
        ...
    while feels "keep going?":  loop until it stops feeling true
        ...
    match "what now?":          route between descriptions
        "go north" -> say "..."
        "go south" ->
            say "..."
            say "..."
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import parser as P
from pathlib import Path

DEFAULT_MODEL = Path.home() / "workspace" / "maybe" / "demo" / "model.pt"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="maybe", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="run a .maybe program")
    run.add_argument("file")
    run.add_argument("--model", default=str(DEFAULT_MODEL))
    run.add_argument("--quiet", action="store_true", help="hide decision traces")
    run.add_argument("--max-loop", type=int, default=8)

    check = sub.add_parser("check", help="parse a .maybe program without running it")
    check.add_argument("file")

    args = ap.parse_args(argv)
    source = Path(args.file).read_text()
    try:
        stmts = P.parse(source)
    except SyntaxError as exc:
        print(f"syntax error: {exc}", file=sys.stderr)
        return 1
    if args.cmd == "check":
        print(f"ok: {len(stmts)} top-level statements")
        return 0
    from .decider import Decider
    from .interpreter import Interpreter

    decider = Decider(args.model)
    Interpreter(decider, max_loop=args.max_loop, echo=not args.quiet).run(stmts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
