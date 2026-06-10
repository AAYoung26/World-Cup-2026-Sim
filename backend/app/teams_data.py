"""Hard-coded FIFA World Cup 2026 team and group data.

The 2026 tournament expands to 48 teams arranged in 12 groups (A-L) of 4 teams
each. The top two from every group plus the eight best third-placed teams
(2 x 12 + 8 = 32) advance to a Round of 32 -- a single-elimination bracket that
runs through the Final.

NOTE on the spec: the build brief's "16 groups of 3" wording is inconsistent
with its own "groups A-L" and "top 2 + 8 best thirds = 32" rules. Only 12 groups
of 4 produce exactly 32 knockout qualifiers, which is also the real FIFA 2026
format, so that is what we implement here.

The group draw below is representative of a plausible 2026 draw (hosts USA,
Canada, Mexico seeded into separate groups). The Elo ratings double as the
in-memory fallback dataset used when the external Elo API is unreachable, so the
simulator always has 48 rated teams to work with.
"""
from __future__ import annotations

from .models import Team

# Each tuple: (id, name, elo_rating, group, flag_emoji)
_TEAM_TABLE: list[tuple[str, str, int, str, str]] = [
    # Group A
    ("MEX", "Mexico", 1812, "A", "\U0001F1F2\U0001F1FD"),
    ("CRO", "Croatia", 1915, "A", "\U0001F1ED\U0001F1F7"),
    ("WAL", "Wales", 1788, "A", "\U0001F3F4"),
    ("NOR", "Norway", 1820, "A", "\U0001F1F3\U0001F1F4"),
    # Group B
    ("CAN", "Canada", 1709, "B", "\U0001F1E8\U0001F1E6"),
    ("MAR", "Morocco", 1903, "B", "\U0001F1F2\U0001F1E6"),
    ("SWE", "Sweden", 1801, "B", "\U0001F1F8\U0001F1EA"),
    ("QAT", "Qatar", 1652, "B", "\U0001F1F6\U0001F1E6"),
    # Group C
    ("USA", "United States", 1831, "C", "\U0001F1FA\U0001F1F8"),
    ("JPN", "Japan", 1879, "C", "\U0001F1EF\U0001F1F5"),
    ("SRB", "Serbia", 1808, "C", "\U0001F1F7\U0001F1F8"),
    ("GHA", "Ghana", 1683, "C", "\U0001F1EC\U0001F1ED"),
    # Group D
    ("ARG", "Argentina", 2143, "D", "\U0001F1E6\U0001F1F7"),
    ("IRN", "Iran", 1799, "D", "\U0001F1EE\U0001F1F7"),
    ("AUS", "Australia", 1752, "D", "\U0001F1E6\U0001F1FA"),
    ("JAM", "Jamaica", 1601, "D", "\U0001F1EF\U0001F1F2"),
    # Group E
    ("FRA", "France", 2081, "E", "\U0001F1EB\U0001F1F7"),
    ("SUI", "Switzerland", 1871, "E", "\U0001F1E8\U0001F1ED"),
    ("POL", "Poland", 1819, "E", "\U0001F1F5\U0001F1F1"),
    ("KSA", "Saudi Arabia", 1650, "E", "\U0001F1F8\U0001F1E6"),
    # Group F
    ("ENG", "England", 2012, "F", "\U0001F3F4"),
    ("SEN", "Senegal", 1841, "F", "\U0001F1F8\U0001F1F3"),
    ("TUN", "Tunisia", 1703, "F", "\U0001F1F9\U0001F1F3"),
    ("PAN", "Panama", 1621, "F", "\U0001F1F5\U0001F1E6"),
    # Group G
    ("BRA", "Brazil", 2021, "G", "\U0001F1E7\U0001F1F7"),
    ("COL", "Colombia", 1911, "G", "\U0001F1E8\U0001F1F4"),
    ("EGY", "Egypt", 1702, "G", "\U0001F1EA\U0001F1EC"),
    ("CRC", "Costa Rica", 1654, "G", "\U0001F1E8\U0001F1F7"),
    # Group H
    ("POR", "Portugal", 2003, "H", "\U0001F1F5\U0001F1F9"),
    ("KOR", "South Korea", 1793, "H", "\U0001F1F0\U0001F1F7"),
    ("ALG", "Algeria", 1751, "H", "\U0001F1E9\U0001F1FF"),
    ("UZB", "Uzbekistan", 1622, "H", "\U0001F1FA\U0001F1FF"),
    # Group I
    ("NED", "Netherlands", 2031, "I", "\U0001F1F3\U0001F1F1"),
    ("URU", "Uruguay", 1901, "I", "\U0001F1FA\U0001F1FE"),
    ("NGA", "Nigeria", 1742, "I", "\U0001F1F3\U0001F1EC"),
    ("HON", "Honduras", 1582, "I", "\U0001F1ED\U0001F1F3"),
    # Group J
    ("ESP", "Spain", 2051, "J", "\U0001F1EA\U0001F1F8"),
    ("DEN", "Denmark", 1852, "J", "\U0001F1E9\U0001F1F0"),
    ("PER", "Peru", 1751, "J", "\U0001F1F5\U0001F1EA"),
    ("NZL", "New Zealand", 1503, "J", "\U0001F1F3\U0001F1FF"),
    # Group K
    ("BEL", "Belgium", 1931, "K", "\U0001F1E7\U0001F1EA"),
    ("ECU", "Ecuador", 1833, "K", "\U0001F1EA\U0001F1E8"),
    ("CMR", "Cameroon", 1681, "K", "\U0001F1E8\U0001F1F2"),
    ("PAR", "Paraguay", 1722, "K", "\U0001F1F5\U0001F1FE"),
    # Group L
    ("GER", "Germany", 1962, "L", "\U0001F1E9\U0001F1EA"),
    ("AUT", "Austria", 1831, "L", "\U0001F1E6\U0001F1F9"),
    ("UKR", "Ukraine", 1801, "L", "\U0001F1FA\U0001F1E6"),
    ("CIV", "Ivory Coast", 1711, "L", "\U0001F1E8\U0001F1EE"),
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
