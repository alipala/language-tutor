"""
Story Worlds generator — turns (language, level, genre) into a complete,
playable story world using gpt-4o-mini (cheap, what news generation uses).

A world = setting + character + N scenes. Each scene is a voice quest:
in-story goal, the model "solving" line, a help suggestion, target vocab,
multi-language translations, and a cliffhanger into the next scene.

Mirrors backend/news_generation/news_generator.py: shared async OpenAI client,
gpt-4o-mini, response_format=json_object. No multiplayer — single-player only.
"""

import asyncio
import json
import logging
import os
import random
import re
from typing import Any, Dict, List, Optional

from openai_client import get_async_openai

logger = logging.getLogger(__name__)

# Story/arc generation model. gpt-4o-mini is cheap but, per research, fails to keep a
# multi-episode narrative contradiction-free (≈0% contradiction-free rate on serialized
# storytelling), which is what made episodes drift (a "statue mystery" became a "paintings
# mystery"). gpt-4o holds a coherent arc across episodes. The JUDGE/TURN loop stays on
# gpt-4o-mini (turn_service.py) — it's called every turn and only scores one short reply,
# so it doesn't need the bigger model. Override via STORY_GEN_MODEL for easy rollback.
MODEL = os.getenv("STORY_GEN_MODEL", "gpt-4o")

# ---------------------------------------------------------------------------
# STORY_GENERATOR_FIX_V2 — clean-at-the-source generation.
# Master rollback: STORY_GEN_V2=0 reverts ALL of the V2 behaviour below to legacy
# (byte-identical generation — same model, temp, prompt, and the old empty/help!=me-only
# repair gate). STORY_GEN_V2=1 (default) enables the deterministic structural gate, the
# two-pass (normal→stubborn) repair, and the recoverability prompt block.
STORY_GEN_V2 = os.getenv("STORY_GEN_V2", "1") != "0"
# Finer knob: disable ONLY the (more expensive) cold-recall gate while keeping structural + prompt.
RECOVERABILITY_GATE = os.getenv("STORY_GEN_RECOVERABILITY_GATE", "1") != "0"

# Deterministic detector — single source of truth, mirroring the validated repair-sweep
# (STORY_SCENE_REPAIR_SWEEP_V1) that cleaned the existing corpus, plus a conservative
# cold-recall check. No LLM: pure structural rules over the scene dict.
_ASK_EN = re.compile(r"\b(ask|asks|asking|find out|finds out|finding out|inquire|inquires|"
                     r"request|requests|requesting|question)\b", re.I)
_ASK_TARGET = {
    "english":    _ASK_EN,
    "dutch":      re.compile(r"\b(vraag\w*|informeer\w*|navraag\w*)\b", re.I),
    "spanish":    re.compile(r"\b(pregunt\w*|pide\b|pedir\b|solicit\w*|averigua\w*)\b", re.I),
    "french":     re.compile(r"\b(demand\w*|interrog\w*|renseigne\w*|questionn\w*)\b", re.I),
    "german":     re.compile(r"\b(frag\w*|erkundig\w*|nachfrag\w*)\b", re.I),
    "portuguese": re.compile(r"\b(pergunt\w*|pede\b|pedir\b|solicit\w*|averigu\w*)\b", re.I),
}

# minimal closed-class stopword sets (just enough to isolate CONTENT words for recoverability)
_STOP = {
  "english": set("a an the i you he she it we they me my your his her our their is am are be was were do does did have has had can could will would shall yes no and or but to of in on at this that these those what who where when why how not please ok okay here there".split()),
  "dutch":   set("de het een ik jij je u hij zij ze wij we mijn jouw uw is ben bent zijn was waren heb hebt heeft hebben kan kun kunt zal zul zult ja nee en of maar te van in op aan dit dat deze die wat wie waar wanneer waarom hoe niet alstublieft hier daar".split()),
  "spanish": set("el la los las un una unos unas yo tu usted el ella nosotros ellos mi tu su es soy eres son era si no y o pero a de en con este ese esta esa esto eso que quien donde cuando como por favor aqui alli".split()),
  "french":  set("le la les un une des je tu il elle nous ils mon ton son ma ta sa est suis es sont oui non et ou mais a de en ce cet cette ces que qui ou quand comment ne pas pour ici la".split()),
  "german":  set("der die das ein eine ich du er sie wir mein dein sein ist bin bist sind war waren habe hast hat ja nein und oder aber zu von in auf an dies dieser diese was wer wo wann wie nicht bitte hier da".split()),
  "portuguese": set("o a os as um uma uns umas eu tu voce ele ela nos eles meu teu seu e ou mas de em com este esse esta essa isto isso que quem onde quando como por favor sim nao aqui ali".split()),
}
_YES_NO = {
  "english": ("yes","yeah","yep","sure","okay","ok","no","nope"),
  "dutch":   ("ja","jawel","zeker","nee"),
  "spanish": ("si","sí","claro","vale","no"),
  "french":  ("oui","non","ouais"),
  "german":  ("ja","klar","sicher","nein"),
  "portuguese": ("sim","claro","não","nao"),
}


def _tokens(s: str):
    return re.findall(r"[\wÀ-ÿ']+", (s or "").lower())


def _goal_is_ask(scene: Dict[str, Any], language: str) -> bool:
    if _ASK_EN.search(scene.get("goal_en") or ""):
        return True
    rx = _ASK_TARGET.get((language or "").lower())
    return bool(rx and rx.search(scene.get("goal") or ""))


def _is_recoverable(scene: Dict[str, Any], language: str) -> bool:
    """Conservative: can the player PRODUCE `me` from open.line ALONE?
    Recoverable if `me` is a closed (yes/no-led) reply, or at least one of its content words
    already appears in open.line. False (cold_recall) only when EVERY content word in `me` is
    absent from open.line and it is not a yes/no reply."""
    lang = (language or "").lower()
    me_toks = _tokens(scene.get("me"))
    if not me_toks:
        return True  # emptiness handled by empty_me
    if me_toks[0] in _YES_NO.get(lang, ()):  # "Ja, ...", "Yes, ..." → closed reply
        return True
    stop = _STOP.get(lang, set())
    open_toks = set(_tokens((scene.get("open") or {}).get("line")))
    content = [t for t in me_toks if t not in stop]
    if not content:
        return True  # nothing the player must "know" — fully recoverable
    return any(t in open_toks for t in content)


def scene_breakages(scene: Dict[str, Any], language: str, *, check_recoverability: bool = True) -> List[str]:
    """Single source of truth. Empty list => scene is healthy."""
    codes = []
    me = (scene.get("me") or "").strip()
    open_line = ((scene.get("open") or {}).get("line") or "").strip()
    help_sug = ((scene.get("help") or {}).get("suggestion") or "").strip()
    if not me:
        codes.append("empty_me")
    if help_sug != me:
        codes.append("help_ne_me")
    char_q = open_line.endswith("?")
    if char_q and me.endswith("?"):
        codes.append("echo_question")
    if char_q and _goal_is_ask(scene, language):
        codes.append("goal_ask_after_char_asked")
    if check_recoverability and me and not _is_recoverable(scene, language):
        codes.append("cold_recall")
    return codes


# Creative-seed pools. gpt-4o-mini collapses to the same "most likely" answer for
# a given (genre, level) — e.g. EVERY supernatural prompt produced a silver-haired
# forest guide named "Luna". Injecting a random seed per series steers the model
# off that default toward distinct characters and settings, so two stories with the
# same genre don't clone each other. Seeds are flavour nudges, not hard constraints.
_SEED_TONES = [
    "cozy and heartwarming", "tense and suspenseful", "playful and comedic",
    "bittersweet and reflective", "epic and grand", "quirky and offbeat",
    "warm and nostalgic", "mysterious and dreamlike",
]
_SEED_SETTINGS = [
    "a bustling city", "a quiet coastal town", "a remote mountain village",
    "a busy market", "an old train station", "a rooftop garden", "a night bazaar",
    "a sleepy farm", "a harbour at dawn", "a desert outpost", "a forgotten library",
    "a lively street festival", "a snowed-in cabin", "a riverside café",
]
_SEED_LEADS = [
    "an unexpected elderly mentor", "a witty street vendor", "a nervous newcomer",
    "a retired traveller", "a curious child", "a no-nonsense shopkeeper",
    "a wandering musician", "a local guide with a secret", "a rival turned ally",
    "a cheerful baker", "a grumpy neighbour with a soft heart", "a daring explorer",
]

