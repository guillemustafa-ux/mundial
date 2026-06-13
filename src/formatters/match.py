from .timezone import format_time, format_datetime, format_date_short

# Emojis de bandera por nombre de equipo (48 selecciones + alias comunes)
FLAG = {
    "argentina": "🇦🇷", "australia": "🇦🇺", "austria": "🇦🇹",
    "bahrain": "🇧🇭", "belgium": "🇧🇪", "bolivia": "🇧🇴",
    "brazil": "🇧🇷", "brasil": "🇧🇷", "canada": "🇨🇦", "canadá": "🇨🇦",
    "chile": "🇨🇱", "china": "🇨🇳", "colombia": "🇨🇴",
    "costa rica": "🇨🇷", "croatia": "🇭🇷", "croacia": "🇭🇷",
    "denmark": "🇩🇰", "dinamarca": "🇩🇰", "ecuador": "🇪🇨",
    "egypt": "🇪🇬", "egipto": "🇪🇬", "england": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "inglaterra": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "france": "🇫🇷", "francia": "🇫🇷", "germany": "🇩🇪", "alemania": "🇩🇪",
    "ghana": "🇬🇭", "greece": "🇬🇷", "grecia": "🇬🇷",
    "honduras": "🇭🇳", "hungary": "🇭🇺", "hungría": "🇭🇺",
    "indonesia": "🇮🇩", "iran": "🇮🇷", "iraq": "🇮🇶",
    "israel": "🇮🇱", "italy": "🇮🇹", "italia": "🇮🇹",
    "ivory coast": "🇨🇮", "cote d'ivoire": "🇨🇮",
    "japan": "🇯🇵", "japón": "🇯🇵", "jordan": "🇯🇴",
    "korea republic": "🇰🇷", "south korea": "🇰🇷", "corea del sur": "🇰🇷",
    "kuwait": "🇰🇼", "mali": "🇲🇱", "mexico": "🇲🇽", "méxico": "🇲🇽",
    "morocco": "🇲🇦", "marruecos": "🇲🇦", "netherlands": "🇳🇱", "países bajos": "🇳🇱",
    "new zealand": "🇳🇿", "nigeria": "🇳🇬", "norway": "🇳🇴", "noruega": "🇳🇴",
    "panama": "🇵🇦", "panamá": "🇵🇦", "paraguay": "🇵🇾", "peru": "🇵🇪", "perú": "🇵🇪",
    "poland": "🇵🇱", "polonia": "🇵🇱", "portugal": "🇵🇹",
    "qatar": "🇶🇦", "romania": "🇷🇴", "rumania": "🇷🇴",
    "saudi arabia": "🇸🇦", "arabia saudita": "🇸🇦",
    "senegal": "🇸🇳", "serbia": "🇷🇸", "slovakia": "🇸🇰", "eslovaquia": "🇸🇰",
    "slovenia": "🇸🇮", "eslovenia": "🇸🇮", "spain": "🇪🇸", "españa": "🇪🇸",
    "switzerland": "🇨🇭", "suiza": "🇨🇭", "thailand": "🇹🇭", "tailandia": "🇹🇭",
    "togo": "🇹🇬", "trinidad and tobago": "🇹🇹",
    "tunisia": "🇹🇳", "túnez": "🇹🇳", "turkey": "🇹🇷", "turquía": "🇹🇷",
    "ukraine": "🇺🇦", "ucrania": "🇺🇦",
    "united arab emirates": "🇦🇪", "uae": "🇦🇪",
    "united states": "🇺🇸", "usa": "🇺🇸", "estados unidos": "🇺🇸",
    "uruguay": "🇺🇾", "venezuela": "🇻🇪",
    "wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "gales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
}

STATUS_LABELS = {
    "NS": "Por jugar", "1H": "1° tiempo", "HT": "Entretiempo",
    "2H": "2° tiempo", "ET": "Prórroga", "PEN": "Penales",
    "FT": "Final", "AET": "Final (ET)", "PEN_FT": "Final (Pen)",
    "CANC": "Cancelado", "PST": "Postergado", "ABD": "Abandonado",
}


