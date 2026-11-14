"""The analyses Chess Habits runs. Each one is computed per time control, because the same
behaviour means different things in bullet and in rapid.

Adding an analysis = writing one function that returns FindingDrafts and registering it here.
Which analyses exist, and why, comes from docs/research/shortlist.md.
"""

from app.analysis.after_loss import after_loss
from app.analysis.base import Analysis
from app.analysis.clock import clock_profile

ANALYSES: list[Analysis] = [
    Analysis(
        "clock_profile",
        "Clock profile",
        "When do you run short of time, why, and what does the clock cost you?",
        clock_profile,
    ),
    Analysis(
        "after_loss",
        "After a loss",
        "Does losing change how you play next, and would a stop-loss rule help you?",
        after_loss,
    ),
]
