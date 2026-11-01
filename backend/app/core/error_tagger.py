"""
Error Tagger
=============
Classifies a wrong answer into one of three error types:

  CONCEPTUAL         - Fundamental misunderstanding of the topic.
                       Triggered when: wrong on easy question (difficulty 1)
                       AND the student's mastery is low (< 0.5).

  CARELESS           - Student knows the concept but made a silly mistake.
                       Triggered when: wrong on hard/medium question
                       AND mastery is high (> 0.70).

  LANGUAGE_CONFUSION - Answer matches a known regional-language interference
                       pattern (e.g., reading 'lakh' as '1000', flipping
                       the direction of an inequality due to Hindi/Telugu
                       phrasing, common rupee-word-problem misreads).
                       This is checked FIRST as it can co-occur with the
                       others, but language confusion is the root cause.

Returns None for correct answers (no error to tag).
"""

from __future__ import annotations
from typing import Optional, List

ERROR_CONCEPTUAL         = "conceptual"
ERROR_CARELESS           = "careless"
ERROR_LANGUAGE_CONFUSION = "language_confusion"

# ---------------------------------------------------------------------------
# Regional language interference patterns (India-focused, Class 6-10 Math)
# These are known wrong-answer "attractors" caused by L1 interference.
# Each entry: (description, keywords_in_question, wrong_answer_keywords)
# ---------------------------------------------------------------------------
LANGUAGE_PATTERNS: List[dict] = [
    {
        "desc": "lakh/crore confusion with thousand/million",
        "question_keywords": ["lakh", "crore", "lac"],
        "wrong_answer_keywords": ["1000", "million", "thousand"],
    },
    {
        "desc": "Percentage written as fraction (Hindi: pratishat)",
        "question_keywords": ["percent", "%", "pratishat"],
        "wrong_answer_keywords": ["/100", "out of hundred"],
    },
    {
        "desc": "Simple interest formula flipped (P*R/T vs P*R*T)",
        "question_keywords": ["simple interest", "S.I", "SI"],
        "wrong_answer_keywords": ["divided by time", "÷ years"],
    },
    {
        "desc": "Inequality direction flip (greater/less confusion in translation)",
        "question_keywords": ["greater than", "less than", "at least", "at most"],
        "wrong_answer_keywords": ["<", ">"],
    },
    {
        "desc": "Area/Perimeter swap (kshetrafal vs paridhi)",
        "question_keywords": ["perimeter", "boundary", "paridhi"],
        "wrong_answer_keywords": ["square", "squared", "²"],
    },
    {
        "desc": "Cube root confused with cube (teen guna vs teen ghaat)",
        "question_keywords": ["cube root", "∛"],
        "wrong_answer_keywords": ["×3", "*3", "triple"],
    },
]


def _check_language_confusion(
    question_text: str,
    student_answer: str,
    error_hints: Optional[List[str]] = None,
) -> bool:
    """Return True if the wrong answer looks like a language-confusion error."""
    q_lower = question_text.lower()
    a_lower = student_answer.lower()

    # Check explicit hints from question metadata first
    if error_hints and "language_confusion" in error_hints:
        return True

    # Pattern matching
    for pattern in LANGUAGE_PATTERNS:
        q_match = any(kw in q_lower for kw in pattern["question_keywords"])
        a_match = any(kw in a_lower for kw in pattern["wrong_answer_keywords"])
        if q_match and a_match:
            return True

    return False


def tag_error(
    correct: bool,
    mastery: float,
    difficulty: int,
    question_text: str,
    student_answer: str,
    error_hints: Optional[List[str]] = None,
) -> Optional[str]:
    """
    Classify the error type for a wrong answer.

    Args:
        correct        : True if the student answered correctly
        mastery        : current P(L) BEFORE this answer
        difficulty     : 1 (easy) | 2 (medium) | 3 (hard)
        question_text  : raw question string (for language pattern matching)
        student_answer : what the student submitted
        error_hints    : list of hint tags from question metadata

    Returns:
        One of 'conceptual' | 'careless' | 'language_confusion', or None.
    """
    if correct:
        return None

    # Language confusion is checked first — it overrides other categories
    # because the root cause is linguistic, not purely cognitive.
    if _check_language_confusion(question_text, student_answer, error_hints):
        return ERROR_LANGUAGE_CONFUSION

    # Careless: student demonstrably knows the material (high mastery)
    # but got it wrong on a non-trivial question.
    if mastery >= 0.70 and difficulty >= 2:
        return ERROR_CARELESS

    # Also tag as careless if mastery is decent but slipped on easy question
    if mastery >= 0.85 and difficulty == 1:
        return ERROR_CARELESS

    # Conceptual: low mastery, got easy question wrong → fundamental gap
    if mastery < 0.50 and difficulty == 1:
        return ERROR_CONCEPTUAL

    # Default for medium mastery range: still treat as conceptual
    # (student is still forming understanding)
    return ERROR_CONCEPTUAL


def error_summary(error_log: List[str]) -> dict:
    """
    Aggregate a list of error type strings into a summary dict.
    Useful for the teacher dashboard.
    """
    total = len(error_log)
    if total == 0:
        return {
            "total_errors": 0,
            "conceptual": 0,
            "careless": 0,
            "language_confusion": 0,
            "conceptual_pct": 0.0,
            "careless_pct": 0.0,
            "language_confusion_pct": 0.0,
        }

    c  = error_log.count(ERROR_CONCEPTUAL)
    ca = error_log.count(ERROR_CARELESS)
    lc = error_log.count(ERROR_LANGUAGE_CONFUSION)

    return {
        "total_errors": total,
        "conceptual": c,
        "careless": ca,
        "language_confusion": lc,
        "conceptual_pct": round(c / total * 100, 1),
        "careless_pct": round(ca / total * 100, 1),
        "language_confusion_pct": round(lc / total * 100, 1),
    }
