CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Maceió": [
        "maceió", "pajuçara", "ponta verde", "jatiúca", "cruz das almas",
        "jaraguá", "capital alagoana",
    ],
    "Arapiraca": ["arapiraca", "agreste alagoano"],
    "Interior": [
        "penedo", "marechal deodoro", "são miguel dos campos",
        "palmeira dos índios", "delmiro gouveia", "união dos palmares",
        "rio largo", "interior de alagoas",
    ],
    "Política": [
        "governo", "governador", "prefeito", "câmara", "senado", "deputado",
        "vereador", "eleição", "político", "legislativo", "executivo",
    ],
    "Esporte": [
        "futebol", "csa", "crb", "campeonato", "jogo", "gol", "atleta",
        "esporte", "torneio", "seleção",
    ],
    "Cultura": [
        "cultura", "festival", "música", "teatro", "exposição", "artista",
        "carnaval", "folclore", "patrimônio",
    ],
}

# Priority order: first match wins
PRIORITY_ORDER = ["Maceió", "Arapiraca", "Interior", "Política", "Esporte", "Cultura"]
FALLBACK_CATEGORY = "Cidades"


def classify_article(title: str, first_paragraph: str) -> str:
    combined = (title + " " + first_paragraph).lower()
    for category in PRIORITY_ORDER:
        keywords = CATEGORY_KEYWORDS[category]
        if any(kw.lower() in combined for kw in keywords):
            return category
    return FALLBACK_CATEGORY
