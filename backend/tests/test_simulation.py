"""Tests for the Monte Carlo aggregation engine."""
import time

from app.simulation import run_simulation
from app.teams_data import default_teams


def test_championship_counts_sum_to_runs():
    teams = default_teams()
    result = run_simulation(teams, weight=1.0, num_runs=500, seed=1)
    total = sum(t.championship_count for t in result.teams)
    assert total == result.runs_completed == 500


def test_stage_count_invariants():
    teams = default_teams()
    runs = 300
    result = run_simulation(teams, weight=1.0, num_runs=runs, seed=2)
    by_stage = {"ROUND_OF_32": 0, "ROUND_OF_16": 0, "QUARTER": 0, "SEMI": 0,
                "FINAL": 0, "WINNER": 0}
    for t in result.teams:
        for stage, count in t.stage_reached_counts.items():
            by_stage[stage] += count
    # Each run: 32 in R32, 16 in R16, 8 in QF, 4 in SF, 2 in final, 1 winner.
    assert by_stage["ROUND_OF_32"] == 32 * runs
    assert by_stage["ROUND_OF_16"] == 16 * runs
    assert by_stage["QUARTER"] == 8 * runs
    assert by_stage["SEMI"] == 4 * runs
    assert by_stage["FINAL"] == 2 * runs
    assert by_stage["WINNER"] == 1 * runs


def test_progress_callback_emits_every_50_runs():
    teams = default_teams()
    calls = []

    def cb(done, total, top5):
        calls.append((done, total, len(top5)))

    run_simulation(teams, weight=1.0, num_runs=1000, progress_callback=cb,
                   progress_every=50, seed=3)
    # Exactly 20 updates for 1000 runs at every-50 cadence.
    assert len(calls) == 20
    assert calls[0][0] == 50
    assert calls[-1] == (1000, 1000, 5)


def test_zero_weight_is_near_uniform():
    teams = default_teams()
    result = run_simulation(teams, weight=0.0, num_runs=2000, seed=5)
    top_prob = max(t.championship_probability for t in result.teams)
    # No single team should dominate when every match is a coin flip.
    assert top_prob < 0.10


def test_full_weight_is_elo_dominated():
    teams = default_teams()
    result = run_simulation(teams, weight=1.0, num_runs=2000, seed=6)
    # Strongest team (Spain) should be the clear favourite.
    top = result.teams[0]
    assert top.team_id == "ESP"
    assert top.championship_probability > 0.15
    # Probabilities are far more concentrated than the uniform case.
    assert top.championship_probability > 0.10


def test_bracket_is_populated():
    teams = default_teams()
    result = run_simulation(teams, weight=1.0, num_runs=100, seed=7)
    assert result.bracket.champion_id is not None
    assert len(result.bracket.rounds["ROUND_OF_32"]) == 16
    assert len(result.bracket.rounds["FINAL"]) == 1
    final = result.bracket.rounds["FINAL"][0]
    assert final.home is not None and final.away is not None
    # Championship probabilities should be attached to bracket teams.
    assert final.home.championship_probability >= 0.0


def test_group_results_are_well_formed():
    teams = default_teams()
    runs = 400
    result = run_simulation(teams, weight=1.0, num_runs=runs, seed=9)
    assert len(result.groups) == 12
    for group in result.groups:
        assert len(group.teams) == 4
        # Ordered best-to-worst by expected finishing position.
        positions = [t.avg_position for t in group.teams]
        assert positions == sorted(positions)
        for t in group.teams:
            assert 1.0 <= t.avg_position <= 4.0
            assert abs(sum(t.finish_probs) - 1.0) < 1e-6
            assert 0.0 <= t.advance_probability <= 1.0
        # In each group exactly one team takes each position every run, so each
        # position column sums to 1.0 across the four teams.
        for col in range(4):
            assert abs(sum(t.finish_probs[col] for t in group.teams) - 1.0) < 1e-6


def test_group_winner_is_usually_the_strongest_at_full_weight():
    teams = default_teams()
    result = run_simulation(teams, weight=1.0, num_runs=500, seed=10)
    # Group J contains Argentina (clearly the strongest); it should be the
    # predicted winner (lowest expected position) at full Elo weight.
    group_j = next(g for g in result.groups if g.group == "J")
    assert group_j.teams[0].team_id == "ARG"
    assert group_j.teams[0].advance_probability > 0.9


def test_1000_runs_under_10_seconds():
    teams = default_teams()
    start = time.perf_counter()
    result = run_simulation(teams, weight=1.0, num_runs=1000, seed=8)
    elapsed = time.perf_counter() - start
    assert result.runs_completed == 1000
    assert elapsed < 10.0, f"1000 runs took {elapsed:.2f}s (limit 10s)"
