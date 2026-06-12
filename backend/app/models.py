"""Pydantic data models for the World Cup 2026 simulator.

These models define the API contract shared between the FastAPI backend and the
React frontend. They intentionally mirror the data-model section of the build
spec (Team, Match, SimulationResult, SimulationProgress).
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Stage(str, Enum):
    """Tournament stages, ordered from earliest to latest."""

    GROUP = "GROUP"
    ROUND_OF_32 = "ROUND_OF_32"
    ROUND_OF_16 = "ROUND_OF_16"
    QUARTER = "QUARTER"
    SEMI = "SEMI"
    FINAL = "FINAL"
    WINNER = "WINNER"


# Knockout stages in advancement order. Reaching stage N implies the team played
# (and won the previous round to get) into that stage. WINNER is the terminal
# label for the champion.
KNOCKOUT_ORDER = [
    Stage.ROUND_OF_32,
    Stage.ROUND_OF_16,
    Stage.QUARTER,
    Stage.SEMI,
    Stage.FINAL,
    Stage.WINNER,
]


class Team(BaseModel):
    """A national team participating in the tournament."""

    id: str = Field(..., description="FIFA country code, e.g. 'BRA'")
    name: str = Field(..., description="Display name, e.g. 'Brazil'")
    elo_rating: int = Field(..., description="Elo rating, roughly 1500-2200")
    group: str = Field(..., description="Group letter 'A'-'L'")
    flag: str = Field("", description="Emoji flag for display (optional)")


class Match(BaseModel):
    """A single match between two teams within a simulation run."""

    home_team_id: str
    away_team_id: str
    stage: Stage
    home_win_probability: float = Field(..., ge=0.0, le=1.0)
    predicted_winner_id: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None


class SimulateRequest(BaseModel):
    """Request body for POST /api/simulate."""

    elo_weight: float = Field(
        100.0,
        ge=0.0,
        le=100.0,
        description="Influence of Elo delta, 0 (uniform) to 100 (full Elo).",
    )
    num_runs: int = Field(
        1000,
        ge=1,
        le=50000,
        description="Number of Monte Carlo simulation runs.",
    )


class SimulateResponse(BaseModel):
    """Response for POST /api/simulate."""

    session_id: str
    ws_url: str
    elo_weight: float
    num_runs: int


class TeamResult(BaseModel):
    """Aggregated outcome for one team across all simulation runs."""

    team_id: str
    name: str
    group: str
    elo_rating: int
    flag: str = ""
    championship_count: int = 0
    championship_probability: float = 0.0
    # Map of Stage value -> number of runs the team reached that stage.
    stage_reached_counts: dict[str, int] = Field(default_factory=dict)


class LeaderboardEntry(BaseModel):
    """One row of the live top-5 leaderboard."""

    id: str
    name: str
    flag: str = ""
    wins: int
    probability: float


class SimulationProgress(BaseModel):
    """Progress message streamed over the WebSocket every N runs."""

    type: str = "progress"
    runs_completed: int
    total_runs: int
    top_5_teams: list[LeaderboardEntry] = Field(default_factory=list)


class BracketTeam(BaseModel):
    """A team slot inside the displayed bracket."""

    id: str
    name: str
    flag: str = ""
    elo_rating: int
    championship_probability: float = 0.0


class BracketMatch(BaseModel):
    """A single matchup in the displayed (representative) bracket."""

    stage: Stage
    slot: int
    home: Optional[BracketTeam] = None
    away: Optional[BracketTeam] = None
    winner_id: Optional[str] = None
    home_win_probability: float = 0.0


class Bracket(BaseModel):
    """The representative knockout bracket shown in the UI.

    Rounds are keyed by Stage value (ROUND_OF_32 ... FINAL) and each holds the
    ordered list of matches for that round.
    """

    rounds: dict[str, list[BracketMatch]] = Field(default_factory=dict)
    champion_id: Optional[str] = None


class GroupTeamResult(BaseModel):
    """A team's aggregated group-stage outcome across all runs."""

    team_id: str
    name: str
    flag: str = ""
    elo_rating: int
    # Expected finishing position (1.0 = always first, 4.0 = always last).
    avg_position: float
    # [P(finish 1st), P(2nd), P(3rd), P(4th)] across all runs.
    finish_probs: list[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    # Probability of reaching the knockout stage (top 2 or best-third).
    advance_probability: float = 0.0


class GroupResult(BaseModel):
    """Predicted standings for one group, ordered best-to-worst."""

    group: str
    teams: list[GroupTeamResult] = Field(default_factory=list)


class SimulationResult(BaseModel):
    """Final payload returned over WebSocket and from GET /api/results."""

    type: str = "complete"
    session_id: str
    elo_weight: float
    num_runs: int
    runs_completed: int
    duration_seconds: float
    teams: list[TeamResult] = Field(default_factory=list)
    groups: list[GroupResult] = Field(default_factory=list)
    bracket: Bracket = Field(default_factory=Bracket)
