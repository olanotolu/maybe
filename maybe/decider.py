"""The decision engine inside Maybe: jevbetter, a one-pass option scorer.

Every `feels`, `if`, `while`, and `match` in a Maybe program becomes one
forward pass: context in, one probability per option, no decoding.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "workspace" / "jevbetter"))

import torch

from jevbetter.data import ChoiceExample
from jevbetter.model import load_checkpoint, select_device
from jevbetter.train import move


class Decider:
    """Scores options with jevbetter. `feels` is just decide(ctx, [yes, no])."""

    def __init__(self, checkpoint: str | Path, device: str = "cpu") -> None:
        self.device = select_device(device)
        self.model, self.collator, _, self.temperature = load_checkpoint(
            checkpoint, self.device
        )
        self.model.eval()

    def decide(self, context: str, options: list[str]):
        """Return (best_index, probabilities)."""
        batch = move(
            self.collator([ChoiceExample(context, tuple(options), 0)]),
            self.device,
        )
        with torch.no_grad():
            logits = self.model(batch) / self.temperature
            probs = logits.softmax(-1)[0, : len(options)].cpu().tolist()
        best = max(range(len(options)), key=lambda i: probs[i])
        return best, probs

    def feels(self, context: str, question: str):
        """Ask a yes/no question. Returns (answer, p_yes)."""
        best, probs = self.decide(f"{context}\n{question}", ["yes", "no"])
        return best == 0, probs[0]
