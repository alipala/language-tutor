"""
Beginner (A1/A2) high-frequency word lists + grammar locks — per language.

Why this exists (2026-07-29):
  OpenAI's realtime prompting guide and CEFR research (arxiv 2501.15247,
  2502.07544; ERIC EJ1466280) converge on one finding: an LLM hits a requested
  CEFR level only when the prompt carries an EXPLICIT high-frequency word list.
  With only a level LABEL ("speak simply, A1"), GPT-4o matched the target level
  ~5% of the time and could NOT distinguish A1 from A2 — the exact "A1 and A2
  start the same / feel the same" complaint we saw in production.

Design:
  - DATA, not prompt logic. The prompt SKELETON stays a single language-agnostic
    template in prompt_v3.py; this file is the per-(language, level) payload it
    injects. Adding a language = adding a dict entry, no code change.
  - A1 / A2 only. B1+ do not need a hard lexical ceiling (research shows the
    model differentiates upper levels adequately, and a broad range is desired).
  - Two parts per (lang, level):
      seed_words: a REPRESENTATIVE sample of the most frequent words (NOT the
        full list — the model generalizes from the sample; ~40 words is enough
        to anchor register without bloating the prompt / blowing the mini-model
        token budget). These are function words + everyday content words drawn
        from standard frequency lists (Routledge Frequency Dictionaries / CEFR-J
        / Oxford 3000 A1-A2 band).
      grammar_lock: the ONE grammatical ceiling for that level, worded as a
        rule the model can follow (guide: state limits explicitly, capitalized).

Languages: english, spanish, german, dutch, french, portuguese.
Level keys: "A1", "A2".
"""

from typing import Dict, List, Optional

# ─────────────────────────────────────────────────────────────────────────────
# Grammar locks — shared shape across languages, translated intent per level.
# Kept language-agnostic here because the STRUCTURE (tense/question limits) is
# what matters; the model applies it in the target language.
# ─────────────────────────────────────────────────────────────────────────────

