DEFAULT_BLACKLIST = [
    "homicídio", "assassinato", "assalto", "roubo", "furto", "preso", "prisão",
    "delegacia", "polícia", "policial", "crime", "criminoso", "tráfico", "drogas",
    "arma", "tiroteio", "facada", "esfaqueado", "baleado", "morte violenta",
    "latrocínio", "estupro", "feminicídio", "acidente fatal", "corpo encontrado",
    "milícia", "gangue", "operação policial", "mandado", "flagrante", "detido",
    "apreensão", "inquérito", "penal", "homicida", "suspeito preso",
    "vítima fatal", "óbito violento",
]


def is_violent_content(title: str, body: str, blacklist: list[str] | None = None) -> bool:
    if blacklist is None:
        blacklist = DEFAULT_BLACKLIST
    combined = (title + " " + body).lower()
    return any(keyword.lower() in combined for keyword in blacklist)
