"""Aero ships its transcript UI as a manifest-only desktop half (desktop/plugin.js).

Hermes loads directory plugins through Python, so this module satisfies the
loader contract and registers the bundled skill; all rendering stays in the
desktop half.
"""

from pathlib import Path

# 60-char budget: Hermes clips skill descriptions to SKILL_PROMPT_DESC_LIMIT
# (60) in the system prompt's <available_skills> index, so the exact qualified
# load name leads - models that call skill_view('aero') bare get "not found".
_SKILL_DESCRIPTION = "skill_view('aero:aero'): kartu, kuis, tabel, peta, form"


def register(ctx):
    """Register the bundled skill so models learn the ui directive syntax."""
    ctx.register_skill(
        "aero",
        Path(__file__).parent / "skills" / "aero" / "SKILL.md",
        description=_SKILL_DESCRIPTION,
    )
