"""
Adaptive Question Selector
===========================
Selects the next question for a student based on their current mastery
level for a skill, enforcing difficulty zones and avoiding recently-seen
questions (anti-repetition).

Mastery zones → difficulty:
  < 0.40  → difficulty 1 (easy)   — Learn mode
  0.40-0.70 → difficulty 2 (medium) — Solve mode
  > 0.70  → difficulty 3 (hard)   — Test mode

Student can override mode via explicit mode selection.
"""

from __future__ import annotations
import random
from typing import List, Optional


MASTERY_ZONE_EASY   = 0.40
MASTERY_ZONE_MEDIUM = 0.70

MODE_LEARN = "learn"
MODE_SOLVE = "solve"
MODE_TEST  = "test"


def mastery_to_difficulty(mastery: float) -> int:
    """Map current mastery probability to target difficulty (1/2/3)."""
    if mastery < MASTERY_ZONE_EASY:
        return 1
    elif mastery < MASTERY_ZONE_MEDIUM:
        return 2
    else:
        return 3


def mode_to_difficulty(mode: str) -> int:
    """Map explicit student mode to target difficulty."""
    return {MODE_LEARN: 1, MODE_SOLVE: 2, MODE_TEST: 3}.get(mode, 2)


def select_next_question(
    questions: List[dict],
    mastery: float,
    skill_id: int,
    mode: Optional[str] = None,
    recently_seen_ids: Optional[List[int]] = None,
) -> Optional[dict]:
    """
    Select the best next question for a student.

    Args:
        questions        : full question bank (list of dicts with keys:
                           id, skill_id, difficulty, text, options,
                           correct_answer, error_hints)
        mastery          : current P(L) for this skill
        skill_id         : filter questions to this skill
        mode             : 'learn' | 'solve' | 'test' | None (auto)
        recently_seen_ids: list of question IDs answered in last session

    Returns:
        A single question dict, or None if no suitable question found.
    """
    recently_seen_ids = recently_seen_ids or []

    # Determine target difficulty
    target_difficulty = (
        mode_to_difficulty(mode) if mode
        else mastery_to_difficulty(mastery)
    )

    # Filter: right skill, not recently seen
    pool = [
        q for q in questions
        if q["skill_id"] == skill_id
        and q["id"] not in recently_seen_ids
    ]

    # Primary: exact difficulty match
    exact = [q for q in pool if q["difficulty"] == target_difficulty]
    if exact:
        return random.choice(exact)

    # Fallback 1: adjacent difficulty (±1)
    adjacent = [q for q in pool if abs(q["difficulty"] - target_difficulty) == 1]
    if adjacent:
        return random.choice(adjacent)

    # Fallback 2: any unseen question for this skill
    if pool:
        return random.choice(pool)

    # Fallback 3: include recently seen (reset anti-repeat)
    all_skill_qs = [q for q in questions if q["skill_id"] == skill_id]
    return random.choice(all_skill_qs) if all_skill_qs else None