# Scenes scale by CEFR — DEPTH grows with level, count stays in a tight band
# (per the progression spec: A1=5, C2 up to ~12).
# Tight one-sitting band (~5-7 min/episode). Depth scales via DIFFICULTY, not count —
# but with the daily-drip release (1 episode/day) a slightly longer episode reads more
# like a real mini-series instalment without breaking the "one sitting" feel. A1/A2=8,
# B1/B2=10. C1/C2 stay shorter (out of the current A1-B2 content plan).
SCENES_BY_LEVEL: Dict[str, int] = {
    "A1": 8, "A2": 8, "B1": 10, "B2": 10, "C1": 7, "C2": 7,
}

# The 7 support languages we localise translations into (matches ConversationHelp).
SUPPORT_LANGS = ["english", "turkish", "spanish", "french", "german", "dutch", "portuguese"]

# The 6 languages the app supports (matches challenge/news generation).
LANG_NAMES = {
    "english": "English", "spanish": "Spanish", "french": "French",
    "german": "German", "dutch": "Dutch", "portuguese": "Portuguese",
}

# 20 Gen-Z-friendly genres. Keys are stable ids; titles/labels live in the admin UI.
GENRES = [
    "daily_life",      # everyday life, slice-of-life
    "mystery",         # whodunnit, clues
    "romance",         # gentle crush / relationship
    "adventure",       # quests, exploration
    "sci_fi",          # space, future, tech
    "fantasy",         # magic, dragons, other worlds
    "horror",          # spooky, suspense (teen-safe)
    "thriller",        # high-stakes, chase, escape
    "comedy",          # funny, awkward, lighthearted
    "drama",           # emotional, coming-of-age
    "sports",          # football, competition, training
    "music",           # band, concert, becoming an artist
    "gaming",          # esports, streamers, virtual worlds
    "social_media",    # influencer, viral, online life
    "school_life",     # campus, exams, friendships
    "travel",          # backpacking, getting lost abroad
    "food",            # cooking, foodie, restaurant
    "fashion",         # style, design, runway
    "supernatural",    # ghosts, powers, the uncanny
    "detective",       # noir, investigation, spy
]


# Per-genre WORLD steering so each genre produces its OWN distinct setting + a lead of a
# fitting (and varied) age/occupation — instead of every story collapsing into "a high
# school student" (gpt-4o's default for "simple, teen-safe"). These are inspiration, not
# hard scripts; they exist to break the self-repetition the founder flagged.
_GENRE_WORLD: Dict[str, str] = {
    "daily_life":   "an ordinary adult's everyday world — a neighbourhood, a workplace, a home; lead is an adult (a barista, a nurse, a parent, a retiree).",
    "mystery":      "a place with secrets — a coastal town, an old hotel, a museum; lead can be a curious adult, a detective, a journalist, a shopkeeper (NOT necessarily a student).",
    "romance":      "a gentle adult romance — a café, a bookshop, a small town; two grown-ups meeting (e.g. a florist and a musician).",
    "adventure":    "an expedition — mountains, jungle, open sea, ruins; lead is an explorer, guide, sailor, or archaeologist.",
    "sci_fi":       "the future or space — a station, a colony, a lab; lead is an engineer, pilot, scientist, or android.",
    "fantasy":      "a magical realm — a kingdom, a forest, a market of wonders; lead is a mage, blacksmith, traveller, or creature.",
    "horror":       "an eerie but teen-safe setting — a foggy village, an old house; lead is an adult investigating strange events.",
    "thriller":     "high stakes — a city at night, a train, an embassy; lead is a spy, agent, courier, or ordinary person caught up in events.",
    "comedy":       "a funny everyday mix-up — a restaurant, an office, a wedding; lead is an adult with a relatable problem (vary the job).",
    "drama":        "an emotional human story — a family business, a hospital, a small town; lead is an adult facing a turning point.",
    "sports":       "a team or athlete — a club, a gym, a stadium; lead is a coach, an athlete, or a determined amateur (any age).",
    "music":        "the music world — a band, a studio, a street festival; lead is a musician, producer, or singer.",
    "gaming":       "games/esports — a tournament, a studio, a virtual world; lead is a gamer, streamer, or developer.",
    "social_media": "online life — content creation, going viral; lead is a creator, photographer, or small-business owner.",
    "school_life":  "a campus — THIS is the one genre set at a school; lead is a student or teacher.",
    "travel":       "a journey abroad — a foreign city, a hostel, a train; lead is a backpacker, a guide, or a local host (any age).",
    "food":         "the food world — a kitchen, a market, a family restaurant; lead is a chef, baker, vendor, or home cook.",
    "fashion":      "design/style — an atelier, a runway, a vintage shop; lead is a designer, tailor, or stylist.",
    "supernatural": "the uncanny — a haunted lighthouse, a town with a secret; lead is an adult with or investigating a strange gift.",
    "detective":    "investigation/noir — a precinct, a rainy city, a crime scene; lead is a detective, private eye, or reporter.",
}


def _genre_world(genre: str) -> str:
    return _GENRE_WORLD.get(genre, "a vivid, concrete world fitting the genre; vary the lead's age and occupation.")


# Concrete, research-grounded difficulty bands so A1 and B1 don't feel identical.
# Sentence-length / vocab numbers come from CEFR text-profiling studies (A1 ~7.7
# words/sentence, A2 ~10.9, B1 ~15.2; A1 ≈66% top-frequency words, dropping per level).
# These describe the CHARACTER's lines AND the expected player answer length.
_DIFFICULTY: Dict[str, str] = {
    "A1": (
        "A1 (true beginner). Character lines: 1 short sentence, MAX ~7 words, present "
        "tense only, the ~500 most common words. The player's answer `me` is 2-5 words "
        "(a set phrase, a yes/no + reason, a name, a number). No subordinate clauses, no "
        "past/future tense. Concrete here-and-now situations (greetings, asking prices, "
        "directions, simple wants)."
    ),
    "A2": (
        "A2 (elementary). Character lines: 1-2 sentences, ~8-11 words each, mostly present "
        "with simple past for events, common everyday vocabulary. The player's answer `me` "
        "is a short full sentence (~4-8 words). Simple connectors allowed (en, maar, want / "
        "and, but, because). Familiar topics: shopping, routines, plans, feelings."
    ),
    "B1": (
        "B1 (intermediate). Character lines: 2 sentences, ~12-15 words each, past/present/"
        "future, the character pushes back and asks WHY. The player's answer `me` is a "
        "1-2 sentence explanation or opinion (~8-15 words) that gives a reason. Use "
        "connectors (omdat, hoewel, daarom / because, although, so). Topics can be abstract-ish."
    ),
    "B2": (
        "B2 (upper-intermediate). Character lines: 2-3 sentences, ~15-18 words, varied tenses "
        "and some idiom. The player must persuade, compare, or hypothesise in 2-3 sentences. "
        "Expect nuance, disagreement to resolve, conditional structures."
    ),
    "C1": (
        "C1 (advanced). Character lines: rich, ~18-22 words, idiomatic, implied meaning. The "
        "player argues a nuanced position, handles abstract/figurative topics, registers shift."
    ),
    "C2": (
        "C2 (mastery). Character lines: sophisticated, subtle, fully idiomatic. The player "
        "produces precise, register-appropriate, near-native responses to layered prompts."
    ),
}


def _difficulty_profile(level: str) -> str:
    return _DIFFICULTY.get(level.upper(), _DIFFICULTY["A1"])


def _episode_ramp(episode_number: int, total_episodes: int) -> str:
    """A GENTLE within-series difficulty curve, applied ON TOP of the CEFR band.
    The whole series stays at its level — this only nudges richness so the opening
    episodes feel effortless and confidence builds. The player must NEVER hit a
    'I can't answer this' wall: even the last episode stays comfortably answerable.
    Maps 5 episodes to the founder's curve: EP1-2 very easy, EP3 easy, EP4-5 a touch richer."""
    if total_episodes <= 1:
        return ""
    # position 0..1 across the series
    pos = (episode_number - 1) / max(1, total_episodes - 1)
    if pos <= 0.25:        # EP1
        band = ("OPENING EPISODE — the EASIEST of the whole series. HARD CAP: every character "
                "`open.line` is ONE short sentence of AT MOST 6 words. The player's `me` is a "
                "2-3 word set phrase. No two-sentence lines, no sub-clauses, no abstract words. "
                "Zero friction — this is where the player decides to keep playing.")
    elif pos <= 0.45:      # EP2 of 5
        band = ("EARLY EPISODE — still very easy. Character `open.line` AT MOST 7 words, one "
                "sentence. Player `me` 2-4 words. High-frequency words, predictable answers.")
    elif pos <= 0.65:      # EP3 of 5
        band = ("MID EPISODE — easy. Character `open.line` up to ~8 words; the player's answers "
                "may be a short full sentence (3-5 words). Still well within the level.")
    else:                  # EP4-EP5 of 5
        band = ("LATER EPISODE — a touch richer: `open.line` up to ~9 words, the player's answer "
                "can be a short full sentence (4-6 words). IMPORTANT: still comfortably answerable "
                "for THIS level — never a wall, never a test. Only slightly richer than the "
                "opening, never beyond the level.")
    return (f"WITHIN-SERIES DIFFICULTY RAMP (episode {episode_number} of {total_episodes}) — this "
            f"OVERRIDES the band length where stricter: {band}")


