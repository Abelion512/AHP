"""Aero ships its transcript UI as a manifest-only desktop half (desktop/plugin.js).

Hermes loads directory plugins through Python, so this module satisfies the
loader contract and registers the bundled skill; all rendering stays in the
desktop half.
"""

from pathlib import Path

_SKILL_DESCRIPTION = (
    "Interactive native cards rendered in chat - product cards with images and "
    "source links, quizzes, interviews, comparisons, process flows, charts, "
    "forms, wizards. Use when the user asks for product recommendations, a quiz, "
    "a survey/interview, or any visual interactive card UI."
)


def register(ctx):
    """Register the bundled skill so models learn the ui directive syntax."""
    ctx.register_skill(
        "aero",
        Path(__file__).parent / "skills" / "aero" / "SKILL.md",
        description=_SKILL_DESCRIPTION,
    )