def _flag(team_name: str) -> str:
    return FLAG.get(team_name.lower(), "🏳️")


def _status(s: str) -> str:
    return STATUS_LABELS.get(s, s)


def _wc26_status(fixture: dict) -> str:
    """Map worldcup26 time_elapsed to short status code."""
    te = fixture.get("time_elapsed", "")
    finished = str(fixture.get("finished", "FALSE")).upper()
    if finished == "TRUE" or te == "finished":
        return "FT"
    if te == "notstarted" or not te:
        return "NS"
    # during match worldcup26 may send "1H", "HT", "2H", etc.
    return te.upper() if te else "NS"


def _score_line(fixture: dict) -> str:
    """Works with both API-Football and worldcup26.ir shapes."""
    status = fixture.get("status", fixture.get("fixture", {}).get("status", {}).get("short", ""))
    if isinstance(status, dict):
        status = status.get("short", "")
    if not status:
        status = _wc26_status(fixture)

    # API-Football shape
    if "goals" in fixture:
        h = fixture["goals"].get("home")
        a = fixture["goals"].get("away")
    elif "home_score" in fixture:
        h = fixture.get("home_score")
        a = fixture.get("away_score")
        try:
            h = int(h) if str(h).isdigit() else None
            a = int(a) if str(a).isdigit() else None
        except Exception:
            h = a = None
    else:
        h = a = None

    if status in ("NS", "PST", "CANC") or h is None:
        return "vs"
    return f"{h} - {a}"


def _teams(fixture: dict) -> tuple[str, str]:
    """Return (home, away) team names, normalised across API shapes."""
    if "teams" in fixture:
        return fixture["teams"]["home"]["name"], fixture["teams"]["away"]["name"]
    if "home_team_name_en" in fixture:
        return fixture.get("home_team_name_en", "?"), fixture.get("away_team_name_en", "?")
    return fixture.get("home_team", "?"), fixture.get("away_team", "?")


def _match_time(fixture: dict) -> str:
    date = (
        fixture.get("fixture", {}).get("date")
        or fixture.get("date")
        or fixture.get("datetime")
        or ""
    )
    if date:
        try:
            return format_time(date)
        except Exception:
            return date[:5]
    # worldcup26: "MM/DD/YYYY HH:MM" — return HH:MM as-is (venue local time)
    local_date = fixture.get("local_date", "")
    if local_date:
        parts = local_date.split(" ")
        return parts[1] if len(parts) > 1 else local_date
    return "??:??"


# ── públicos ───────────────────────────────────────────────────────────────

def format_match_line(fixture: dict) -> str:
    home, away = _teams(fixture)
    score = _score_line(fixture)
    time = _match_time(fixture)
    status = fixture.get("status", fixture.get("fixture", {}).get("status", {}).get("short", ""))
    if isinstance(status, dict):
        status = status.get("short", "")
    if not status:
        status = _wc26_status(fixture)
    status_label = _status(status)
    fh, fa = _flag(home), _flag(away)
    return f"{fh} <b>{home}</b>  {score}  <b>{away}</b> {fa}  <i>{time} ({status_label})</i>"


def format_day_list(fixtures: list, date_str: str) -> str:
    if not fixtures:
        return f"No hay partidos programados para el {date_str}."
    lines = [f"⚽ <b>Partidos del {date_str}</b>\n"]
    for f in sorted(fixtures, key=lambda x: x.get("fixture", {}).get("date", x.get("date", ""))):
        lines.append(format_match_line(f))
    return "\n".join(lines)