_RECOVERABILITY_BLOCK = """
RECOVERABILITY (critical for low levels — this is the #1 reason beginners get stuck and quit):
The player must be able to PRODUCE the answer `me` from `open.line` ALONE. They should ONLY have to
work out HOW to say the reply in {lang_name}, NEVER guess WHAT information to supply from memory.
- Put any content word the player needs INTO `open.line` (let the CHARACTER name the object, place,
  or person), OR make `me` a closed response (yes/no, or a choice between options the character
  stated in open.line).
- WRONG (cold recall): open.line "What is missing?" → me "An old compass." — the word "compass" is
  nowhere in the question, so the player cannot know to say it.
- RIGHT (recoverable): open.line "The compass is gone! Can you help me find it?" → me "Yes, I can."
  — the character names the compass; the player only confirms.
- RIGHT (recoverable): open.line "Is the door open or closed?" → me "It is closed." — both options
  are given; the player just picks one.
Read every scene back: if the player would have to invent a content word that is not in open.line,
rewrite open.line so the character supplies it.
"""


def _system_prompt(language: str, level: str, scene_count: int,
                   episode_number: int = 1, total_episodes: int = 1,
                   v2: bool = None) -> str:
    if v2 is None:
        v2 = STORY_GEN_V2
    lang_name = LANG_NAMES.get(language.lower(), language.title())
    # In-target-language example so the model anchors on the RIGHT language
    # (using a Dutch example when target was English caused it to drift).
    open_ex, me_ex = _example_lines(language.lower())
    difficulty = _difficulty_profile(level)
    ramp = _episode_ramp(episode_number, total_episodes)
    # V2: recoverability guidance appended right after the difficulty/ramp section.
    # V2 off → empty string → byte-identical to the legacy prompt.
    recoverability = _RECOVERABILITY_BLOCK.format(lang_name=lang_name) if v2 else ""
    return f"""You are an expert language-learning game designer creating a single-player
VOICE adventure that teaches the {lang_name.upper()} LANGUAGE to learners at CEFR level {level}.

⚠️ TARGET LANGUAGE = {lang_name.upper()}. Every in-game spoken line (`open.line`, `me`,
`goal`, `reply.line`, `suggestion`) MUST be written in {lang_name}, and ONLY {lang_name}.
The learner is practising {lang_name}, so the characters speak {lang_name} to them. Do NOT
write these lines in any other language (not Turkish, not the language of this prompt).
If {lang_name} is English, the lines are in ENGLISH.

The learner talks their way through a short story. Each SCENE is a quest: the
character resists until the learner says the right thing in {lang_name}, then the
scene unlocks. Your job: produce a vivid, finishable world with {scene_count} scenes.

WHO IS PLAYING (design for the human, not just the CEFR label):
- This is a GAME first, a lesson second. The player opened it to feel a story pull them
  forward and to feel "I can do this in {lang_name}" — NOT to be tested. If the very first
  scene feels impossible, they quit. Every scene MUST end in a small win.
- Make each scene WINNABLE on the first or second try by someone who barely knows {lang_name}.
  The correct answer is always a SHORT, HIGH-FREQUENCY phrase the player can RECOGNISE even
  if they couldn't have produced it cold.
- The fun is in the STORY and the feeling of progress, not in difficulty. Difficulty rises
  across the SERIES and via richer phrasing — never by turning a single scene into a
  guessing game.
- The learner TYPES their answer (no multiple-choice). So the goal must be answerable with
  a SHORT phrase a {level} learner can actually recall and produce, and `open.line` should
  make the expected kind of answer obvious from context (the player should never have to
  guess WHAT to say, only HOW to say it in {lang_name}).

DIFFICULTY BAND FOR THIS STORY — calibrate EVERY line and every `me` to this exactly, so
the level is unmistakable (an A1 story must feel clearly easier than a B1 one):
  {difficulty}

{ramp}
{recoverability}
WHO IS WHO (read carefully — getting this wrong breaks the whole game):
- The story is a conversation between the LEAD CHARACTER and the LEARNER (the player).
- The LEAD CHARACTER (the named character of this world) is the one TALKING TO the player.
  Every `open.line` and `reply.line` is spoken BY the lead character (or another named
  side-character), addressed TO the learner.
- The LEARNER is the player. `me` is the LEARNER's reply — NOT the lead character's words.
  The learner is a separate person FROM the lead character: the lead character talks, the
  learner answers.
- NAME RULES (this is what makes dialogue sound human):
  * The lead character must NEVER address the learner by the lead's OWN name, and must never
    speak their own name back to themselves (a character saying "Emma, can you...?" when the
    character IS Emma is WRONG and absurd).
  * The character does NOT know the learner's name, so do NOT invent a name for the learner
    and do NOT start lines with a name-vocative at all. Write "Can you help me?" — never
    "Emma, can you help me?".
  * No `open.line` or `reply.line` may begin with a personal name followed by a comma. Vary
    the openings naturally (a question, a reaction, a request), like real speech.

HARD RULES:
- All `line`, `me`, `goal`, `suggestion` fields that are spoken in-game must be in {lang_name}.
- ZERO foreign-word leakage: every in-game word must be a real {lang_name} word. Do NOT drop
  English (or any other language) words into {lang_name} lines — translate the concept fully.
  (e.g. if {lang_name} is Dutch, write "raadsel", never "riddle"; "sleutel", never "key".)
  This applies to `goal`, `open.line`, `me`, `reply.line`, `help.suggestion` — all of them.
- CRITICAL — `open.line` vs `me` are DIFFERENT SPEAKERS:
  * `open.line` = the CHARACTER speaks first, addressing the player and creating a
    need/question. It MUST NOT contain the answer the player should give, and MUST
    end by handing the turn to the player (a question, a request, or an invitation
    to respond — e.g. "{open_ex}"). NEVER put the player's own line here.
  * `me` = the PLAYER's response that satisfies the goal (e.g. "{me_ex}").
  * They must never be the same sentence or two halves of one exchange swapped.
- CRITICAL — the four fields of EACH scene must form ONE coherent exchange. Build every
  scene by reading it as a real back-and-forth and checking ALL of these:
  * `goal` describes what THE PLAYER must do, written from the PLAYER's side of the
    conversation — never something the character already did. If `open.line` already
    asks the question or makes the request, the goal MUST be to ANSWER/respond to it,
    not to ask the same thing again. (Bad: open.line = "Can you help me?" with goal =
    "ask for help" — the character already asked; the player should AGREE to help.)
  * `me` must be the natural, correct reply to `open.line` AND fully satisfy `goal`.
    Read open.line → me out loud: it must sound like a real two-person exchange.
  * `help.suggestion` MUST be the SAME utterance as `me` (or a trivially close variant
    that also satisfies the goal). It is the line a stuck learner copies to win the
    scene. NEVER make `help.suggestion` an unrelated phrase (e.g. goal = answer a
    question, but help = "Say 'Thank you'" is WRONG).
  * `reply.line` must be the character's natural reaction to `me` (acknowledging what
    the player just said), then nudge the story forward.
- SELF-CHECK each scene before finalising, and REWRITE it if ANY answer is no:
  * does open.line → me → reply.line read as one natural mini-dialogue?
  * does `me` actually achieve `goal`, and is `goal` written from the PLAYER's side
    (a thing the player must SAY/DO in response — not a restatement of what the
    character already did)?
  * is `help.suggestion` == `me`?
- Difficulty MUST match {level}: A1 = single short survival phrases; B1 = connected
  talk, the character pushes back and asks for reasons; C1+ = nuanced persuasion.
- Each scene's `me` is the SHORTEST natural utterance that achieves the goal — it is
  the model answer that unlocks the scene.
- `translations` must provide the {lang_name} line rendered into EACH support language.
- `title` and the story content are in {lang_name}; `title_en` and `description` are in English for the admin.
- STUDENT BRIEFING — produce `student_briefing` LAST, AFTER the scenes. It is a NETFLIX-STYLE
  'what awaits you in this episode' preview the learner reads BEFORE the conversation. Its jobs are
  to give the player REAL CONTEXT (who, where, what's happening, what's at stake) and spark
  curiosity, so they begin feeling oriented and ready — not dropped in cold. Be genuinely helpful
  and descriptive: `hook` is a full 3-4 sentence setup and `mission` is 2 sentences (see the field
  specs below for exactly what each must cover). Write both in {lang_name} (the TARGET language) at
  CEFR {level} so the learner can read them (immersion + reading practice), and provide ALL
  support-language translation keys for each. STRICT RULES: it MUST NOT reveal how the episode
  resolves, MUST NOT contain any of the player's answer lines (`me`), and MUST NOT tell the player
  what to SAY or coach exact phrasing. Rich context and goal in broad story terms only — the puzzle
  is still solved in the conversation, and the in-scene Help (not the briefing) is what rescues a
  stuck player. Think "the episode description on a streaming app", never "here are the answers".
- Keep it wholesome and safe (family-friendly, no graphic violence, romance is gentle) —
  but this does NOT mean it must be about teenagers or school. Characters can be ANY age
  (children, young adults, adults, the elderly) and ANY walk of life. Only the `school_life`
  genre is set at a school.
- The final scene is the climax (a satisfying resolution).

Return STRICT JSON only."""


