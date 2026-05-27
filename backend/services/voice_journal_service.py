"""
Voice Journal Service  (S3.6)

Daily 90-second voice prompt ritual. Provides deterministic daily prompts
per user + language + date, and status checks for the voice_journal_entries
collection.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from database import database


# ──────────────────────────────────────────────────────────────────────────────
# Prompt lists (pre-written — no dynamic translation required per spec)
# ──────────────────────────────────────────────────────────────────────────────

PROMPTS: Dict[str, Dict[str, List[str]]] = {
    "english": {
        "A1": [
            "Tell me about your morning routine. What do you do when you wake up?",
            "Describe your home. How many rooms does it have?",
            "What did you eat today? Was it good?",
            "Talk about a person in your family. Who are they?",
            "What is your favourite colour and why?",
            "Tell me the name of the street or city where you live.",
            "What do you do on weekends?",
        ],
        "A2": [
            "Describe a typical day at work or school from start to finish.",
            "Talk about a hobby you enjoy. How did you start it?",
            "Tell me about a recent trip you took, even a short one.",
            "What kind of food do you usually cook at home?",
            "Describe a friend. What do you like about them?",
            "What was the last film or TV show you watched?",
            "Talk about the weather today and what you prefer.",
        ],
        "B1": [
            "Describe a challenge you faced recently and how you dealt with it.",
            "What is one goal you have for the next six months?",
            "Talk about a news story you heard this week.",
            "Explain why you are learning this language and what motivates you.",
            "Describe your ideal holiday destination and why.",
            "What changes would you make to your town or city if you could?",
            "Talk about a book or podcast that influenced you recently.",
        ],
        "B2": [
            "Discuss the pros and cons of remote work versus working in an office.",
            "Describe a moment in your life that changed your perspective.",
            "What do you think is the biggest challenge facing your generation?",
            "Talk about a skill you wish you had learned earlier.",
            "Describe an important decision you made and whether you would change it.",
            "What role does technology play in your daily relationships?",
            "Discuss how your lifestyle has changed over the past few years.",
        ],
    },
    "dutch": {
        "A1": [
            "Vertel me over je ochtendroutine. Wat doe jij als je wakker wordt?",
            "Beschrijf je huis. Hoeveel kamers heeft het?",
            "Wat heb je vandaag gegeten? Was het lekker?",
            "Vertel over een persoon in je familie. Wie zijn ze?",
            "Wat is je lievelingskleur en waarom?",
            "Vertel me de naam van de straat of stad waar je woont.",
            "Wat doe jij in het weekend?",
        ],
        "A2": [
            "Beschrijf een normale dag op je werk of school van begin tot eind.",
            "Vertel over een hobby die je leuk vindt. Hoe ben je ermee begonnen?",
            "Vertel me over een recente reis die je hebt gemaakt, ook al was het kort.",
            "Wat voor eten kook je meestal thuis?",
            "Beschrijf een vriend. Wat vind je leuk aan hem of haar?",
            "Welke film of tv-serie heb je als laatste gezien?",
            "Vertel over het weer vandaag en wat je liever hebt.",
        ],
        "B1": [
            "Beschrijf een uitdaging die je onlangs hebt gehad en hoe je ermee omging.",
            "Wat is één doel dat je hebt voor de komende zes maanden?",
            "Vertel over een nieuwsbericht dat je deze week hebt gehoord.",
            "Leg uit waarom je deze taal leert en wat je motiveert.",
            "Beschrijf je ideale vakantiebestemming en waarom.",
            "Welke veranderingen zou je aanbrengen in je dorp of stad als je kon?",
            "Vertel over een boek of podcast die je onlangs heeft beïnvloed.",
        ],
        "B2": [
            "Bespreek de voor- en nadelen van thuiswerken versus op kantoor werken.",
            "Beschrijf een moment in je leven dat je perspectief veranderde.",
            "Wat denk je dat de grootste uitdaging is voor jouw generatie?",
            "Vertel over een vaardigheid die je eerder had willen leren.",
            "Beschrijf een belangrijke beslissing die je hebt genomen en of je die zou veranderen.",
            "Welke rol speelt technologie in jouw dagelijkse relaties?",
            "Bespreek hoe jouw levensstijl de afgelopen jaren is veranderd.",
        ],
    },
    "spanish": {
        "A1": [
            "Cuéntame sobre tu rutina matutina. ¿Qué haces cuando te despiertas?",
            "Describe tu casa. ¿Cuántas habitaciones tiene?",
            "¿Qué comiste hoy? ¿Estaba bueno?",
            "Habla de una persona en tu familia. ¿Quién es?",
            "¿Cuál es tu color favorito y por qué?",
            "Dime el nombre de la calle o ciudad donde vives.",
            "¿Qué haces los fines de semana?",
        ],
        "A2": [
            "Describe un día típico en tu trabajo o escuela de principio a fin.",
            "Habla de un hobby que disfrutas. ¿Cómo empezaste?",
            "Cuéntame sobre un viaje reciente que hiciste, aunque fuera corto.",
            "¿Qué tipo de comida sueles cocinar en casa?",
            "Describe a un amigo. ¿Qué te gusta de esa persona?",
            "¿Cuál fue la última película o serie que viste?",
            "Habla del clima hoy y qué prefieres.",
        ],
        "B1": [
            "Describe un desafío que enfrentaste recientemente y cómo lo manejaste.",
            "¿Cuál es un objetivo que tienes para los próximos seis meses?",
            "Habla de una noticia que escuchaste esta semana.",
            "Explica por qué estás aprendiendo este idioma y qué te motiva.",
            "Describe tu destino de vacaciones ideal y por qué.",
            "¿Qué cambios harías en tu pueblo o ciudad si pudieras?",
            "Habla de un libro o podcast que te influyó recientemente.",
        ],
        "B2": [
            "Analiza las ventajas y desventajas del trabajo remoto frente al trabajo en oficina.",
            "Describe un momento en tu vida que cambió tu perspectiva.",
            "¿Cuál crees que es el mayor desafío que enfrenta tu generación?",
            "Habla de una habilidad que desearías haber aprendido antes.",
            "Describe una decisión importante que tomaste y si la cambiarías.",
            "¿Qué papel juega la tecnología en tus relaciones diarias?",
            "Analiza cómo ha cambiado tu estilo de vida en los últimos años.",
        ],
    },
    "french": {
        "A1": [
            "Parle-moi de ta routine matinale. Que fais-tu quand tu te réveilles?",
            "Décris ta maison. Combien de pièces a-t-elle?",
            "Qu'as-tu mangé aujourd'hui? C'était bon?",
            "Parle d'une personne dans ta famille. Qui est-ce?",
            "Quelle est ta couleur préférée et pourquoi?",
            "Dis-moi le nom de la rue ou de la ville où tu habites.",
            "Que fais-tu le week-end?",
        ],
        "B1": [
            "Décris un défi que tu as relevé récemment et comment tu l'as géré.",
            "Quel est un objectif que tu as pour les six prochains mois?",
            "Parle d'une actualité que tu as entendue cette semaine.",
            "Explique pourquoi tu apprends cette langue et ce qui te motive.",
            "Décris ta destination de vacances idéale et pourquoi.",
            "Quels changements apporterais-tu à ta ville si tu pouvais?",
            "Parle d'un livre ou d'un podcast qui t'a influencé récemment.",
        ],
    },
    "german": {
        "A1": [
            "Erzähl mir von deiner Morgenroutine. Was machst du, wenn du aufwachst?",
            "Beschreibe dein Zuhause. Wie viele Zimmer hat es?",
            "Was hast du heute gegessen? War es gut?",
            "Erzähl von einer Person in deiner Familie. Wer ist das?",
            "Was ist deine Lieblingsfarbe und warum?",
            "Nenn mir den Namen der Straße oder Stadt, in der du wohnst.",
            "Was machst du am Wochenende?",
        ],
        "B1": [
            "Beschreibe eine Herausforderung, mit der du kürzlich konfrontiert warst, und wie du damit umgegangen bist.",
            "Was ist ein Ziel, das du für die nächsten sechs Monate hast?",
            "Erzähl von einer Nachricht, die du diese Woche gehört hast.",
            "Erkläre, warum du diese Sprache lernst und was dich motiviert.",
            "Beschreibe dein ideales Urlaubsziel und warum.",
            "Welche Änderungen würdest du an deiner Stadt vornehmen, wenn du könntest?",
            "Erzähl von einem Buch oder Podcast, der dich kürzlich beeinflusst hat.",
        ],
    },
    "portuguese": {
        "A1": [
            "Fala sobre a tua rotina matinal. O que fazes quando acordas?",
            "Descreve a tua casa. Quantos quartos tem?",
            "O que comeste hoje? Era bom?",
            "Fala de uma pessoa na tua família. Quem é?",
            "Qual é a tua cor favorita e porquê?",
            "Diz-me o nome da rua ou cidade onde moras.",
            "O que fazes aos fins de semana?",
        ],
        "B1": [
            "Descreve um desafio que enfrentaste recentemente e como o lidaste.",
            "Qual é um objetivo que tens para os próximos seis meses?",
            "Fala de uma notícia que ouviste esta semana.",
            "Explica por que estás a aprender esta língua e o que te motiva.",
            "Descreve o teu destino de férias ideal e porquê.",
            "Que mudanças farias na tua cidade se pudesses?",
            "Fala de um livro ou podcast que te influenciou recentemente.",
        ],
    },
    "turkish": {
        "A1": [
            "Sabah rutininden bahset. Uyandığında ne yaparsın?",
            "Evini anlat. Kaç odası var?",
            "Bugün ne yedin? Güzel miydi?",
            "Ailenden bir kişiyi anlat. Kim onlar?",
            "En sevdiğin renk ne ve neden?",
            "Yaşadığın sokak veya şehrin adını söyle.",
            "Hafta sonları ne yaparsın?",
        ],
        "B1": [
            "Son zamanlarda karşılaştığın bir zorluğu ve bununla nasıl başa çıktığını anlat.",
            "Önümüzdeki altı ay için bir hedefin nedir?",
            "Bu hafta duyduğun bir haberi anlat.",
            "Bu dili neden öğrendiğini ve seni ne motive ettiğini açıkla.",
            "İdeal tatil destinasyonunu ve nedenini anlat.",
            "Yapabilseydin şehrinde ya da kasabanda ne değiştirirdin?",
            "Son zamanlarda seni etkileyen bir kitap veya podcast'i anlat.",
        ],
    },
}

# Fallback language key when an unsupported language is requested
_FALLBACK_LANGUAGE = "english"

# Fallback level key when an unsupported level is requested
_FALLBACK_LEVEL = "B1"


def _normalise_language(language: str) -> str:
    """Lowercase + strip whitespace; fall back to english."""
    lang = (language or "").lower().strip()
    return lang if lang in PROMPTS else _FALLBACK_LANGUAGE


def _normalise_level(language_key: str, level: str) -> str:
    """Uppercase level; fall back to nearest available level for language."""
    lev = (level or "B1").strip().upper()
    available = list(PROMPTS[language_key].keys())
    if lev in available:
        return lev
    # Try prefix match (e.g., "B1+" → "B1")
    for av in available:
        if lev.startswith(av):
            return av
    return _FALLBACK_LEVEL if _FALLBACK_LEVEL in available else available[0]


def get_today_prompt(user_id: str, language: str, level: str, date_str: Optional[str] = None) -> Dict[str, Any]:
    """
    Return a deterministic daily prompt for the given user + language + level.

    The prompt is stable for the whole day — the same user always gets the same
    prompt on a given date.  It rotates daily via a hash seed.

    Args:
        user_id: MongoDB user ID string.
        language: Target language (e.g. "dutch").
        level: CEFR level (e.g. "B1").
        date_str: ISO date string override (for testing); defaults to today UTC.

    Returns:
        {
            "prompt_id": str,   # stable identifier for this prompt
            "prompt_text": str, # the actual prompt sentence
            "language": str,    # normalised language key
            "level": str,       # normalised level key
        }
    """
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lang_key = _normalise_language(language)
    level_key = _normalise_level(lang_key, level)
    prompts_for_level = PROMPTS[lang_key][level_key]

    # Deterministic seed: hash of user_id + date → pick index
    seed_str = f"{user_id}:{date_str}:{lang_key}:{level_key}"
    seed_hash = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
    idx = seed_hash % len(prompts_for_level)

    prompt_text = prompts_for_level[idx]
    prompt_id = f"{lang_key}_{level_key}_{idx}"

    return {
        "prompt_id": prompt_id,
        "prompt_text": prompt_text,
        "language": lang_key,
        "level": level_key,
    }


async def get_today_journal_status(
    user_id: str,
    language: str,
    level: str,
    date_str: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Check whether the user has already recorded a journal entry today.

    Returns:
        {
            "already_recorded": bool,
            "entry": dict | None,   # the existing entry (if already_recorded)
            "prompt": dict,         # today's prompt (always present)
        }
    """
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lang_key = _normalise_language(language)
    level_key = _normalise_level(lang_key, level)
    prompt = get_today_prompt(user_id, language, level, date_str)

    collection = database.voice_journal_entries
    existing = await collection.find_one(
        {"user_id": user_id, "language": lang_key, "entry_date": date_str},
        {"_id": 0},
    )

    return {
        "already_recorded": existing is not None,
        "entry": existing,
        "prompt": prompt,
    }
