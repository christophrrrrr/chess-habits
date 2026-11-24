"""The analyses Chess Habits runs. Each one is computed per time control, because the same
behaviour means different things in bullet and in rapid.

Adding an analysis = writing one function that returns FindingDrafts and registering it here.
Which analyses exist, and why, comes from docs/research/shortlist.md.
"""

from app.analysis.after_loss import after_loss
from app.analysis.base import Analysis
from app.analysis.clock import clock_profile
from app.analysis.habits import form, opening_time, premoves, time_of_day, warm_up

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
    Analysis(
        "warm_up",
        "First game of a session",
        "Do you need a warm-up: how do you play in the first game after a break?",
        warm_up,
    ),
    Analysis(
        "time_of_day",
        "Time of day",
        "Are there hours when you play clearly below your level?",
        time_of_day,
    ),
    Analysis(
        "opening_time",
        "Opening time",
        "How much of your clock goes on the opening, and in which openings?",
        opening_time,
    ),
    Analysis(
        "premoves",
        "Premoves",
        "How often do you premove, and does it change when the clock runs low?",
        premoves,
    ),
    Analysis(
        "form",
        "Form over time",
        "How have your rating and your results against expectation moved, month by month?",
        form,
    ),
]