# A tiny in-target-language example pair so the model anchors on the correct
# language rather than echoing the prompt language.
_EXAMPLES = {
    "english":    ("Hello! Can I help you?", "Yes, please."),
    "dutch":      ("Hallo! Kan ik je helpen?", "Ja, graag."),
    "german":     ("Hallo! Kann ich dir helfen?", "Ja, gerne."),
    "spanish":    ("¡Hola! ¿Te puedo ayudar?", "Sí, por favor."),
    "french":     ("Bonjour ! Je peux t'aider ?", "Oui, s'il te plaît."),
    "portuguese": ("Olá! Posso ajudar?", "Sim, por favor."),
}


def _example_lines(language: str):
    return _EXAMPLES.get(language, _EXAMPLES["english"])


# Turkish-only letters + common function words. Turkish is our support language and
# the most frequent "leak" into the title; if these show up in a non-Turkish target
# title, the model drifted and we fall back to title_en.
_TR_LETTERS = set("şŞğĞıİ")
_TR_WORDS = {"nın", "nin", "nun", "nün", "ları", "leri", "macera", "sırlar", "hazine", "avı", "ve", "bir"}


def _looks_non_target(title: str, language: str) -> bool:
    """Heuristic: does this title look like it's NOT in the target language?
    Conservative — only flags Turkish leakage (the common failure), and never for
    Turkish-adjacent targets. Returns False when unsure (don't over-correct)."""
    if language in ("turkish",):
        return False
    low = title.lower()
    if any(ch in _TR_LETTERS for ch in title):
        return True
    # apostrophe-suffix pattern like "Lila'nın" is a strong Turkish signal
    if "'n" in low and any(low.endswith(w) or (w + " ") in (low + " ") for w in ("nın", "nin", "nun", "nün")):
        return True
    return False


def _user_prompt(language: str, level: str, genre: str, scene_count: int, theme: str = "", seed: str = "", cast: str = "") -> str:
    lang_name = LANG_NAMES.get(language.lower(), language.title())
    theme_line = f"\nTheme hint: {theme}" if theme else ""
    seed_line = f"\n{seed}" if seed else ""
    cast_line = f"\n{cast}" if cast else ""
    return f"""Create one {genre} story world that teaches {lang_name}, for level {level},
with exactly {scene_count} scenes. ALL in-game spoken lines must be in {lang_name}.{theme_line}{seed_line}{cast_line}

ORIGINALITY (important): invent a FRESH character and setting. Do NOT default to
overused fantasy/AI names like Luna, Max, Lily, Aria, Nova, Leo, Sam, or Mia, and
avoid the generic "silver-haired magical forest guide" trope. Give the lead a
specific, ordinary, culturally-fitting name and a concrete, non-cliché setting.
Two stories of the same genre should feel clearly different from each other.

Return JSON with this EXACT shape:
{{
  "title": "evocative world title written in {lang_name} (the TARGET language — never any other language). If the target language is English, this is in English.",
  "title_en": "the same title in English for admin reference (identical to title when the target language is English)",
  "tagline": "a SHORT punchy hook in {lang_name} (the TARGET language), MAX 6 words, that makes someone want to start — a teaser, not a summary (e.g. a tantalising question or a hint of the mystery). No spoilers.",
  "synopsis": "a 2-3 sentence back-cover SUMMARY of the whole story in {lang_name} (the TARGET language), written AT THIS CEFR LEVEL ({level}) so the learner can read it — introduce the lead character, the setting, and the central mystery/goal, WITHOUT spoiling the ending. Simple, inviting, present tense for A1/A2.",
  "description": "one-line hook in English (admin reference)",
  "genre": "{genre}",
  "setting": "where it takes place (English, for the cover artist)",
  "character": {{ "name": "...", "role": "e.g. the vendor", "persona": "1 sentence" }},
  "style_bible": "the SERIES-wide visual identity for the cover artist (English): the lead character's exact appearance (age, hair, clothing, distinguishing features), the colour palette, and the art style — concrete enough that every episode cover shows the SAME character and look. No text.",
  "cover_prompt": "a rich, concrete visual description of THIS EPISODE's cover moment for an illustrator — feature the lead character in a scene that captures this episode's hook. Choose a BRIGHT, well-lit, daytime or luminous moment (the app has a dark UI, so dark/night/gloomy covers disappear); vivid and colourful, no text",
  "episode_synopsis": "a 1-2 sentence summary of THIS EPISODE specifically in {lang_name} (the TARGET language), written at CEFR {level} so the learner can read it — what happens in THIS episode and why it matters, WITHOUT spoiling its ending. (This is per-episode; the top-level `synopsis` summarises the whole story.)",
  "student_briefing": {{
    "hook": "a RICH 'what awaits you in this episode' setup in {lang_name} (the TARGET language), written AT CEFR {level} so the learner can READ it — 3 to 4 sentences (aim ~40-70 words), like a proper streaming-app episode description. Cover, in order: (1) WHO the player meets and WHERE they are, (2) the SITUATION / what just happened, (3) the TENSION or question that makes it intriguing, (4) what kind of moment is COMING UP for the player. Give enough concrete context that someone who never saw the story understands the setup and feels ready to begin. Keep sentences simple and level-appropriate (short clauses for A1/A2). It MUST NOT reveal the plot resolution, MUST NOT contain any of the player's answer lines, and MUST NOT tell them what to say. Atmosphere, characters, and situation only.",
    "hook_translations": {{ {", ".join(f'"{l}": "..."' for l in SUPPORT_LANGS)} }},
    "mission": "TWO sentences in {lang_name} (TARGET language) at CEFR {level} describing the learner's GOAL for this episode in broad story terms. Sentence 1: WHAT they are trying to achieve in the story (e.g. 'Help the engineer find the fault.'). Sentence 2: a little more on WHY it matters or what success looks like, so the goal feels concrete and motivating. Describe the goal, NOT how to say it — no phrases the player will type, no specific answers, no solutions.",
    "mission_translations": {{ {", ".join(f'"{l}": "..."' for l in SUPPORT_LANGS)} }}
  }},
  // student_briefing is a Netflix-style 'coming up' preview the learner reads before the
  // conversation. It builds context + curiosity ONLY. It must NEVER leak the puzzle answers
  // (the `me` lines) or coach exact phrasing — that's what the in-scene Help is for.
  "scenes": [
    {{
      "label": "Scene 1 of {scene_count} · short title",
      "goal": "what THE PLAYER must do, in the TARGET language — a direct response to open.line, from the player's side (never restate what the character already did)",
      "goal_en": "the same goal in English (admin reference)",
      "open": {{ "line": "the character's opening line in target language — asks/requests something and hands the turn to the player",
                 "translations": {{ {", ".join(f'"{l}": "..."' for l in SUPPORT_LANGS)} }} }},
      "me": "the shortest natural learner utterance that REPLIES to open.line and satisfies goal (target language)",
      "reply": {{ "line": "character's natural reaction to `me` once solved, then nudge the story forward (target language)",
                  "translations": {{ {", ".join(f'"{l}": "..."' for l in SUPPORT_LANGS)} }} }},
      "help": {{ "suggestion": "MUST equal `me` (the exact winning line a stuck learner copies) — never an unrelated phrase (target language)",
                 "translations": {{ {", ".join(f'"{l}": "..."' for l in SUPPORT_LANGS)} }},
                 "why": "1-line tip in English on the structure used" }},
      "vocab": ["3-5 target words the learner practised this scene"],
      "narr": {{ "line": "a one-line NARRATOR beat in {lang_name} (the TARGET language) at CEFR {level} — a short cinematic sentence describing what the character DOES or what happens next, bridging into the next scene (e.g. 'Sophie opens her laptop to look for clues.'). Story prose, present tense, readable at this level.",
                 "translations": {{ {", ".join(f'"{l}": "..."' for l in SUPPORT_LANGS)} }} }}
    }}
    // ... {scene_count} scenes total, final one resolves the story
  ]
}}"""


