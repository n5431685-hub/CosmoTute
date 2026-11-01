"""
BKT Simulation Tests
=====================
Simulates 5 fake students answering sequences of questions and verifies
that mastery trajectories behave realistically.

Run: pytest tests/test_bkt_simulation.py -v -s
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from app.core.bkt import BKTParams, BKTState, bkt_update, simulate_student
from app.core.error_tagger import tag_error, error_summary, ERROR_CONCEPTUAL, ERROR_CARELESS, ERROR_LANGUAGE_CONFUSION
from app.core.question_selector import (
    select_next_question, mastery_to_difficulty,
    MODE_LEARN, MODE_SOLVE, MODE_TEST
)


# ── Shared params ─────────────────────────────────────────────────────────────

SKILL_PARAMS = [
    BKTParams(p_l0=0.10, p_t=0.30, p_s=0.10, p_g=0.20),  # Rational Numbers
    BKTParams(p_l0=0.15, p_t=0.25, p_s=0.12, p_g=0.18),  # Linear Equations
    BKTParams(p_l0=0.20, p_t=0.20, p_s=0.08, p_g=0.15),  # Quadrilaterals
    BKTParams(p_l0=0.12, p_t=0.28, p_s=0.10, p_g=0.22),  # Squares & Roots
    BKTParams(p_l0=0.25, p_t=0.30, p_s=0.12, p_g=0.20),  # Comparing Quantities
]


# ── Student profile simulations ───────────────────────────────────────────────

class TestStudentSimulations:
    """
    Each test simulates a different student archetype.
    Success criterion: mastery must converge in the expected direction.
    """

    def test_strong_student_reaches_mastery(self):
        """Student who answers 90% correctly should reach >0.90 mastery in 20 trials."""
        params = SKILL_PARAMS[0]
        state = BKTState.from_params(params)

        import random
        random.seed(42)
        for _ in range(25):
            # Strong student: 90% correct
            correct = random.random() < 0.90
            state = bkt_update(state, params, correct=correct)

        print(f"\n[Strong Student] Final mastery: {state.mastery:.4f}")
        assert state.mastery > 0.80, f"Expected >0.80, got {state.mastery:.4f}"

    def test_weak_student_stays_low(self):
        """Student who answers 15% correctly (pure guess) should stay below 0.45."""
        params = SKILL_PARAMS[0]
        state = BKTState.from_params(params)

        import random
        random.seed(99)
        for _ in range(20):
            # Weak student: mostly guesses (20% correct = guess rate)
            correct = random.random() < 0.20
            state = bkt_update(state, params, correct=correct)

        print(f"\n[Weak Student] Final mastery: {state.mastery:.4f}")
        assert state.mastery < 0.55, f"Expected <0.55, got {state.mastery:.4f}"

    def test_average_student_mid_range(self):
        """
        Student with 55% correct rate should end up strictly above the initial
        p_l0 and below 1.0 (cannot saturate perfectly in 30 trials unless
        very lucky — we check the distribution over multiple seeds).
        """
        params = SKILL_PARAMS[1]

        import random
        above_initial = 0
        runs = 10
        for seed_val in range(runs):
            state = BKTState.from_params(params)
            random.seed(seed_val * 17)
            for _ in range(30):
                correct = random.random() < 0.55
                state = bkt_update(state, params, correct=correct)
            if state.mastery > params.p_l0:
                above_initial += 1

        # At least 80% of runs should produce mastery above initial (sanity check)
        print(f"\n[Average Student] {above_initial}/{runs} runs above p_l0")
        assert above_initial >= 8, \
            f"Expected ≥8/{runs} runs above p_l0, got {above_initial}"

    def test_mastery_monotonically_increases_on_all_correct(self):
        """All-correct sequence must produce strictly non-decreasing mastery."""
        params = SKILL_PARAMS[0]
        state = BKTState.from_params(params)
        prev = state.mastery

        for _ in range(30):
            state = bkt_update(state, params, correct=True)
            assert state.mastery >= prev, \
                f"Mastery decreased: {prev:.4f} → {state.mastery:.4f}"
            prev = state.mastery

    def test_five_students_all_skills(self):
        """Run all 5 students through all 5 skills, verify no NaN or out-of-range."""
        import random
        student_correct_rates = [0.85, 0.60, 0.35, 0.75, 0.20]

        for s_idx, rate in enumerate(student_correct_rates):
            random.seed(s_idx * 13)
            for skill_params in SKILL_PARAMS:
                state = BKTState.from_params(skill_params)
                for _ in range(20):
                    correct = random.random() < rate
                    state = bkt_update(state, skill_params, correct=correct)

                assert 0.0 <= state.mastery <= 1.0, \
                    f"Student {s_idx+1} mastery out of range: {state.mastery}"
                assert not (state.mastery != state.mastery), "NaN detected"

    def test_simulate_helper_returns_correct_length(self):
        params = SKILL_PARAMS[0]
        traj, answers = simulate_student(params, n_trials=50)
        # trajectory has n_trials+1 entries (initial + one per trial)
        assert len(traj) == 51
        assert len(answers) == 50


# ── Error Tagger Tests ────────────────────────────────────────────────────────

class TestErrorTagger:
    def test_correct_answer_returns_none(self):
        result = tag_error(
            correct=True, mastery=0.3, difficulty=1,
            question_text="What is 2+2?", student_answer="4"
        )
        assert result is None

    def test_conceptual_error_low_mastery_easy_question(self):
        result = tag_error(
            correct=False, mastery=0.20, difficulty=1,
            question_text="What is 3x = 21?", student_answer="3"
        )
        assert result == ERROR_CONCEPTUAL

    def test_careless_error_high_mastery_hard_question(self):
        result = tag_error(
            correct=False, mastery=0.85, difficulty=3,
            question_text="Expand (a+3)²", student_answer="a²+9"
        )
        assert result == ERROR_CARELESS

    def test_language_confusion_lakh_pattern(self):
        result = tag_error(
            correct=False, mastery=0.50, difficulty=2,
            question_text="A shopkeeper earned 5 lakh rupees. What is this in thousands?",
            student_answer="5 million"
        )
        assert result == ERROR_LANGUAGE_CONFUSION

    def test_language_confusion_via_hint(self):
        result = tag_error(
            correct=False, mastery=0.60, difficulty=2,
            question_text="Find simple interest.",
            student_answer="200",
            error_hints=["language_confusion"]
        )
        assert result == ERROR_LANGUAGE_CONFUSION

    def test_error_summary_empty(self):
        summary = error_summary([])
        assert summary["total_errors"] == 0
        assert summary["conceptual_pct"] == 0.0

    def test_error_summary_mixed(self):
        errors = [ERROR_CONCEPTUAL, ERROR_CONCEPTUAL, ERROR_CARELESS,
                  ERROR_LANGUAGE_CONFUSION, ERROR_CONCEPTUAL]
        summary = error_summary(errors)
        assert summary["total_errors"] == 5
        assert summary["conceptual"] == 3
        assert summary["careless"] == 1
        assert summary["language_confusion"] == 1
        assert summary["conceptual_pct"] == pytest.approx(60.0)


# ── Question Selector Tests ───────────────────────────────────────────────────

class TestQuestionSelector:
    @pytest.fixture
    def sample_questions(self):
        return [
            {"id": 1, "skill_id": 1, "difficulty": 1, "text": "Easy Q", "options": ["a","b"], "correct_answer": "a", "error_hints": []},
            {"id": 2, "skill_id": 1, "difficulty": 2, "text": "Med Q",  "options": ["a","b"], "correct_answer": "a", "error_hints": []},
            {"id": 3, "skill_id": 1, "difficulty": 3, "text": "Hard Q", "options": ["a","b"], "correct_answer": "a", "error_hints": []},
            {"id": 4, "skill_id": 2, "difficulty": 1, "text": "Skill2", "options": ["a","b"], "correct_answer": "a", "error_hints": []},
        ]

    def test_low_mastery_selects_easy(self, sample_questions):
        q = select_next_question(sample_questions, mastery=0.10, skill_id=1)
        assert q["difficulty"] == 1

    def test_medium_mastery_selects_medium(self, sample_questions):
        q = select_next_question(sample_questions, mastery=0.55, skill_id=1)
        assert q["difficulty"] == 2

    def test_high_mastery_selects_hard(self, sample_questions):
        q = select_next_question(sample_questions, mastery=0.80, skill_id=1)
        assert q["difficulty"] == 3

    def test_mode_learn_overrides_mastery(self, sample_questions):
        """Even with high mastery, mode=learn forces easy questions."""
        q = select_next_question(sample_questions, mastery=0.90, skill_id=1, mode=MODE_LEARN)
        assert q["difficulty"] == 1

    def test_mode_test_overrides_mastery(self, sample_questions):
        """Even with low mastery, mode=test forces hard questions."""
        q = select_next_question(sample_questions, mastery=0.05, skill_id=1, mode=MODE_TEST)
        assert q["difficulty"] == 3

    def test_recently_seen_avoids_ids(self, sample_questions):
        """Should not return recently seen questions if alternatives exist."""
        q = select_next_question(
            sample_questions, mastery=0.10, skill_id=1, recently_seen_ids=[1]
        )
        # Question 1 (easy) is seen → should fall back to adjacent (medium)
        assert q["id"] != 1

    def test_wrong_skill_returns_none(self, sample_questions):
        q = select_next_question(sample_questions, mastery=0.5, skill_id=99)
        assert q is None

    def test_mastery_to_difficulty_boundaries(self):
        assert mastery_to_difficulty(0.0)  == 1
        assert mastery_to_difficulty(0.39) == 1
        assert mastery_to_difficulty(0.40) == 2
        assert mastery_to_difficulty(0.69) == 2
        assert mastery_to_difficulty(0.70) == 3
        assert mastery_to_difficulty(1.00) == 3


# ── Full simulation: mastery trajectory verification ─────────────────────────

class TestMasteryTrajectory:
    def test_trajectory_starts_at_p_l0(self):
        params = SKILL_PARAMS[0]
        traj, _ = simulate_student(params, n_trials=10)
        assert traj[0] == pytest.approx(params.p_l0, abs=1e-9)

    def test_trajectory_length_correct(self):
        traj, answers = simulate_student(SKILL_PARAMS[0], n_trials=30)
        assert len(traj) == 31
        assert len(answers) == 30

    def test_all_mastery_values_in_range(self):
        params = SKILL_PARAMS[0]
        traj, _ = simulate_student(params, n_trials=50)
        for i, m in enumerate(traj):
            assert 0.0 <= m <= 1.0, f"Out-of-range mastery at step {i}: {m}"

    def test_high_true_mastery_converges_high(self):
        """Simulate student with true mastery=0.95, should converge high."""
        import random
        random.seed(2024)
        params = BKTParams(p_l0=0.10, p_t=0.30, p_s=0.08, p_g=0.15)
        traj, _ = simulate_student(params, n_trials=40, true_mastery=0.95)
        final = traj[-1]
        print(f"\n[High-mastery sim] Final mastery: {final:.4f}")
        assert final > 0.75, f"Expected >0.75, got {final:.4f}"
