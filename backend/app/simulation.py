"""Monte Carlo engine: run many tournaments and aggregate the outcomes.

:func:`run_simulation` plays ``num_runs`` independent tournaments, tallies how
often each team wins and how far each team advances, and (optionally) calls a
``progress_callback`` every ``progress_every`` runs so the WebSocket layer can
stream a live leaderboard. It also builds a single representative "chalk"
bracket for display, colouring each slot by the team's Monte Carlo
championship probability.
"""
from __future__ import annotations

import time
from random import Random
from typing import Callable, Optional

from .models import (
    Bracket,
    BracketMatch,
    BracketTeam,
    LeaderboardEntry,
    SimulationResult,
    Stage,
    TeamResult,
)
from .tournament import (
    RTeam,
    runtime_groups,
    simulate_tournament,
)

# Order of knockout stages tracked in the per-team counters.
_KO_STAGES = [
    Stage.ROUND_OF_32,
    Stage.ROUND_OF_16,
    Stage.QUARTER,
    Stage.SEMI,
    Stage.FINAL,
    Stage.WINNER,
]
_STAGE_TO_INDEX = {stage: i for i, stage in enumerate(_KO_STAGES)}

ProgressCallback = Callable[[int, int, list[LeaderboardEntry]], None]
StopCheck = Callable[[], bool]


def _top_5(
    champ_counts: list[int],
    teams: list[RTeam],
    runs_completed: int,
) -> list[LeaderboardEntry]:
    """Build the current top-5 leaderboard from championship tallies."""
    indexed = sorted(
        range(len(teams)), key=lambda i: champ_counts[i], reverse=True
    )[:5]
    entries: list[LeaderboardEntry] = []
    denom = max(runs_completed, 1)
    for i in indexed:
        entries.append(
            LeaderboardEntry(
                id=teams[i].id,
                name=teams[i].name,
                flag=teams[i].flag,
                wins=champ_counts[i],
                probability=champ_counts[i] / denom,
            )
        )
    return entries


def run_simulation(
    teams,
    weight: float,
    num_runs: int,
    session_id: str = "",
    progress_callback: Optional[ProgressCallback] = None,
    progress_every: int = 50,
    seed: Optional[int] = None,
    should_stop: Optional[StopCheck] = None,
) -> SimulationResult:
    """Run ``num_runs`` tournaments and return aggregated results.

    Args:
        teams: list of Pydantic ``Team`` models (48 teams).
        weight: Elo influence in [0.0, 1.0].
        num_runs: number of Monte Carlo runs.
        session_id: identifier echoed back in the result.
        progress_callback: called as ``(runs_completed, total, top_5)`` roughly
            every ``progress_every`` runs.
        progress_every: emit a progress update every this many runs.
        seed: optional RNG seed for reproducible runs.
        should_stop: optional predicate; if it returns True the loop stops early
            and results reflect the runs completed so far.
    """
    start = time.perf_counter()
    rng = Random(seed)

    groups = runtime_groups(teams)
    flat_teams: list[RTeam] = [t for g in groups.values() for t in g]
    index_of = {t.id: i for i, t in enumerate(flat_teams)}
    n = len(flat_teams)

    champ_counts = [0] * n
    # stage_counts[i] = [reached R32, R16, QF, SEMI, FINAL, WINNER]
    stage_counts = [[0] * len(_KO_STAGES) for _ in range(n)]

    runs_completed = 0
    for run_idx in range(num_runs):
        if should_stop is not None and should_stop():
            break
        outcome = simulate_tournament(groups, weight, rng)
        champ_counts[index_of[outcome.champion.id]] += 1

        for team_id, stage in outcome.furthest_stage.items():
            top = _STAGE_TO_INDEX.get(stage)
            if top is None:
                continue  # GROUP-stage exit: no knockout counters.
            counters = stage_counts[index_of[team_id]]
            for k in range(top + 1):
                counters[k] += 1

        runs_completed += 1
        if progress_callback is not None and runs_completed % progress_every == 0:
            progress_callback(
                runs_completed,
                num_runs,
                _top_5(champ_counts, flat_teams, runs_completed),
            )

    # Always emit a final progress snapshot if we didn't land on a boundary.
    if (
        progress_callback is not None
        and runs_completed > 0
        and runs_completed % progress_every != 0
    ):
        progress_callback(
            runs_completed, num_runs, _top_5(champ_counts, flat_teams, runs_completed)
        )

    duration = time.perf_counter() - start
    denom = max(runs_completed, 1)

    team_results: list[TeamResult] = []
    champ_prob_by_id: dict[str, float] = {}
    for i, rt in enumerate(flat_teams):
        prob = champ_counts[i] / denom
        champ_prob_by_id[rt.id] = prob
        stage_dict = {
            _KO_STAGES[k].value: stage_counts[i][k] for k in range(len(_KO_STAGES))
        }
        team_results.append(
            TeamResult(
                team_id=rt.id,
                name=rt.name,
                group=rt.group,
                elo_rating=rt.elo,
                flag=rt.flag,
                championship_count=champ_counts[i],
                championship_probability=prob,
                stage_reached_counts=stage_dict,
            )
        )

    team_results.sort(key=lambda t: t.championship_count, reverse=True)
    bracket = _build_display_bracket(groups, weight, champ_prob_by_id)

    return SimulationResult(
        session_id=session_id,
        elo_weight=weight * 100.0,
        num_runs=num_runs,
        runs_completed=runs_completed,
        duration_seconds=round(duration, 3),
        teams=team_results,
        bracket=bracket,
    )


def _build_display_bracket(
    groups: dict[str, list[RTeam]],
    weight: float,
    champ_prob_by_id: dict[str, float],
) -> Bracket:
    """Generate the stable chalk bracket and annotate it with win probabilities."""
    outcome = simulate_tournament(
        groups, weight, Random(0), deterministic=True, record_bracket=True
    )
    rounds: dict[str, list[BracketMatch]] = {}
    assert outcome.bracket_rounds is not None
    for stage_value, matches in outcome.bracket_rounds.items():
        bracket_matches: list[BracketMatch] = []
        for m in matches:
            bracket_matches.append(
                BracketMatch(
                    stage=Stage(stage_value),
                    slot=m["slot"],
                    home=_bracket_team(m["home"], champ_prob_by_id),
                    away=_bracket_team(m["away"], champ_prob_by_id),
                    winner_id=m["winner_id"],
                    home_win_probability=m["home_win_probability"],
                )
            )
        rounds[stage_value] = bracket_matches
    return Bracket(rounds=rounds, champion_id=outcome.champion.id)


def _bracket_team(rt: RTeam, champ_prob_by_id: dict[str, float]) -> BracketTeam:
    return BracketTeam(
        id=rt.id,
        name=rt.name,
        flag=rt.flag,
        elo_rating=rt.elo,
        championship_probability=champ_prob_by_id.get(rt.id, 0.0),
    )