def _continuity_block(
    episode_number: int,
    total_episodes: int,
    continuity_hint: str,
    style_bible: str = "",
    arc: Dict[str, Any] = None,
    prev_summary: str = "",
    language: str = "english",
) -> str:
    """Extra prompt for episodes 2..N — keeps the season coherent.

    `arc` (from plan_series_arc) gives the season spine + THIS episode's planned beat;
    `prev_summary` is the REAL summary of the previous episode just generated (its
    title + how it actually ended), so this episode continues what truly happened
    rather than a vague hook. Both are best-effort — absent → old behaviour."""
    lang_name = LANG_NAMES.get(language.lower(), language.title())
    if episode_number <= 1:
        return ""
    is_finale = episode_number >= total_episodes
    finale_rule = (
        "This is the FINAL episode of the series. RESOLVE the whole story arc and end "
        "warm and complete (no new cliffhanger). Set \"next_hook\" to null. The cover_prompt "
        "should be the most epic/dramatic of the series."
        if is_finale else
        "End this episode on a NEW cliffhanger (\"next_hook\") that pulls the player into the next episode."
    )
    style_rule = (
        f"- REUSE this exact series visual identity for style_bible (do not reinvent it): {style_bible}"
        if style_bible else
        "- keep style_bible consistent with the established series look"
    )

    # The SEASON spine — the single most important fix for inter-episode drift.
    arc = arc or {}
    brief = arc_episode_brief(arc, episode_number)
    arc_block = ""
    if arc:
        arc_block = f"""
SEASON SPINE (do NOT deviate — this is one continuous story, not a new plot):
- Lead character (keep them, never rename): {(arc.get('character') or {}).get('name', '')}
- Central mystery/goal of the WHOLE season (every episode is about THIS exact thing — never
  swap it for a different object or topic): {arc.get('central_question', '')}
- How the season ends (do NOT reveal this yet unless this is the finale): {arc.get('payoff', '')}
- THIS EPISODE'S planned beat: {brief.get('beat', '')}
- It must pick up & {('resolve' if not is_finale else 'pay off')}: {brief.get('resolves', 'the previous episode')}
- This episode ends on: {brief.get('hook', '') if not is_finale else 'the full resolution (no cliffhanger)'}
- THIS episode's title should be: "{brief.get('title_en', '')}" (keep it on the central mystery)"""

    prev_block = f"\nWHAT ACTUALLY HAPPENED LAST EPISODE (continue directly from this): {prev_summary}" if prev_summary else ""

    return f"""

THIS IS EPISODE {episode_number} OF {total_episodes} in ONE ongoing serialized story.
Previously: {continuity_hint}{prev_block}{arc_block}
Continue the SAME characters and world. You MUST:
- open with a short \"recap\" field (English, 1 sentence, \"Last time: …\") that refers to what
  ACTUALLY happened last episode (above), not a generic line — this is an internal note
- the FIRST scene's `open.line` should naturally remind the player where the story stood
  (in {lang_name}), so the continuity is felt in-game without a separate recap screen
- pick up DIRECTLY from where the previous episode left off (resolve or escalate its hook) —
  do NOT start an unrelated new plot, do NOT change the setting, and do NOT rename or swap
  the central mystery/object (if the season is about a missing statue, it stays a statue)
- DO NOT RE-ASK or re-reveal information the player already learned in a previous episode.
  Anything stated above as already-happened is KNOWN — treat it as established fact and BUILD
  on it. (Bad: a character's condition/clue was revealed last episode, then this episode a
  scene asks "what is your condition?" again.) Each scene must move NEW ground forward, never
  re-cover a beat the player already completed.
{('- This is NOT the finale: do NOT solve the central mystery yet. Advance it and leave a new question open.' if not is_finale else '- This IS the finale: now fully resolve the central mystery and pay it off.')}
{style_rule}
- cover_prompt must show the SAME lead character (per style_bible) in THIS episode's new moment
- {finale_rule}
Add these top-level fields to the JSON: "recap" (string|null), "next_hook" (string|null)."""


def _normalize_narr(narr: Any) -> Dict[str, Any]:
    """Coerce a scene's `narr` to {line, translations}. Accepts the new object shape or a
    legacy bare string (puts it in `line`, leaves translations empty for the app to fall back)."""
    if isinstance(narr, dict):
        line = (narr.get("line") or "").strip()
        tr = narr.get("translations")
        tr = tr if isinstance(tr, dict) else {}
        return {"line": line, "translations": {l: (tr.get(l) or "").strip() for l in SUPPORT_LANGS}}
    # legacy string (or None)
    return {"line": (narr or "").strip() if isinstance(narr, str) else "",
            "translations": {l: "" for l in SUPPORT_LANGS}}


def _ensure_student_briefing(briefing: Any, scenes: List[Dict[str, Any]], ep_syn: str) -> Dict[str, Any]:
    """Normalise the model's student_briefing into the Netflix-style {hook, mission} shape
    (target-language text + per-language translations), or synthesise a minimal one from the
    episode synopsis. CRITICAL: never derive content from scene `me` answers — the briefing
    must NOT leak the puzzle solutions; it only sets context + curiosity."""
    def _clean_tr(d):
        d = d if isinstance(d, dict) else {}
        return {l: (d.get(l) or "").strip() for l in SUPPORT_LANGS}

    if isinstance(briefing, dict) and (briefing.get("hook") or "").strip():
        return {
            "hook": (briefing.get("hook") or "").strip(),
            "hook_translations": _clean_tr(briefing.get("hook_translations")),
            "mission": (briefing.get("mission") or "").strip(),
            "mission_translations": _clean_tr(briefing.get("mission_translations")),
        }

    # ---- fallback: reuse the episode synopsis as the hook (already spoiler-safe, target lang) ----
    hook = (ep_syn or "").strip()
    return {
        "hook": hook,
        "hook_translations": _clean_tr(None),
        "mission": "",
        "mission_translations": _clean_tr(None),
    }


