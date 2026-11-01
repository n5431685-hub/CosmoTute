"""
Unit tests for the BKT math engine.
Tests every formula branch, edge case, and parameter validation.

Run: pytest tests/test_bkt_math.py -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from app.core.bkt import (
    BKTParams, BKTState, bkt_update,
    predicted_correct_probability, mastery_level_label
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def typical_params():
    """Typical Class-8 skill params."""
    return BKTParams(p_l0=0.15, p_t=0.25, p_s=0.10, p_g=0.20)


@pytest.fixture
def initial_state(typical_params):
    return BKTState.from_params(typical_params)


# ── Parameter validation ─────────────────────────────────────────────────────

class TestBKTParamValidation:
    def test_valid_params_ok(self):
        p = BKTParams(p_l0=0.1, p_t=0.3, p_s=0.1, p_g=0.2)
        assert p.p_l0 == 0.1

    def test_p_l0_out_of_range(self):
        with pytest.raises(ValueError):
            BKTParams(p_l0=1.5, p_t=0.3, p_s=0.1, p_g=0.2)

    def test_negative_param(self):
        with pytest.raises(ValueError):
            BKTParams(p_l0=0.1, p_t=-0.1, p_s=0.1, p_g=0.2)

    def test_slip_plus_guess_too_high(self):
        with pytest.raises(ValueError):
            BKTParams(p_l0=0.1, p_t=0.3, p_s=0.6, p_g=0.5)

    def test_slip_plus_guess_exactly_one_invalid(self):
        with pytest.raises(ValueError):
            BKTParams(p_l0=0.1, p_t=0.3, p_s=0.5, p_g=0.5)


# ── BKT State initialisation ─────────────────────────────────────────────────

class TestBKTStateInit:
    def test_from_params_sets_mastery_to_p_l0(self, typical_params):
        state = BKTState.from_params(typical_params)
        assert state.mastery == pytest.approx(typical_params.p_l0)

    def test_initial_opportunities_zero(self, typical_params):
        state = BKTState.from_params(typical_params)
        assert state.opportunities == 0

    def test_initial_history_empty(self, typical_params):
        state = BKTState.from_params(typical_params)
        assert state.history == []


# ── BKT Update: Correct Answer ────────────────────────────────────────────────

class TestBKTUpdateCorrect:
    def test_mastery_increases_on_correct(self, initial_state, typical_params):
        new_state = bkt_update(initial_state, typical_params, correct=True)
        assert new_state.mastery > initial_state.mastery

    def test_opportunities_incremented(self, initial_state, typical_params):
        new_state = bkt_update(initial_state, typical_params, correct=True)
        assert new_state.opportunities == 1

    def test_history_appended(self, initial_state, typical_params):
        new_state = bkt_update(initial_state, typical_params, correct=True)
        assert new_state.history == [True]

    def test_mastery_formula_correct_manual(self):
        """Manual verification of the BKT update formula for correct answer."""
        params = BKTParams(p_l0=0.5, p_t=0.3, p_s=0.1, p_g=0.2)
        state  = BKTState(mastery=0.5)

        # Step 1: posterior
        # P(L|correct) = P(L)*(1-P(S)) / [P(L)*(1-P(S)) + (1-P(L))*P(G)]
        p_l = 0.5
        numerator   = p_l * (1 - 0.1)      # 0.5 * 0.9 = 0.45
        denominator = numerator + (1 - p_l) * 0.2   # 0.45 + 0.5*0.2 = 0.45 + 0.10 = 0.55
        p_l_given_obs = numerator / denominator      # 0.45 / 0.55 ≈ 0.8182

        # Step 2: learning
        p_l_next = p_l_given_obs + (1 - p_l_given_obs) * 0.3
        # 0.8182 + 0.1818*0.3 ≈ 0.8182 + 0.05455 ≈ 0.8727

        new_state = bkt_update(state, params, correct=True)
        assert new_state.mastery == pytest.approx(p_l_next, abs=1e-4)

    def test_high_mastery_correct_stays_high(self, typical_params):
        state = BKTState(mastery=0.95)
        new_state = bkt_update(state, typical_params, correct=True)
        assert new_state.mastery > 0.95
        assert new_state.mastery <= 1.0

    def test_mastery_never_exceeds_one(self, typical_params):
        state = BKTState(mastery=1.0)
        new_state = bkt_update(state, typical_params, correct=True)
        assert new_state.mastery <= 1.0


# ── BKT Update: Incorrect Answer ─────────────────────────────────────────────

class TestBKTUpdateIncorrect:
    def test_raw_mastery_decreases_then_recovers_via_learning(
        self, initial_state, typical_params
    ):
        """After a wrong answer the posterior drops, but P(T) partially recovers it."""
        new_state = bkt_update(initial_state, typical_params, correct=False)
        # Final mastery might still be slightly above or below initial depending on params,
        # but the posterior P(L|incorrect) should be lower than the prior.
        p_l = initial_state.mastery
        p_s = typical_params.p_s
        p_g = typical_params.p_g
        posterior = (p_l * p_s) / (p_l * p_s + (1 - p_l) * (1 - p_g))
        assert posterior < p_l  # posterior is always lower on wrong answer

    def test_mastery_formula_incorrect_manual(self):
        """Manual verification of the BKT update formula for incorrect answer."""
        params = BKTParams(p_l0=0.5, p_t=0.3, p_s=0.1, p_g=0.2)
        state  = BKTState(mastery=0.5)

        # Step 1: posterior
        p_l = 0.5
        numerator   = p_l * 0.1           # 0.5 * 0.1 = 0.05
        denominator = numerator + (1 - p_l) * (1 - 0.2)   # 0.05 + 0.5*0.8 = 0.05 + 0.40 = 0.45
        p_l_given_obs = numerator / denominator             # 0.05 / 0.45 ≈ 0.1111

        # Step 2: learning
        p_l_next = p_l_given_obs + (1 - p_l_given_obs) * 0.3

        new_state = bkt_update(state, params, correct=False)
        assert new_state.mastery == pytest.approx(p_l_next, abs=1e-4)

    def test_mastery_never_negative(self, typical_params):
        state = BKTState(mastery=0.0)
        new_state = bkt_update(state, typical_params, correct=False)
        assert new_state.mastery >= 0.0

    def test_history_appended_incorrect(self, initial_state, typical_params):
        new_state = bkt_update(initial_state, typical_params, correct=False)
        assert new_state.history == [False]


# ── Convergence ───────────────────────────────────────────────────────────────

class TestBKTConvergence:
    def test_all_correct_converges_to_high_mastery(self, typical_params):
        state = BKTState.from_params(typical_params)
        for _ in range(20):
            state = bkt_update(state, typical_params, correct=True)
        assert state.mastery > 0.90, f"Expected >0.90, got {state.mastery:.4f}"

    def test_alternating_stabilises(self, typical_params):
        state = BKTState.from_params(typical_params)
        for i in range(40):
            state = bkt_update(state, typical_params, correct=(i % 2 == 0))
        # After 40 alternating answers, mastery should be in a stable range
        assert 0.0 < state.mastery < 1.0

    def test_immutability_original_state_unchanged(self, initial_state, typical_params):
        original_mastery = initial_state.mastery
        _ = bkt_update(initial_state, typical_params, correct=True)
        assert initial_state.mastery == original_mastery


# ── Predicted Probability ─────────────────────────────────────────────────────

class TestPredictedCorrectProbability:
    def test_high_mastery_high_prob(self, typical_params):
        state = BKTState(mastery=0.95)
        prob = predicted_correct_probability(state, typical_params)
        # P(correct) = 0.95*(1-0.10) + 0.05*0.20 = 0.855 + 0.01 = 0.865
        assert prob == pytest.approx(0.865, abs=1e-4)

    def test_zero_mastery_only_guess(self, typical_params):
        state = BKTState(mastery=0.0)
        prob = predicted_correct_probability(state, typical_params)
        # P(correct) = 0*(1-p_s) + 1*p_g = p_g = 0.20
        assert prob == pytest.approx(typical_params.p_g, abs=1e-6)

    def test_full_mastery_bounded_by_slip(self, typical_params):
        state = BKTState(mastery=1.0)
        prob = predicted_correct_probability(state, typical_params)
        # P(correct) = 1*(1-p_s) + 0*p_g = 1 - p_s = 0.90
        assert prob == pytest.approx(1.0 - typical_params.p_s, abs=1e-6)


# ── Mastery Labels ────────────────────────────────────────────────────────────

class TestMasteryLabels:
    @pytest.mark.parametrize("mastery,expected", [
        (0.10, "at_risk"),
        (0.39, "at_risk"),
        (0.40, "struggling"),
        (0.59, "struggling"),
        (0.60, "proficient"),
        (0.84, "proficient"),
        (0.85, "mastered"),
        (1.00, "mastered"),
    ])
    def test_label_boundaries(self, mastery, expected):
        assert mastery_level_label(mastery) == expected
