"""Tournament engine: group stage + single-elimination knockout bracket.

A single call to :func:`simulate_tournament` plays one full World Cup:

  * 12 groups of 4, round-robin, FIFA ranking (points -> goal diff -> goals
    scored, with Elo as a deterministic final tiebreak),
  * the 12 winners, 12 runners-up and 8 best third-placed teams seeded into a
    standard 32-team bracket,
  * single elimination through the Final.

The hot path (used by the Monte Carlo loop) deliberately avoids Pydantic and
builds only plain Python structures for speed. Goal scores are sampled from a
Poisson model whose supremacy scales with the *weighted* Elo gap, so the
"Elo Influence" slider flows all the way down to individual scorelines:
weight 0 -> symmetric goals (≈uniform outcomes), weight 1 -> Elo-dominated.

Knockout ties are resolved by a shootout drawn from the logistic win
probability, keeping the standard Elo formula at the heart of advancement.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from random import Random

from .models import KNOCKOUT_ORDER, Stage
from .probability import normalize_weight, weighted_win_probability

# Goal model tuning.
BASE_GOALS_PER_TEAM = 1.3   # expected goals each in a perfectly even match
ELO_PER_GOAL = 200.0        # Elo points equivalent to one goal of supremacy
MIN_LAMBDA = 0.15           # floor so even big underdogs can score

# Round-robin pairings for a 4-team group (indices into the group list).
_GROUP_PAIRS = [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]


@dataclass(slots=True)
class RTeam:
    """Lightweight runtime team used inside the simulation hot loop."""

    id: str
    name: str
    group: str
    elo: int
    flag: str


@dataclass(slots=True)
class Standing:
    """Mutable per-group accumulator for one team in one run."""

    team: RTeam
    points: int = 0
    gf: int = 0
    ga: int = 0

    @property
    def gd(self) -> int:
        return self.gf - self.ga


def _poisson(lam: float, rng: Random) -> int:
    """Sample from a Poisson distribution (Knuth's algorithm).

    Fast for the small means used here (lambda ~0.3-2.5 -> a couple of
    iterations on average).
    """
    if lam <= 0:
        return 0
    el = math.exp(-lam)
    k = 0
    p = 1.0
    while True:
        p *= rng.random()
        if p <= el:
            return k
        k += 1


def simulate_score(
    home: RTeam, away: RTeam, weight: float, rng: Random
) -> tuple[int, int]:
    """Sample a group-stage scoreline from the weighted Elo gap."""
    supremacy = weight * (home.elo - away.elo) / ELO_PER_GOAL
    lam_home = max(MIN_LAMBDA, BASE_GOALS_PER_TEAM + supremacy / 2.0)
    lam_away = max(MIN_LAMBDA, BASE_GOALS_PER_TEAM - supremacy / 2.0)
    return _poisson(lam_home, rng), _poisson(lam_away, rng)


def knockout_winner(
    home: RTeam, away: RTeam, weight: float, rng: Random
) -> RTeam:
    """Return the team that advances from a knockout match.

    Uses the logistic win probability (scaled by ``weight``); there are no draws
    in knockouts, so this single draw decides regulation + extra time + pens.
    """
    p_home = weighted_win_probability(home.elo, away.elo, weight)
    return home if rng.random() < p_home else away


def _rank_key(s: Standing) -> tuple[int, int, int, int]:
    """Sort key implementing FIFA group ranking (higher is better).

    points -> goal difference -> goals scored -> Elo (deterministic tiebreak in
    place of the deeper head-to-head / drawing-of-lots rules).
    """
    return (s.points, s.gd, s.gf, s.team.elo)


def simulate_group(
    group_teams: list[RTeam], weight: float, rng: Random
) -> list[Standing]:
    """Play a 4-team round-robin and return standings best-to-worst."""
    standings = {t.id: Standing(team=t) for t in group_teams}
    for i, j in _GROUP_PAIRS:
        home, away = group_teams[i], group_teams[j]
        hg, ag = simulate_score(home, away, weight, rng)
        sh, sa = standings[home.id], standings[away.id]
        sh.gf += hg
        sh.ga += ag
        sa.gf += ag
        sa.ga += hg
        if hg > ag:
            sh.points += 3
        elif ag > hg:
            sa.points += 3
        else:
            sh.points += 1
            sa.points += 1
    return sorted(standings.values(), key=_rank_key, reverse=True)


def _deterministic_group(group_teams: list[RTeam]) -> list[Standing]:
    """Chalk standings: rank purely by Elo (used for the display bracket)."""
    ordered = sorted(group_teams, key=lambda t: t.elo, reverse=True)
    # Synthesize plausible points so downstream third-place ranking still works.
    return [
        Standing(team=t, points=(len(ordered) - idx) * 3, gf=len(ordered) - idx, ga=0)
        for idx, t in enumerate(ordered)
    ]


def _seed_bracket_order(n: int) -> list[int]:
    """Standard single-elimination seed order for a bracket of size ``n``.

    Produces the classic balanced ordering (1, n, n/2, ...) so that the top two
    seeds can only meet in the final. ``n`` must be a power of two.
    """
    order = [1]
    while len(order) < n:
        m = len(order) * 2
        nxt: list[int] = []
        for x in order:
            nxt.append(x)
            nxt.append(m + 1 - x)
        order = nxt
    return order


@dataclass(slots=True)
class TournamentOutcome:
    """Result of one full tournament simulation."""

    champion: RTeam
    # team id -> furthest Stage reached this run.
    furthest_stage: dict[str, Stage]
    # Present only when ``record_bracket`` is requested.
    bracket_rounds: dict[str, list[dict]] | None = None


def _qualifiers(
    groups: dict[str, list[RTeam]], weight: float, rng: Random, deterministic: bool
) -> tuple[list[RTeam], dict[str, Stage]]:
    """Run all groups and return 32 seeded qualifiers + group-stage stages.

    Seeding order: the 12 group winners (ranked among themselves), then the 12
    runners-up, then the 8 best third-placed teams. Within each tier teams are
    ordered by the same FIFA criteria, giving seeds 1..32.
    """
    furthest: dict[str, Stage] = {}
    winners: list[Standing] = []
    runners: list[Standing] = []
    thirds: list[Standing] = []

    for group_letter in sorted(groups.keys()):
        gteams = groups[group_letter]
        standings = (
            _deterministic_group(gteams)
            if deterministic
            else simulate_group(gteams, weight, rng)
        )
        winners.append(standings[0])
        runners.append(standings[1])
        thirds.append(standings[2])
        for s in standings:
            furthest[s.team.id] = Stage.GROUP

    # Best 8 of the 12 third-placed teams advance.
    thirds.sort(key=_rank_key, reverse=True)
    qualifying_thirds = thirds[:8]

    winners.sort(key=_rank_key, reverse=True)
    runners.sort(key=_rank_key, reverse=True)

    seeded = [s.team for s in winners] + [s.team for s in runners] + [
        s.team for s in qualifying_thirds
    ]
    # Everyone in the knockout reached at least the Round of 32.
    for team in seeded:
        furthest[team.id] = Stage.ROUND_OF_32
    return seeded, furthest


def simulate_tournament(
    groups: dict[str, list[RTeam]],
    weight: float,
    rng: Random,
    deterministic: bool = False,
    record_bracket: bool = False,
) -> TournamentOutcome:
    """Simulate one complete tournament and return its outcome.

    Args:
        groups: {group_letter: [4 RTeam]}.
        weight: Elo influence in [0, 1].
        rng: random source.
        deterministic: if True, outcomes follow Elo chalk (no randomness),
            used to build the stable display bracket.
        record_bracket: if True, capture the full round-by-round bracket.
    """
    seeded, furthest = _qualifiers(groups, weight, rng, deterministic)

    seed_order = _seed_bracket_order(len(seeded))  # 32 positions
    # Build initial slots in bracket order: position p holds seed seed_order[p].
    current: list[RTeam] = [seeded[seed_order[p] - 1] for p in range(len(seeded))]

    knockout_stages = [
        Stage.ROUND_OF_32,
        Stage.ROUND_OF_16,
        Stage.QUARTER,
        Stage.SEMI,
        Stage.FINAL,
    ]

    bracket_rounds: dict[str, list[dict]] | None = {} if record_bracket else None

    for stage in knockout_stages:
        next_round: list[RTeam] = []
        round_matches: list[dict] = []
        for slot in range(0, len(current), 2):
            home, away = current[slot], current[slot + 1]
            if deterministic:
                winner = home if home.elo >= away.elo else away
            else:
                winner = knockout_winner(home, away, weight, rng)
            next_round.append(winner)

            # The winner advances to the next stage (or becomes champion).
            advanced_stage = (
                _next_stage(stage) if stage != Stage.FINAL else Stage.WINNER
            )
            furthest[winner.id] = advanced_stage

            if record_bracket:
                round_matches.append(
                    {
                        "stage": stage.value,
                        "slot": slot // 2,
                        "home": home,
                        "away": away,
                        "winner_id": winner.id,
                        "home_win_probability": weighted_win_probability(
                            home.elo, away.elo, weight
                        ),
                    }
                )
        if bracket_rounds is not None:
            bracket_rounds[stage.value] = round_matches
        current = next_round

    champion = current[0]
    return TournamentOutcome(
        champion=champion,
        furthest_stage=furthest,
        bracket_rounds=bracket_rounds,
    )


def _next_stage(stage: Stage) -> Stage:
    """Return the stage a team reaches by *winning* a match at ``stage``."""
    idx = KNOCKOUT_ORDER.index(stage)
    return KNOCKOUT_ORDER[idx + 1]


def to_runtime(teams) -> list[RTeam]:
    """Convert Pydantic Team models into runtime RTeam structs."""
    return [
        RTeam(id=t.id, name=t.name, group=t.group, elo=t.elo_rating, flag=t.flag)
        for t in teams
    ]


def runtime_groups(teams) -> dict[str, list[RTeam]]:
    """Build {group_letter: [RTeam]} from a flat Pydantic team list."""
    rteams = to_runtime(teams)
    groups: dict[str, list[RTeam]] = {}
    for rt in rteams:
        groups.setdefault(rt.group, []).append(rt)
    return groups


def weight_from_slider(slider_value: float) -> float:
    """Public helper mirroring probability.normalize_weight for callers."""
    return normalize_weight(slider_value)