async def generate_world(
    language: str,
    level: str,
    genre: str = "daily_life",
    theme: str = "",
    episode_number: int = 1,
    total_episodes: int = 1,
    continuity_hint: str = "",
    style_bible: str = "",
    arc: Dict[str, Any] = None,
    prev_summary: str = "",
    _structural_retry: bool = False,
) -> Dict[str, Any]:
    """Generate one episode (world). For episode_number>1 it continues the series.

    `_structural_retry` is a private bound on the single structural regen (Part B): if dropping
    unfixable scenes would leave too few, we regenerate the episode ONCE with this set, so the
    drop loop can never recurse infinitely."""
    language = language.lower()
    level = level.upper()
    scene_count = SCENES_BY_LEVEL.get(level, 6)
    if genre not in GENRES:
        genre = "daily_life"

    client = get_async_openai()
    logger.info("[STORY-GEN] Generating %s/%s %s ep %d/%d (%d scenes)",
                language, level, genre, episode_number, total_episodes, scene_count)

    # Creative seed — only on EPISODE 1 (it defines the cast/setting; episodes 2..N
    # inherit them via continuity_hint + style_bible, so we must NOT re-seed them or
    # the character would drift mid-series). Random per series → breaks the "every
    # supernatural story is Luna in a forest" collapse.
    # When an arc is present it already fixes the cast/setting (the cast lock below),
    # so the random lead/setting nudge would only fight it — keep just the tone hint.
    seed = ""
    if episode_number <= 1:
        if arc and (arc.get("character") or {}).get("name"):
            seed = (
                f"Creative direction (inspiration, not literal text): "
                f"tone — {random.choice(_SEED_TONES)}."
            )
        else:
            seed = (
                f"Creative direction for THIS story (use as inspiration, not literal text): "
                f"tone — {random.choice(_SEED_TONES)}; setting — {random.choice(_SEED_SETTINGS)}; "
                f"the lead character is {random.choice(_SEED_LEADS)}."
            )

    # On episode 1, lock the cast/setting to what the SHOWRUNNER planned so the lead
    # the season was designed around actually plays the scenes (the per-episode writer
    # was inventing a different name). Episodes 2..N inherit it via style_bible/continuity.
    cast = ""
    if episode_number <= 1 and arc:
        ac = arc.get("character", {}) or {}
        brief1 = arc_episode_brief(arc, 1)
        if ac.get("name"):
            cast = (
                f"THIS EPISODE IS EPISODE 1 of a planned season — follow the plan EXACTLY so "
                f"the later episodes line up:\n"
                f"- Lead character — the one who TALKS TO the learner (do NOT rename/replace): "
                f"{ac.get('name')} — {ac.get('role', '')}. {ac.get('persona', '')} "
                f"(This character speaks the open.line/reply.line; the learner answers. The "
                f"character never uses their own name as a vocative and does not know the learner's name.)\n"
                f"- Season setting: {arc.get('setting', '')}\n"
                f"- The season's central mystery/goal (the WHOLE series is about THIS — do not "
                f"substitute a different object/topic): {arc.get('central_question', '')}\n"
                f"- What happens in THIS episode: {brief1.get('beat', '')}\n"
                f"- IMPORTANT: episode 1 only OPENS the mystery. Do NOT solve or resolve it here. "
                f"End on this cliffhanger and nothing more final: {brief1.get('hook', '')}\n"
                f"- The `title` must match this episode's subject (\"{brief1.get('title_en', '')}\"), "
                f"and stay on the season's central mystery — not a renamed variant of it."
            )
    user_prompt = _user_prompt(language, level, genre, scene_count, theme, seed=seed, cast=cast)
    user_prompt += _continuity_block(
        episode_number, total_episodes, continuity_hint, style_bible,
        arc=arc, prev_summary=prev_summary, language=language,
    )

    messages = [
        {"role": "system", "content": _system_prompt(language, level, scene_count, episode_number, total_episodes)},
        {"role": "user", "content": user_prompt},
    ]
    # Worlds with 7-language translations per scene are large, and longer episodes
    # (A1/A2=8, B1/B2=10 scenes) plus the per-episode student_briefing push the JSON
    # bigger still; too small a cap truncates it mid-string ("Unterminated string").
    # Give ample headroom (12000) AND retry once on a parse failure (the model
    # occasionally emits malformed JSON) so one bad generation doesn't kill the series.
    world = None
    last_err = None
    for attempt in range(2):
        resp = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.8 if attempt == 0 else 0.4,  # cooler on retry → more reliable JSON
            max_tokens=12000,
        )
        raw = resp.choices[0].message.content
        try:
            world = json.loads(raw)
            break
        except json.JSONDecodeError as e:
            last_err = e
            logger.warning("[STORY-GEN] JSON parse failed (attempt %d) for %s/%s %s ep %d: %s",
                           attempt + 1, language, level, genre, episode_number, e)
    if world is None:
        raise ValueError(f"Model returned unparseable JSON after retries: {last_err}")

    # Light validation + normalisation so the mobile app gets a stable shape.
    world["language"] = language
    world["level"] = level
    world["genre"] = world.get("genre", genre)

    # ---- TITLE language guarantee (deterministic, prompt-independent) ----
    # gpt-4o-mini sometimes writes `title` in the support language (e.g. Turkish)
    # instead of the target language, especially when target == English (then
    # title and title_en should be identical). Enforce it in code so it's 100% solid.
    title = (world.get("title") or "").strip()
    title_en = (world.get("title_en") or "").strip()
    if language == "english":
        # for English target, the localized title IS the English title
        world["title"] = title_en or title
        world["title_en"] = title_en or title
    elif title and title_en and _looks_non_target(title, language):
        # title drifted into another language → fall back to the English title
        # (better an English placeholder than the wrong language; admin can edit)
        logger.warning("[STORY-GEN] title '%s' not in target %s — using title_en", title, language)
        world["title"] = title_en

    scenes = world.get("scenes", [])
    if not scenes:
        raise ValueError("Model returned no scenes")
    # Mark the last scene as the boss/climax.
    for i, sc in enumerate(scenes):
        sc["fill"] = round((i) / max(1, scene_count), 3)
        sc["is_boss"] = (i == len(scenes) - 1)
        sc.pop("choices", None)  # chips removed — learner types their answer

    # VALIDATE + REPAIR scenes whose logic is provably broken (backwards goal, missing
    # distractors, help≠me). The generator's own self-check is unreliable, so we run a
    # cheap targeted repair pass — only on flagged scenes, concurrently, never fatal.
    bad = [i for i, sc in enumerate(scenes) if _scene_needs_repair(sc, language)]
    if bad:
        logger.info("[STORY-GEN] repairing %d/%d scene(s) ep %d", len(bad), len(scenes), episode_number)
        repaired = await asyncio.gather(
            *(validate_and_repair_scene(scenes[i], language, level) for i in bad),
            return_exceptions=True,
        )
        for idx, res in zip(bad, repaired):
            if isinstance(res, dict):
                scenes[idx] = res

    # ---- STRUCTURAL INVARIANT (Part B): drop-and-renumber (V2 only) ----
    # The repair pass is best-effort, so a scene can still ship structurally broken. This
    # deterministic sweep GUARANTEES 0 structural breakages in the output: any scene that STILL
    # trips a structural code (echo_question / goal_ask_after_char_asked / help_ne_me / empty_me)
    # is dropped. cold_recall is a SOFT target and must NEVER cause a drop (the scene is playable).
    if STORY_GEN_V2:
        kept, dropped = [], 0
        for sc in scenes:
            if scene_breakages(sc, language, check_recoverability=False):
                dropped += 1
                logger.warning("[STORY-GEN] dropping unfixable scene ep%d/%d: %r",
                               episode_number, total_episodes, sc.get("label"))
                continue
            kept.append(sc)

        if dropped:
            # rare safety net: if too few scenes survive, regenerate this episode ONCE.
            if len(kept) < 3 and not _structural_retry:
                logger.warning("[STORY-GEN] only %d clean scenes ep%d — one structural regen",
                               len(kept), episode_number)
                return await generate_world(
                    language, level, genre, theme, episode_number, total_episodes,
                    continuity_hint, style_bible, arc=arc, prev_summary=prev_summary,
                    _structural_retry=True,
                )
            scenes = kept
            # renumber labels ("Scene i of N · title"), re-fill, re-mark boss
            n = len(scenes)
            for i, sc in enumerate(scenes):
                sc["fill"] = round(i / max(1, n), 3)
                sc["is_boss"] = (i == n - 1)
                lbl = sc.get("label") or ""
                sc["label"] = re.sub(r"Scene\s+\d+\s+of\s+\d+", f"Scene {i + 1} of {n}", lbl) or lbl
            world["scenes"] = scenes

    world["scene_count"] = len(scenes)

    # ---- TAGLINE guarantee (short target-language hook for the lobby card) ----
    # Fall back to the world title if the model omitted/over-wrote it; never English
    # for a non-English target (the English description already lives in `description`).
    tagline = (world.get("tagline") or "").strip()
    if not tagline or _looks_non_target(tagline, language):
        tagline = world.get("title") or world.get("title_en") or ""
    world["tagline"] = tagline

    # ---- SYNOPSIS guarantee (2-3 sentence target-language back-cover summary) ----
    # Shown on the series detail screen so the learner understands what the story is
    # about before starting. Target language only (immersive). Falls back to tagline.
    synopsis = (world.get("synopsis") or "").strip()
    if not synopsis or _looks_non_target(synopsis, language):
        synopsis = tagline
    world["synopsis"] = synopsis

    # ---- EPISODE-LEVEL synopsis (per episode "what happens here", target language) ----
    # Distinct from the story synopsis above: this summarises THIS episode only. Shown
    # in-app per episode. Falls back to the story synopsis if missing/wrong-language.
    ep_syn = (world.get("episode_synopsis") or "").strip()
    if not ep_syn or _looks_non_target(ep_syn, language):
        ep_syn = synopsis
    world["episode_synopsis"] = ep_syn

    # ---- STUDENT BRIEFING guarantee (English study-aid modal shown pre-conversation) ----
    # The model produces it last (from the real scenes). If it's missing or malformed, derive
    # a minimal honest briefing from the scenes so the modal is NEVER empty.
    world["student_briefing"] = _ensure_student_briefing(world.get("student_briefing"), scenes, ep_syn)

    # NARR normalisation — `narr` is now an object {line, translations} (target language +
    # 7 translations), but older content / model slips may emit a bare string. Coerce every
    # scene's narr to the object shape so the mobile app can render target text + a UI-language
    # translation consistently.
    for sc in scenes:
        sc["narr"] = _normalize_narr(sc.get("narr"))

    # episode metadata
    is_finale = episode_number >= total_episodes
    world["episode_number"] = episode_number
    world["recap"] = world.get("recap") if episode_number > 1 else None
    # next_hook: model-provided for non-finale; else last scene narr line; null on finale
    if is_finale:
        world["next_hook"] = None
    else:
        last_narr = (scenes[-1].get("narr") or {}).get("line") if scenes else None
        world["next_hook"] = world.get("next_hook") or last_narr
    world["series_finale"] = is_finale
    # series-wide visual identity: episode 1 DEFINES it; episodes 2..N inherit the
    # passed-in style_bible verbatim (don't let the model re-translate/rewrite it,
    # which would drift the character look across covers).
    if episode_number > 1 and style_bible:
        world["style_bible"] = style_bible
    else:
        world["style_bible"] = world.get("style_bible") or style_bible or ""
    # episode title (target lang + English) — fall back to the world title
    world.setdefault("episode_title", world.get("title"))
    world.setdefault("episode_title_en", world.get("title_en"))

    logger.info("[STORY-GEN] ✓ ep %d/%d '%s' (%d scenes)%s",
                episode_number, total_episodes, world.get("title_en") or world.get("title"),
                len(scenes), " [FINALE]" if is_finale else "")
    return world


