from .match import _flag


def _team_flag(name: str) -> str:
    return _flag(name)


def format_group(group_data: dict) -> str:
    """Format a single group table. Works with both API-Football and worldcup26 shapes."""
    name = group_data.get("name", group_data.get("group", "?"))
    standings = group_data.get("standings", group_data.get("teams", []))

    # API-Football returns standings as list of lists (each group is [[...]])
    if standings and isinstance(standings[0], list):
        standings = standings[0]

    lines = [f"<b>Grupo {name}</b>"]
    lines.append(f"{'#'} {'País':<20} {'PJ':>3} {'G':>3} {'E':>3} {'P':>3} {'GF':>3} {'GC':>3} {'GD':>3} {'Pts':>4}")

    for i, row in enumerate(standings, 1):
        # Normalize across API shapes
        team = row.get("team", {})
        if isinstance(team, dict):
            team_name = team.get("name", "?")
        else:
            team_name = str(team)
        # worldcup26 enriched format: "name" key directly on row
        if team_name == "?":
            team_name = row.get("name", "?")

        all_data = row.get("all", row)
        played = all_data.get("played", row.get("games_played", row.get("mp", row.get("played", "?"))))
        win    = all_data.get("win",    row.get("wins", row.get("w", row.get("won", "?"))))
        draw   = all_data.get("draw",   row.get("draws", row.get("d", row.get("drawn", "?"))))
        lose   = all_data.get("lose",   row.get("losses", row.get("l", row.get("lost", "?"))))
        gf     = all_data.get("goals", {}).get("for",     row.get("goals_for", row.get("gf", "?")))
        gc     = all_data.get("goals", {}).get("against", row.get("goals_against", row.get("ga", "?")))
        gd     = row.get("goalsDiff",  row.get("goal_difference", row.get("gd", "?")))
        pts    = row.get("points",     row.get("pts", "?"))
        flag   = _team_flag(team_name)
        display = f"{flag}{team_name}"[:22]
        lines.append(
            f"{i} {display:<22} {str(played):>3} {str(win):>3} {str(draw):>3} {str(lose):>3} "
            f"{str(gf):>3} {str(gc):>3} {str(gd):>3} {str(pts):>4}"
        )
    return "\n".join(lines)


def format_all_groups(data: list) -> tuple[str, str]:
    """Return two HTML messages: groups A-F and G-L (to stay under 4096 chars)."""
    groups = []
    for item in data:
        # API-Football nests groups under league.standings
        if "league" in item:
            for grp in item["league"]["standings"]:
                groups.append({"name": item["league"].get("name", ""), "standings": [grp]})
        else:
            groups.append(item)

    half = len(groups) // 2 or len(groups)
    first_half = groups[:half]
    second_half = groups[half:]

    msg1 = "<b>⚽ Posiciones — Grupos A–F</b>\n\n" + "\n\n".join(format_group(g) for g in first_half)
    msg2 = "<b>⚽ Posiciones — Grupos G–L</b>\n\n" + "\n\n".join(format_group(g) for g in second_half)
    return msg1, msg2
