from telegram import Update
from telegram.ext import ContextTypes
from ..formatters.match import format_team_fixtures
from ..api.budget import BudgetExceeded

# team name aliases → API-Football team_id
# worldcup26.ir filtra por nombre, no por ID — el ID se usa solo para API-Football fallback
TEAM_ID_MAP: dict[str, tuple[int, str]] = {
    # (team_id, canonical_name)
    "argentina": (6, "Argentina"),
    "arg": (6, "Argentina"),
    "australia": (26, "Australia"),
    "aus": (26, "Australia"),
    "austria": (44, "Austria"),
    "bahrain": (758, "Bahrain"),
    "bah": (758, "Bahrain"),
    "belgium": (1, "Belgium"),
    "belgica": (1, "Belgium"),
    "bélgica": (1, "Belgium"),
    "belgium": (1, "Belgium"),
    "bolivia": (23, "Bolivia"),
    "bol": (23, "Bolivia"),
    "brazil": (6, "Brazil"),
    "brasil": (6, "Brazil"),
    "bra": (6, "Brazil"),
    "canada": (119, "Canada"),
    "canadá": (119, "Canada"),
    "can": (119, "Canada"),
    "chile": (21, "Chile"),
    "chi": (21, "Chile"),
    "china": (29, "China"),
    "chn": (29, "China"),
    "colombia": (20, "Colombia"),
    "col": (20, "Colombia"),
    "costa rica": (37, "Costa Rica"),
    "costarica": (37, "Costa Rica"),
    "crc": (37, "Costa Rica"),
    "croatia": (3, "Croatia"),
    "croacia": (3, "Croatia"),
    "cro": (3, "Croatia"),
    "denmark": (21, "Denmark"),
    "dinamarca": (21, "Denmark"),
    "den": (21, "Denmark"),
    "ecuador": (22, "Ecuador"),
    "ecu": (22, "Ecuador"),
    "egypt": (36, "Egypt"),
    "egipto": (36, "Egypt"),
    "egy": (36, "Egypt"),
    "england": (10, "England"),
    "inglaterra": (10, "England"),
    "eng": (10, "England"),
    "france": (2, "France"),
    "francia": (2, "France"),
    "fra": (2, "France"),
    "germany": (25, "Germany"),
    "alemania": (25, "Germany"),
    "ger": (25, "Germany"),
    "ghana": (52, "Ghana"),
    "gha": (52, "Ghana"),
    "greece": (8, "Greece"),
    "grecia": (8, "Greece"),
    "gre": (8, "Greece"),
    "honduras": (48, "Honduras"),
    "hon": (48, "Honduras"),
    "hungary": (769, "Hungary"),
    "hungria": (769, "Hungary"),
    "hungría": (769, "Hungary"),
    "indonesia": (612, "Indonesia"),
    "idn": (612, "Indonesia"),
    "iran": (28, "Iran"),
    "iraq": (43, "Iraq"),
    "irq": (43, "Iraq"),
    "israel": (46, "Israel"),
    "isr": (46, "Israel"),
    "italy": (768, "Italy"),
    "italia": (768, "Italy"),
    "ita": (768, "Italy"),
    "ivory coast": (53, "Ivory Coast"),
    "costa de marfil": (53, "Ivory Coast"),
    "civ": (53, "Ivory Coast"),
    "japan": (15, "Japan"),
    "japon": (15, "Japan"),
    "japón": (15, "Japan"),
    "jpn": (15, "Japan"),
    "jordan": (49, "Jordan"),
    "jor": (49, "Jordan"),
    "korea republic": (17, "Korea Republic"),
    "corea del sur": (17, "Korea Republic"),
    "south korea": (17, "Korea Republic"),
    "kor": (17, "Korea Republic"),
    "kuwait": (62, "Kuwait"),
    "kuw": (62, "Kuwait"),
    "mali": (516, "Mali"),
    "mli": (516, "Mali"),
    "mexico": (16, "Mexico"),
    "méxico": (16, "Mexico"),
    "mex": (16, "Mexico"),
    "morocco": (45, "Morocco"),
    "marruecos": (45, "Morocco"),
    "mar": (45, "Morocco"),
    "netherlands": (9, "Netherlands"),
    "holanda": (9, "Netherlands"),
    "países bajos": (9, "Netherlands"),
    "ned": (9, "Netherlands"),
    "new zealand": (93, "New Zealand"),
    "nueva zelanda": (93, "New Zealand"),
    "nzl": (93, "New Zealand"),
    "nigeria": (34, "Nigeria"),
    "nga": (34, "Nigeria"),
    "norway": (20, "Norway"),
    "noruega": (20, "Norway"),
    "nor": (20, "Norway"),
    "panama": (91, "Panama"),
    "panamá": (91, "Panama"),
    "pan": (91, "Panama"),
    "paraguay": (27, "Paraguay"),
    "par": (27, "Paraguay"),
    "peru": (24, "Peru"),
    "perú": (24, "Peru"),
    "per": (24, "Peru"),
    "poland": (24, "Poland"),
    "polonia": (24, "Poland"),
    "pol": (24, "Poland"),
    "portugal": (27, "Portugal"),
    "por": (27, "Portugal"),
    "qatar": (9, "Qatar"),
    "qat": (9, "Qatar"),
    "romania": (33, "Romania"),
    "rumania": (33, "Romania"),
    "rou": (33, "Romania"),
    "saudi arabia": (38, "Saudi Arabia"),
    "arabia saudita": (38, "Saudi Arabia"),
    "ksa": (38, "Saudi Arabia"),
    "senegal": (77, "Senegal"),
    "sen": (77, "Senegal"),
    "serbia": (14, "Serbia"),
    "srb": (14, "Serbia"),
    "slovakia": (17, "Slovakia"),
    "eslovaquia": (17, "Slovakia"),
    "svk": (17, "Slovakia"),
    "slovenia": (91, "Slovenia"),
    "eslovenia": (91, "Slovenia"),
    "svn": (91, "Slovenia"),
    "spain": (9, "Spain"),
    "españa": (9, "Spain"),
    "esp": (9, "Spain"),
    "switzerland": (15, "Switzerland"),
    "suiza": (15, "Switzerland"),
    "sui": (15, "Switzerland"),
    "thailand": (41, "Thailand"),
    "tailandia": (41, "Thailand"),
    "tha": (41, "Thailand"),
    "togo": (524, "Togo"),
    "tog": (524, "Togo"),
    "trinidad and tobago": (55, "Trinidad and Tobago"),
    "trinidad": (55, "Trinidad and Tobago"),
    "tto": (55, "Trinidad and Tobago"),
    "tunisia": (30, "Tunisia"),
    "tunez": (30, "Tunisia"),
    "túnez": (30, "Tunisia"),
    "tun": (30, "Tunisia"),
    "turkey": (56, "Turkey"),
    "turquia": (56, "Turkey"),
    "turquía": (56, "Turkey"),
    "tur": (56, "Turkey"),
    "ukraine": (772, "Ukraine"),
    "ucrania": (772, "Ukraine"),
    "ukr": (772, "Ukraine"),
    "united arab emirates": (18, "United Arab Emirates"),
    "emiratos": (18, "United Arab Emirates"),
    "uae": (18, "United Arab Emirates"),
    "united states": (35, "United States"),
    "usa": (35, "United States"),
    "estados unidos": (35, "United States"),
    "uruguay": (19, "Uruguay"),
    "uru": (19, "Uruguay"),
    "venezuela": (36, "Venezuela"),
    "ven": (36, "Venezuela"),
    "wales": (732, "Wales"),
    "gales": (732, "Wales"),
    "wal": (732, "Wales"),
}


