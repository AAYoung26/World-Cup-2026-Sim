"""Hard-coded FIFA World Cup 2026 team and group data.

The 2026 tournament expands to 48 teams arranged in 12 groups (A-L) of 4 teams
each. The top two from every group plus the eight best third-placed teams
(2 x 12 + 8 = 32) advance to a Round of 32 -- a single-elimination bracket that
runs through the Final.

NOTE on the spec: the build brief's "16 groups of 3" wording is inconsistent
with its own "groups A-L" and "top 2 + 8 best thirds = 32" rules. Only 12 groups
of 4 produce exactly 32 knockout qualifiers, which is also the real FIFA 2026
format, so that is what we implement here.

The group draw below matches the official Final Draw held on 5 December 2025
in Washington, D.C. The Elo ratings double as the in-memory fallback dataset
used when the external Elo API is unreachable, so the simulator always has 48
rated teams to work with.
"""
from __future__ import annotations

from .models import Team

# Each tuple: (id, name, elo_rating, group, flag_emoji)
_TEAM_TABLE: list[tuple[str, str, int, str, str]] = [
    # Group A
    ("MEX", "Mexico", 1790, "A", "\U0001F1F2\U0001F1FD"),
    ("KOR", "South Korea", 1790, "A", "\U0001F1F0\U0001F1F7"),
    ("CZE", "Czechia", 1720, "A", "\U0001F1E8\U0001F1FF"),
    ("RSA", "South Africa", 1580, "A", "\U0001F1FF\U0001F1E6"),
    # Group B
    ("CAN", "Canada", 1790, "B", "\U0001F1E8\U0001F1E6"),
    ("SUI", "Switzerland", 1900, "B", "\U0001F1E8\U0001F1ED"),
    ("BIH", "Bosnia and Herzegovina", 1700, "B", "\U0001F1E7\U0001F1E6"),
    ("QAT", "Qatar", 1640, "B", "\U0001F1F6\U0001F1E6"),
    # Group C
    ("BRA", "Brazil", 1991, "C", "\U0001F1E7\U0001F1F7"),
    ("MAR", "Morocco", 1880, "C", "\U0001F1F2\U0001F1E6"),
    ("SCO", "Scotland", 1790, "C",
     "\U0001F3F4\U000E0067\U000E0062\U000E0073\U000E0063\U000E0074\U000E007F"),
    ("HAI", "Haiti", 1540, "C", "\U0001F1ED\U0001F1F9"),
    # Group D
    ("USA", "United States", 1790, "D", "\U0001F1FA\U0001F1F8"),
    ("TUR", "Türkiye", 1830, "D", "\U0001F1F9\U0001F1F7"),
    ("AUS", "Australia", 1730, "D", "\U0001F1E6\U0001F1FA"),
    ("PAR", "Paraguay", 1730, "D", "\U0001F1F5\U0001F1FE"),
    # Group E
    ("GER", "Germany", 1960, "E", "\U0001F1E9\U0001F1EA"),
    ("ECU", "Ecuador", 1840, "E", "\U0001F1EA\U0001F1E8"),
    ("CIV", "Ivory Coast", 1790, "E", "\U0001F1E8\U0001F1EE"),
    ("CUW", "Curaçao", 1600, "E", "\U0001F1E8\U0001F1FC"),
    # Group F
    ("NED", "Netherlands", 1960, "F", "\U0001F1F3\U0001F1F1"),
    ("JPN", "Japan", 1860, "F", "\U0001F1EF\U0001F1F5"),
    ("SWE", "Sweden", 1770, "F", "\U0001F1F8\U0001F1EA"),
    ("TUN", "Tunisia", 1720, "F", "\U0001F1F9\U0001F1F3"),
    # Group G
    ("BEL", "Belgium", 1920, "G", "\U0001F1E7\U0001F1EA"),
    ("IRN", "Iran", 1800, "G", "\U0001F1EE\U0001F1F7"),
    ("EGY", "Egypt", 1740, "G", "\U0001F1EA\U0001F1EC"),
    ("NZL", "New Zealand", 1570, "G", "\U0001F1F3\U0001F1FF"),
    # Group H
    ("ESP", "Spain", 2157, "H", "\U0001F1EA\U0001F1F8"),
    ("URU", "Uruguay", 1930, "H", "\U0001F1FA\U0001F1FE"),
    ("KSA", "Saudi Arabia", 1660, "H", "\U0001F1F8\U0001F1E6"),
    ("CPV", "Cape Verde", 1600, "H", "\U0001F1E8\U0001F1FB"),
    # Group I
    ("FRA", "France", 2063, "I", "\U0001F1EB\U0001F1F7"),
    ("NOR", "Norway", 1880, "I", "\U0001F1F3\U0001F1F4"),
    ("SEN", "Senegal", 1830, "I", "\U0001F1F8\U0001F1F3"),
    ("IRQ", "Iraq", 1650, "I", "\U0001F1EE\U0001F1F6"),
    # Group J
    ("ARG", "Argentina", 2115, "J", "\U0001F1E6\U0001F1F7"),
    ("AUT", "Austria", 1860, "J", "\U0001F1E6\U0001F1F9"),
    ("ALG", "Algeria", 1750, "J", "\U0001F1E9\U0001F1FF"),
    ("JOR", "Jordan", 1590, "J", "\U0001F1EF\U0001F1F4"),
    # Group K
    ("POR", "Portugal", 1989, "K", "\U0001F1F5\U0001F1F9"),
    ("COL", "Colombia", 1982, "K", "\U0001F1E8\U0001F1F4"),
    ("UZB", "Uzbekistan", 1700, "K", "\U0001F1FA\U0001F1FF"),
    ("COD", "DR Congo", 1650, "K", "\U0001F1E8\U0001F1E9"),
    # Group L
    ("ENG", "England", 2024, "L",
     "\U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F"),
    ("CRO", "Croatia", 1880, "L", "\U0001F1ED\U0001F1F7"),
    ("GHA", "Ghana", 1690, "L", "\U0001F1EC\U0001F1ED"),
    ("PAN", "Panama", 1640, "L", "\U0001F1F5\U0001F1E6"),
]

GROUPS: list[str] = list("ABCDEFGHIJKL")  # 12 groups


def default_teams() -> list[Team]:
    """Return the full list of 48 teams with fallback Elo ratings."""
    return [
        Team(id=tid, name=name, elo_rating=elo, group=group, flag=flag)
        for (tid, name, elo, group, flag) in _TEAM_TABLE
    ]


def fallback_elo_map() -> dict[str, int]:
    """Return id -> Elo mapping used as a fallback when the API is unreachable."""
    return {tid: elo for (tid, _name, elo, _group, _flag) in _TEAM_TABLE}


def teams_by_group(teams: list[Team]) -> dict[str, list[Team]]:
    """Group a flat team list into an ordered {group_letter: [teams]} dict."""
    grouped: dict[str, list[Team]] = {g: [] for g in GROUPS}
    for team in teams:
        grouped.setdefault(team.group, []).append(team)
    return grouped