# ---------------------------------------------------------------------------
# SHOWRUNNER — plan the whole series arc up front (fixes inter-episode drift)
# ---------------------------------------------------------------------------
async def plan_series_arc(
    language: str,
    level: str,
    genre: str,
    total_episodes: int,
    theme: str = "",
    seed: str = "",
) -> Dict[str, Any]:
    """
    One cheap up-front call that designs the SEASON before any episode is written.

    Why: episodes were drifting (a library mystery became a concert by ep 2) because
    each episode was generated from only a thin one-line "hook" with no idea where the
    story was going. A serialized story needs a SHOWRUNNER: one central mystery/goal,
    a per-episode beat that escalates it, and a finale that pays it off. We generate
    that bible once, then feed each episode its own beat + the real previous beat, so
    the season reads as ONE story instead of five disconnected vignettes.

    Returns: {central_question, payoff, character{name,role,persona}, setting,
              episodes:[{n, title_en, beat, hook, resolves}]} — best-effort; on any
    failure returns {} and generation falls back to the old per-episode continuity.
    """
    language = language.lower()
    level = level.upper()
    lang_name = LANG_NAMES.get(language, language.title())
    client = get_async_openai()
    seed_line = f"\n{seed}" if seed else ""
    theme_line = f"\nTheme hint: {theme}" if theme else ""

    system = (
        "You are a TV-style showrunner designing a short serialized season for a "
        f"language-learning story game that teaches {lang_name} at CEFR {level}. "
        "Your ONE job: make the season feel like a single continuous story with a "
        "spine — a central question raised in episode 1, escalated each episode, and "
        "resolved in the finale. Each episode must clearly CONTINUE the previous one "
        "(pick up its hook), never reset to a new unrelated plot. Keep it wholesome "
        "and teen-safe. The cast and setting are FIXED for the whole season. "
        "IMPORTANT framing: the LEAD CHARACTER is the person who TALKS TO the learner "
        "throughout the game — the learner is the lead's companion/confidant who helps "
        "them. So the central question is the LEAD's goal, and the lead speaks to the "
        "learner about it. The lead does not know the learner's name."
    )
    user = f"""Design a {total_episodes}-episode {genre} season.{theme_line}{seed_line}

WORLD FOR THIS GENRE — set the story HERE (do not drift to a school unless the genre is
school_life): {_genre_world(genre)}

ORIGINALITY (critical — stories must NOT feel same-y):
- Invent a fresh, culturally-fitting lead with a SPECIFIC name (NOT Luna/Max/Aria/Nova/Leo,
  NOT a "silver-haired magical forest guide").
- VARY THE LEAD'S AGE AND OCCUPATION to fit the genre — do NOT default to "a high school
  student" or a teenager unless the genre is school_life. Adults, professionals, elders,
  children — pick what fits THIS genre's world above.
- Two different stories must feel clearly different in setting, cast, and tone.

Return STRICT JSON:
{{
  "central_question": "the ONE dramatic question that drives the whole season (English) — raised in ep1, answered in the finale",
  "payoff": "how it resolves in the finale (English, 1 sentence)",
  "character": {{ "name": "...", "role": "...", "persona": "1 sentence" }},
  "setting": "the fixed season setting (English, for the cover artist)",
  "episodes": [
    {{
      "n": 1,
      "title_en": "episode 1 title (English)",
      "beat": "what HAPPENS this episode and how it moves the central question forward (English, 1-2 sentences)",
      "hook": "the cliffhanger this episode ends on that pulls into the next (English; for the finale set this to how it resolves)",
      "resolves": "what thread from the PREVIOUS episode's hook this one picks up and resolves/escalates (English; null for ep1)"
    }}
    // ... exactly {total_episodes} episodes; episode {total_episodes} is the finale and resolves the central_question
  ]
}}"""

    try:
        resp = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={"type": "json_object"},
            temperature=0.8,
            max_tokens=2000,
        )
        arc = json.loads(resp.choices[0].message.content)
        eps = arc.get("episodes") or []
        if not isinstance(eps, list) or len(eps) < total_episodes:
            logger.warning("[STORY-GEN] arc has %d/%d episodes — using anyway", len(eps), total_episodes)
        logger.info("[STORY-GEN] ✓ planned season arc: '%s' (%d beats)",
                    arc.get("central_question", "")[:60], len(eps))
        return arc
    except Exception as e:  # noqa: BLE001 — arc is an enhancement, never fatal
        logger.warning("[STORY-GEN] arc planning failed (%s) — falling back to per-episode continuity", e)
        return {}


def arc_episode_brief(arc: Dict[str, Any], episode_number: int) -> Dict[str, Any]:
    """Pull one episode's beat from a planned arc (or {} if absent)."""
    if not arc:
        return {}
    for ep in arc.get("episodes", []):
        if ep.get("n") == episode_number:
            return ep
    eps = arc.get("episodes", [])
    return eps[episode_number - 1] if 0 < episode_number <= len(eps) else {}


# ---------------------------------------------------------------------------
# VALIDATOR / REPAIR — guarantee the per-scene logic the generator self-check misses
# ---------------------------------------------------------------------------
def _scene_needs_repair(scene: Dict[str, Any], language: str = "english") -> bool:
    """Cheap, deterministic pre-screen — catches the failures we can detect without
    an LLM, so we only pay for a repair call on scenes that actually need it.

    Under STORY_GEN_V2 this uses the full deterministic detector (structural defects +
    optional cold-recall). With V2 off it is byte-identical to the legacy gate (empty
    `me` / help!=me only)."""
    if not STORY_GEN_V2:
        # ---- legacy (byte-identical rollback) ----
        me = (scene.get("me") or "").strip()
        if not me:
            return True
        if (scene.get("help", {}) or {}).get("suggestion", "").strip() != me:
            return True
        return False
    return bool(scene_breakages(scene, language, check_recoverability=RECOVERABILITY_GATE))


_SUPPORT_LANGS = ["english", "turkish", "spanish", "french", "german", "dutch", "portuguese"]

# Recoverability rule appended to BOTH repair passes (the #1 cause of beginners getting stuck).
_REPAIR_RECOVERABILITY = (
    "RECOVERABILITY (most important for low levels): the player must be able to PRODUCE `me` from "
    "open.line ALONE — they should only work out HOW to say it, never guess WHAT to supply from "
    "memory. Put any content word the player needs INTO open.line (let the character name the "
    "object/place/person), OR make `me` a closed reply (yes/no, or a choice between options the "
    "character stated).\n"
)

# Stubborn-pass instruction — MANDATORY reframe (the exact move that cleared 47/66 stubborn scenes
# in the migration), now REQUIRED rather than permitted so a structurally-clean reframe is forced.
_REPAIR_STUBBORN = (
    "The previous rewrite still failed structurally. You MUST now rewrite open.line as a STATEMENT "
    "or a REQUEST that does NOT end with '?'. The character states a situation or asks the player to "
    "do something, and hands the turn over; the player's `me` is then a natural reply. Example: "
    "open.line 'I can't find the key.' (statement) -> me 'Where could it be?'. open.line MUST NOT be "
    "a question. Keep it short and at the same level, and keep help.suggestion identical to me.\n"
)