async def fixture_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "Uso: /fixture [equipo]\nEjemplo: /fixture argentina",
            parse_mode="HTML",
        )
        return

    query = " ".join(args).lower().strip()
    match = TEAM_ID_MAP.get(query)
    if not match:
        # partial match
        for key, val in TEAM_ID_MAP.items():
            if query in key or key in query:
                match = val
                break

    if not match:
        await update.message.reply_text(
            f"No encontré el equipo <b>{query}</b>. Probá con el nombre en inglés o español.",
            parse_mode="HTML",
        )
        return

    team_id, team_name = match
    cache = context.bot_data["cache"]
    cache_key = f"fixtures:team:{team_id}"

    fixtures = await cache.get(cache_key)

    if fixtures is None:
        # Try worldcup26 first (free)
        wc26 = context.bot_data.get("wc26")
        if wc26:
            try:
                fixtures = await wc26.games_for_team(team_name)
                if fixtures:
                    await cache.set_team_fixtures(team_id, fixtures)
            except Exception:
                fixtures = None

    if fixtures is None:
        # Fallback to API-Football with budget check
        budget = context.bot_data["budget"]
        football = context.bot_data["football"]
        try:
            await budget.consume(1)
            raw = await football.team_fixtures(team_id)
            fixtures = raw.get("response", [])
            await cache.set_team_fixtures(team_id, fixtures)
        except BudgetExceeded:
            await update.message.reply_text(
                "⚠️ Límite diario de la API alcanzado. Intentá mañana.",
                parse_mode="HTML",
            )
            return
        except Exception as exc:
            await update.message.reply_text(f"Error al obtener el fixture: {exc}")
            return

    text = format_team_fixtures(fixtures or [], team_name)
    await update.message.reply_text(text, parse_mode="HTML")