def format_argentina_summary(next_fixtures: list, last_fixtures: list, group_row: dict | None) -> str:
    lines = ["🇦🇷 <b>ARGENTINA — Mundial 2026</b>\n"]

    if next_fixtures:
        nxt = next_fixtures[0]
        home, away = _teams(nxt)
        date_field = nxt.get("fixture", {}).get("date") or nxt.get("date") or nxt.get("datetime") or ""
        try:
            dt_str = format_datetime(date_field)
        except Exception:
            dt_str = date_field
        opp = away if home.lower() == "argentina" else home
        lines.append(f"📅 <b>Próximo:</b> vs {_flag(opp)} {opp} — {dt_str}")
    else:
        lines.append("📅 Próximo partido: a confirmar")

    if last_fixtures:
        lines.append("\n🕐 <b>Últimos resultados:</b>")
        for f in last_fixtures[-3:]:
            lines.append(f"  {format_match_line(f)}")

    if group_row:
        s = group_row.get("standing", group_row)
        g_name = group_row.get("group", "")
        pts = s.get("points", s.get("pts", "?"))
        gp = s.get("games_played", s.get("played", "?"))
        gd = s.get("goal_difference", s.get("gd", "?"))
        lines.append(f"\n📊 <b>Grupo {g_name}:</b> {pts} pts | {gp} PJ | GD {gd}")

    return "\n".join(lines)


def format_live(fixtures: list) -> str:
    active = [
        f for f in fixtures
        if f.get("fixture", {}).get("status", {}).get("short", f.get("status", "")) in
        ("1H", "HT", "2H", "ET", "PEN")
    ]
    if not active:
        return "🔇 No hay partidos en vivo ahora mismo."
    lines = ["🔴 <b>EN VIVO — Mundial 2026</b>\n"]
    for f in active:
        elapsed = f.get("fixture", {}).get("status", {}).get("elapsed") or ""
        elapsed_str = f" <code>{elapsed}'</code>" if elapsed else ""
        lines.append(format_match_line(f) + elapsed_str)
    return "\n".join(lines)


def format_team_fixtures(fixtures: list, team_name: str) -> str:
    if not fixtures:
        return f"No se encontraron partidos para {team_name}."
    lines = [f"{_flag(team_name)} <b>Fixture — {team_name}</b>\n"]
    for f in sorted(fixtures, key=lambda x: x.get("fixture", {}).get("date", x.get("date", ""))):
        home, away = _teams(f)
        date_field = f.get("fixture", {}).get("date") or f.get("date") or f.get("datetime") or ""
        try:
            date_short = format_date_short(date_field)
            time = format_time(date_field)
        except Exception:
            date_short = date_field[:10]
            time = ""
        score = _score_line(f)
        opp = away if home.lower() == team_name.lower() else home
        loc = "vs" if home.lower() == team_name.lower() else "en"
        lines.append(f"  {date_short} {time} — {loc} {_flag(opp)} {opp}  <b>{score}</b>")
    return "\n".join(lines)


def format_odds(event: dict) -> str:
    ht = event.get("home_team", "?")
    at = event.get("away_team", "?")
    bookmakers = event.get("bookmakers", [])
    if not bookmakers:
        return "Sin cuotas disponibles."

    lines = [f"💰 <b>Cuotas — {_flag(ht)} {ht} vs {_flag(at)} {at}</b>\n"]
    lines.append(f"{'Casa':<20} {'Local':>7}  {'Empate':>7}  {'Visitante':>9}")
    lines.append("─" * 48)

    for bm in bookmakers[:6]:
        name = bm.get("title", bm.get("id", bm.get("key", "?")))[:18]
        # API-Ninjas: bets[].values[] — The Odds API fallback: markets[].outcomes[]
        bets = bm.get("bets", bm.get("markets", []))
        h2h = next(
            (b for b in bets if b.get("id") in ("h2h", "main") or b.get("key") == "h2h"),
            None,
        )
        if not h2h:
            continue
        values = h2h.get("values", h2h.get("outcomes", []))
        odds_map = {}
        for v in values:
            k = v.get("value", v.get("name", ""))
            p = v.get("odd", v.get("price", "-"))
            odds_map[k] = p
        h = odds_map.get(ht, odds_map.get("Home", "-"))
        d = odds_map.get("Draw", "-")
        a = odds_map.get(at, odds_map.get("Away", "-"))
        lines.append(f"{name:<20} {str(h):>7}  {str(d):>7}  {str(a):>9}")

    return "\n".join(lines)
