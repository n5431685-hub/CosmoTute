"""
Bayesian Knowledge Tracing (BKT) Engine
========================================
Implements the 4-parameter HMM forward-pass for real-time per-answer
mastery updates. Does NOT run EM (that's pyBKT's job for batch param
estimation). This module is pure-Python + numpy so it executes in
microseconds per answer.

Parameters per skill:
  p_l0  : P(L0)  – initial mastery probability
  p_t   : P(T)   – probability of learning (0→1 transition) after an opportunity
  p_s   : P(S)   – slip  (mastered student answers wrong)
  p_g   : P(G)   – guess (unmastered student answers correctly)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class BKTParams:
    """BKT parameters for a single skill."""
    p_l0: float  # initial mastery
    p_t: float   # learn rate
    p_s: float   # slip
    p_g: float   # guess

    def __post_init__(self):
        for name, val in [("p_l0", self.p_l0), ("p_t", self.p_t),
                          ("p_s", self.p_s), ("p_g", self.p_g)]:
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"BKT param '{name}' must be in [0, 1], got {val}")
        if self.p_s + self.p_g >= 1.0:
            raise ValueError("P(S) + P(G) must be < 1 to keep the model identifiable.")


@dataclass
class BKTState:
    """Per-student per-skill mutable state."""
    mastery: float            # current P(L_n)
    opportunities: int = 0   # how many times this skill was practiced
    history: List[bool] = field(default_factory=list)  # answer history

    @classmethod
    def from_params(cls, params: BKTParams) -> "BKTState":
        return cls(mastery=params.p_l0)


def bkt_update(state: BKTState, params: BKTParams, correct: bool) -> BKTState:
    """
    Run one BKT forward-pass step.

    Step 1 — Bayes update given observation:
        P(L | correct)   = P(L) * (1 - P(S))
                         / [P(L)*(1-P(S)) + (1-P(L))*P(G)]

        P(L | incorrect) = P(L) * P(S)
                         / [P(L)*P(S) + (1-P(L))*(1-P(G))]

    Step 2 — Apply learning opportunity:
        P(L_{n+1}) = P(L | obs) + (1 - P(L | obs)) * P(T)

    Returns a NEW BKTState (immutable-style update).
    """
    p_l = state.mastery
    p_s = params.p_s
    p_g = params.p_g
    p_t = params.p_t

    # Step 1: posterior given answer
    if correct:
        numerator   = p_l * (1.0 - p_s)
        denominator = numerator + (1.0 - p_l) * p_g
    else:
        numerator   = p_l * p_s
        denominator = numerator + (1.0 - p_l) * (1.0 - p_g)

    # Guard against degenerate denominators
    if denominator < 1e-10:
        p_l_given_obs = p_l
    else:
        p_l_given_obs = numerator / denominator

    # Clamp to valid probability range
    p_l_given_obs = max(0.0, min(1.0, p_l_given_obs))

    # Step 2: learning opportunity
    p_l_next = p_l_given_obs + (1.0 - p_l_given_obs) * p_t
    p_l_next = max(0.0, min(1.0, p_l_next))

    return BKTState(
        mastery=p_l_next,
        opportunities=state.opportunities + 1,
        history=state.history + [correct],
    )


def predicted_correct_probability(state: BKTState, params: BKTParams) -> float:
    """
    Probability the student will answer the NEXT question correctly.
    P(correct) = P(L)*( 1 - P(S) ) + (1 - P(L))*P(G)
    """
    p_l = state.mastery
    return p_l * (1.0 - params.p_s) + (1.0 - p_l) * params.p_g


def mastery_level_label(mastery: float) -> str:
    """Human-readable mastery bracket for UI display."""
    if mastery < 0.40:
        return "at_risk"
    elif mastery < 0.60:
        return "struggling"
    elif mastery < 0.85:
        return "proficient"
    else:
        return "mastered"


def simulate_student(
    params: BKTParams,
    n_trials: int = 50,
    true_mastery: float = 0.5,
) -> Tuple[List[float], List[bool]]:
    """
    Simulate a student with a fixed 'true mastery' for testing/plotting.
    Returns (mastery_trajectory, answer_sequence).
    """
    import random
    state = BKTState.from_params(params)
    mastery_traj = [state.mastery]
    answers = []

    for _ in range(n_trials):
        # Simulate answer: use true_mastery as ground-truth probability
        if random.random() < true_mastery:
            correct = random.random() > params.p_s   # mastered: slip occasionally
        else:
            correct = random.random() < params.p_g   # unmastered: guess occasionally

        answers.append(correct)
        state = bkt_update(state, params, correct)
        mastery_traj.append(state.mastery)

    return mastery_traj, answers