def _repair_system_prompt(lang_name: str, level: str, *, stubborn: bool) -> str:
    """The repair editor's system prompt. Shared by both passes; the stubborn pass adds the
    statement-reframe instruction on top."""
    return (
        f"You are a strict editor for a {lang_name} ({level}) language-learning story "
        "game. You receive ONE scene and rewrite it so it obeys these rules EXACTLY, "
        f"keeping every in-game line in {lang_name} and the difficulty at {level} "
        "(short, high-frequency, winnable on the first try):\n"
        "1. `goal` is what THE PLAYER must say/do in reply to open.line — never a "
        "restatement of what the character already did. If open.line already asks a "
        "question, the goal is to ANSWER it — NEVER to ask the same thing again.\n"
        "2. open.line → me → reply.line must read as one natural mini-dialogue: the "
        "character asks/invites (open), the player replies (me), the character reacts "
        "and nudges the story on (reply). NEVER answer a question with the same question.\n"
        "3. `help.suggestion` MUST be identical to `me`.\n"
        + _REPAIR_RECOVERABILITY
        + (_REPAIR_STUBBORN if stubborn else "")
        + "4. If you change ANY of open.line / me / reply.line / help.suggestion, you MUST "
        "regenerate that field's `translations` so all of these keys are present and correct: "
        + ", ".join(_SUPPORT_LANGS) + ".\n"
        "Keep the same story intent, characters and vocab. Only fix what breaks the rules."
    )


def _finalize_repair(original: Dict[str, Any], fixed: Dict[str, Any], language: str) -> Optional[Dict[str, Any]]:
    """Merge engine fields + fully validate a candidate repair. Returns the accepted scene,
    or None if it is not strictly better (caller then keeps the original / tries next pass)."""
    if not isinstance(fixed, dict):
        return None
    # preserve engine-set fields the editor must not touch
    for k in ("fill", "is_boss"):
        if k in original:
            fixed[k] = original[k]
    fixed.pop("choices", None)
    me = (fixed.get("me") or "").strip()
    if not me:
        return None
    if ((fixed.get("help") or {}).get("suggestion") or "").strip() != me:
        return None
    # no structural breakage may remain (cold-recall gated to match the repair pre-screen)
    if scene_breakages(fixed, language, check_recoverability=RECOVERABILITY_GATE):
        return None
    # translations must be intact (all 7 keys, non-empty) for any line the player reads
    for fld in ("open", "reply", "help"):
        tr = (fixed.get(fld) or {}).get("translations") or {}
        if any(not (tr.get(k) or "").strip() for k in _SUPPORT_LANGS):
            return None
    return fixed


def _finalize_stubborn(original: Dict[str, Any], fixed: Dict[str, Any], language: str) -> Optional[Dict[str, Any]]:
    """Acceptance for the MANDATORY-reframe pass: STRUCTURAL only (cold_recall is a soft target and
    must not reject a structurally-clean reframe). Forces help.suggestion = me in code (don't trust
    the model for that one field), and rejects if open.line is still a question."""
    if not isinstance(fixed, dict):
        return None
    for k in ("fill", "is_boss"):
        if k in original:
            fixed[k] = original[k]
    fixed.pop("choices", None)
    me = (fixed.get("me") or "").strip()
    if not me:
        return None
    # the reframe MUST have turned open.line into a non-question
    if ((fixed.get("open") or {}).get("line") or "").strip().endswith("?"):
        return None
    # force help.suggestion == me (and mirror its translations from `me`'s carrier if present)
    help_obj = fixed.get("help")
    if not isinstance(help_obj, dict):
        help_obj = {}
        fixed["help"] = help_obj
    help_obj["suggestion"] = me
    # structural-only gate (recoverability explicitly OFF here)
    if scene_breakages(fixed, language, check_recoverability=False):
        return None
    # translations still required for the lines the player reads
    for fld in ("open", "reply", "help"):
        tr = (fixed.get(fld) or {}).get("translations") or {}
        if any(not (tr.get(k) or "").strip() for k in _SUPPORT_LANGS):
            return None
    return fixed


async def validate_and_repair_scene(
    scene: Dict[str, Any], language: str, level: str,
) -> Dict[str, Any]:
    """
    Re-author one scene so it obeys the hard logic rules the generator's own self-check is
    unreliable about (gpt-4o-mini wrote goals like "ask for the clue" right after the character
    already asked). Under STORY_GEN_V2 this is a TWO-PASS repair: pass 1 (temp 0.3) fixes
    goal-direction + recoverability; if the result is still broken, pass 2 (stubborn, temp 0.5)
    is allowed to reframe open.line from a question into a statement/request. Each pass is fully
    validated by `_finalize_repair`; on any failure we keep the ORIGINAL scene (never block
    generation, never write a worse scene). With V2 off, behaves like the legacy single pass.
    """
    lang_name = LANG_NAMES.get(language.lower(), language.title())
    client = get_async_openai()

    def _user_msg(sc: Dict[str, Any]) -> str:
        # strip engine fields from what the editor sees; re-attached in _finalize_repair
        payload = {k: v for k, v in sc.items() if k not in ("fill", "is_boss")}
        return (
            "Rewrite this scene to satisfy all rules. Return STRICT JSON with the SAME shape "
            "(label, goal, goal_en, open{line,translations}, me, reply{line,"
            "translations}, help{suggestion,translations,why}, vocab, narr). Keep all "
            "translation keys.\n\nSCENE:\n" + json.dumps(payload, ensure_ascii=False)
        )

    async def _one_pass(stubborn: bool) -> Optional[Dict[str, Any]]:
        system = _repair_system_prompt(lang_name, level, stubborn=stubborn)
        resp = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": _user_msg(scene)}],
            response_format={"type": "json_object"},
            temperature=0.5 if stubborn else 0.3,
            max_tokens=1600,
        )
        parsed = json.loads(resp.choices[0].message.content)
        # pass 2 (stubborn) accepts on STRUCTURAL grounds only; pass 1 keeps full (incl. recoverability)
        if stubborn:
            return _finalize_stubborn(scene, parsed, language)
        return _finalize_repair(scene, parsed, language)

    try:
        if not STORY_GEN_V2:
            # ---- legacy single pass (byte-identical acceptance: usable `me` only) ----
            system = (
                f"You are a strict editor for a {lang_name} ({level}) language-learning story "
                "game. You receive ONE scene and rewrite it so it obeys these rules EXACTLY, "
                f"keeping every in-game line in {lang_name} and the difficulty at {level} "
                "(short, high-frequency, winnable on the first try):\n"
                "1. `goal` is what THE PLAYER must say/do in reply to open.line — never a "
                "restatement of what the character already did. If open.line already asks a "
                "question, the goal is to ANSWER it.\n"
                "2. open.line → me → reply.line must read as one natural mini-dialogue: the "
                "character asks/invites (open), the player replies (me), the character reacts "
                "and nudges the story on (reply).\n"
                "3. `help.suggestion` MUST be identical to `me`.\n"
                "Keep the same story intent, characters and vocab. Only fix what breaks the rules."
            )
            user = (
                "Rewrite this scene to satisfy all rules. Return STRICT JSON with the SAME shape "
                "(label, goal, goal_en, open{line,translations}, me, reply{line,"
                "translations}, help{suggestion,translations,why}, vocab, narr). Keep all "
                "translation keys.\n\nSCENE:\n" + json.dumps(scene, ensure_ascii=False)
            )
            resp = await client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=1500,
            )
            fixed = json.loads(resp.choices[0].message.content)
            for k in ("fill", "is_boss"):
                if k in scene:
                    fixed[k] = scene[k]
            fixed.pop("choices", None)
            if (fixed.get("me") or "").strip():
                return fixed
            return scene

        # ---- V2 two-pass repair ----
        # pass 1 (normal): fixes goal-direction + recoverability.
        result = await _one_pass(stubborn=False)
        if result is not None:
            return result
        # pass 2 (mandatory reframe): ONLY escalate when a STRUCTURAL code tripped. A scene whose
        # only problem is cold_recall is still playable — never escalate it to a reframe.
        if scene_breakages(scene, language, check_recoverability=False):
            result = await _one_pass(stubborn=True)
            if result is not None:
                return result
    except Exception as e:  # noqa: BLE001 — repair is best-effort
        logger.warning("[STORY-GEN] scene repair failed (%s) — keeping original", e)
    return scene