_GRAMMAR_LOCK: Dict[str, str] = {
    "A1": (
        "GRAMMAR CEILING (A1): Use ONLY the present tense. No past, no future, "
        "no conditionals. Sentences are one clause — subject + verb + object. "
        "NO subordinate clauses (no 'because', 'when', 'if', 'that'). "
        "Ask ONLY yes/no or this-or-that questions. NEVER ask 'why', opinions, "
        "times, dates, or numbers beyond simple counting."
    ),
    "A2": (
        "GRAMMAR CEILING (A2): Present tense mostly; simple past for finished "
        "everyday events is OK. One short subordinate clause ('because', 'when') "
        "is allowed occasionally. Questions may be simple open ones "
        "(what / where / who / did you), but keep them concrete and answerable. "
        "A gentle 'why?' is fine only once the student is relaxed."
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# Per-language seed word samples. ~40 words each: high-frequency function words
# + everyday nouns/verbs/adjectives the level is expected to command.
# ─────────────────────────────────────────────────────────────────────────────

_WORDLISTS: Dict[str, Dict[str, List[str]]] = {
    "english": {
        "A1": [
            "I", "you", "he", "she", "we", "they", "the", "a", "is", "are",
            "have", "do", "like", "want", "go", "eat", "drink", "see", "yes",
            "no", "and", "but", "good", "big", "small", "here", "now", "today",
            "water", "food", "home", "work", "day", "name", "friend", "family",
            "coffee", "this", "that", "please",
        ],
        "A2": [
            "because", "when", "yesterday", "tomorrow", "morning", "evening",
            "week", "month", "always", "sometimes", "never", "often", "buy",
            "cook", "walk", "read", "write", "learn", "meet", "help", "start",
            "finish", "happy", "tired", "busy", "easy", "difficult", "cheap",
            "expensive", "near", "far", "before", "after", "with", "about",
            "money", "city", "weather", "weekend", "holiday",
        ],
    },
    "spanish": {
        "A1": [
            "yo", "tú", "él", "ella", "nosotros", "el", "la", "un", "una",
            "ser", "estar", "tener", "hacer", "gustar", "querer", "ir", "comer",
            "beber", "ver", "sí", "no", "y", "pero", "bueno", "grande",
            "pequeño", "aquí", "ahora", "hoy", "agua", "comida", "casa",
            "trabajo", "día", "nombre", "amigo", "familia", "café", "este",
            "por favor",
        ],
        "A2": [
            "porque", "cuando", "ayer", "mañana", "semana", "mes", "siempre",
            "a veces", "nunca", "comprar", "cocinar", "caminar", "leer",
            "escribir", "aprender", "encontrar", "ayudar", "empezar",
            "terminar", "feliz", "cansado", "ocupado", "fácil", "difícil",
            "barato", "caro", "cerca", "lejos", "antes", "después", "con",
            "sobre", "dinero", "ciudad", "tiempo", "fin de semana", "vacaciones",
            "tarde", "noche", "gente",
        ],
    },
    "german": {
        "A1": [
            "ich", "du", "er", "sie", "wir", "der", "die", "das", "ein",
            "eine", "sein", "haben", "machen", "mögen", "wollen", "gehen",
            "essen", "trinken", "sehen", "ja", "nein", "und", "aber", "gut",
            "groß", "klein", "hier", "jetzt", "heute", "Wasser", "Essen",
            "Haus", "Arbeit", "Tag", "Name", "Freund", "Familie", "Kaffee",
            "dieser", "bitte",
        ],
        "A2": [
            "weil", "wenn", "gestern", "morgen", "Woche", "Monat", "immer",
            "manchmal", "nie", "oft", "kaufen", "kochen", "gehen", "lesen",
            "schreiben", "lernen", "treffen", "helfen", "anfangen",
            "fertig", "glücklich", "müde", "beschäftigt", "einfach",
            "schwierig", "billig", "teuer", "nah", "weit", "vor", "nach",
            "mit", "über", "Geld", "Stadt", "Wetter", "Wochenende", "Urlaub",
            "Abend", "Leute",
        ],
    },
    "dutch": {
        "A1": [
            "ik", "jij", "hij", "zij", "wij", "de", "het", "een", "zijn",
            "hebben", "doen", "houden van", "willen", "gaan", "eten",
            "drinken", "zien", "ja", "nee", "en", "maar", "goed", "groot",
            "klein", "hier", "nu", "vandaag", "water", "eten", "huis", "werk",
            "dag", "naam", "vriend", "familie", "koffie", "deze", "dit",
            "alsjeblieft", "leuk",
        ],
        "A2": [
            "omdat", "wanneer", "gisteren", "morgen", "week", "maand", "altijd",
            "soms", "nooit", "vaak", "kopen", "koken", "lopen", "lezen",
            "schrijven", "leren", "ontmoeten", "helpen", "beginnen", "klaar",
            "blij", "moe", "druk", "makkelijk", "moeilijk", "goedkoop", "duur",
            "dichtbij", "ver", "voor", "na", "met", "over", "geld", "stad",
            "weer", "weekend", "vakantie", "avond", "mensen",
        ],
    },
    "french": {
        "A1": [
            "je", "tu", "il", "elle", "nous", "le", "la", "un", "une", "être",
            "avoir", "faire", "aimer", "vouloir", "aller", "manger", "boire",
            "voir", "oui", "non", "et", "mais", "bon", "grand", "petit", "ici",
            "maintenant", "aujourd'hui", "eau", "nourriture", "maison",
            "travail", "jour", "nom", "ami", "famille", "café", "ce",
            "s'il te plaît", "merci",
        ],
        "A2": [
            "parce que", "quand", "hier", "demain", "semaine", "mois",
            "toujours", "parfois", "jamais", "souvent", "acheter", "cuisiner",
            "marcher", "lire", "écrire", "apprendre", "rencontrer", "aider",
            "commencer", "finir", "heureux", "fatigué", "occupé", "facile",
            "difficile", "bon marché", "cher", "près", "loin", "avant",
            "après", "avec", "argent", "ville", "temps", "week-end",
            "vacances", "soir", "gens",
        ],
    },
    "portuguese": {
        "A1": [
            "eu", "tu", "ele", "ela", "nós", "o", "a", "um", "uma", "ser",
            "estar", "ter", "fazer", "gostar", "querer", "ir", "comer", "beber",
            "ver", "sim", "não", "e", "mas", "bom", "grande", "pequeno", "aqui",
            "agora", "hoje", "água", "comida", "casa", "trabalho", "dia",
            "nome", "amigo", "família", "café", "este", "por favor",
        ],
        "A2": [
            "porque", "quando", "ontem", "amanhã", "semana", "mês", "sempre",
            "às vezes", "nunca", "muitas vezes", "comprar", "cozinhar",
            "caminhar", "ler", "escrever", "aprender", "encontrar", "ajudar",
            "começar", "terminar", "feliz", "cansado", "ocupado", "fácil",
            "difícil", "barato", "caro", "perto", "longe", "antes", "depois",
            "com", "dinheiro", "cidade", "tempo", "fim de semana", "férias",
            "tarde", "noite", "pessoas",
        ],
    },
}

# Normalize common language codes/aliases to the keys above.
_LANG_ALIAS: Dict[str, str] = {
    "en": "english", "english": "english",
    "es": "spanish", "spanish": "spanish", "español": "spanish",
    "de": "german", "german": "german", "deutsch": "german",
    "nl": "dutch", "dutch": "dutch", "nederlands": "dutch",
    "fr": "french", "french": "french", "français": "french",
    "pt": "portuguese", "portuguese": "portuguese", "português": "portuguese",
}


def get_beginner_lexical_lock(language: str, level: str) -> Optional[str]:
    """
    Return a ready-to-inject prompt block (seed word list + grammar ceiling) for
    an A1/A2 session in the given language, or None for B1+ / unknown language.

    The block is small (~40 words + one rule) so it stays well within the
    gpt-realtime-mini instruction budget, and it is worded per OpenAI's guide:
    capitalized key rule, explicit limits, "a sample — generalize from it".
    """
    lvl = (level or "").upper()
    if lvl not in ("A1", "A2"):
        return None
    lang_key = _LANG_ALIAS.get((language or "").lower().strip())
    if not lang_key:
        return None
    words = _WORDLISTS.get(lang_key, {}).get(lvl)
    if not words:
        return None

    grammar = _GRAMMAR_LOCK[lvl]
    word_str = ", ".join(words)
    return (
        f"# Vocabulary ceiling ({lvl})\n"
        f"- Stay within the {lvl} everyday word range. These are SAMPLE high-frequency "
        f"words — generalize from them, do not read the list aloud:\n"
        f"  {word_str}\n"
        f"- If an idea needs a word outside this range, swap it for a simpler one the "
        f"student already knows, or teach the harder word by first saying it, then a "
        f"simple synonym.\n"
        f"- {grammar}"
    )
