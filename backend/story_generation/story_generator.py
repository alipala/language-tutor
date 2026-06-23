"""
Story Worlds generator — turns (language, level, genre) into a complete,
playable story world using gpt-4o-mini (cheap, what news generation uses).

A world = setting + character + N scenes. Each scene is a voice quest:
in-story goal, the model "solving" line, a help suggestion, target vocab,
multi-language translations, and a cliffhanger into the next scene.

Mirrors backend/news_generation/news_generator.py: shared async OpenAI client,
gpt-4o-mini, response_format=json_object. No multiplayer — single-player only.
"""

import json
import logging
import random
from typing import Any, Dict, List

from openai_client import get_async_openai

logger = logging.getLogger(__name__)

MODEL = "gpt-4o-mini"  # cost-efficient, same as news generation

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
# Tight one-sitting band (4-7 min/episode). Depth scales via DIFFICULTY, not count —
# long episodes never end and kill the "one more episode" loop.
SCENES_BY_LEVEL: Dict[str, int] = {
    "A1": 5, "A2": 5, "B1": 6, "B2": 6, "C1": 7, "C2": 7,
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


def _system_prompt(language: str, level: str, scene_count: int) -> str:
    lang_name = LANG_NAMES.get(language.lower(), language.title())
    # In-target-language example so the model anchors on the RIGHT language
    # (using a Dutch example when target was English caused it to drift).
    open_ex, me_ex = _example_lines(language.lower())
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

HARD RULES:
- All `line`, `me`, `goal`, `suggestion` fields that are spoken in-game must be in {lang_name}.
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
- SELF-CHECK each scene before finalising: does open.line → me → reply.line read as one
  natural mini-dialogue, does `me` achieve `goal`, and is `help.suggestion` == `me`?
  If any answer is no, REWRITE the scene.
- Difficulty MUST match {level}: A1 = single short survival phrases; B1 = connected
  talk, the character pushes back and asks for reasons; C1+ = nuanced persuasion.
- Each scene's `me` is the SHORTEST natural utterance that achieves the goal — it is
  the model answer that unlocks the scene.
- `translations` must provide the {lang_name} line rendered into EACH support language.
- `title` and the story content are in {lang_name}; `title_en` and `description` are in English for the admin.
- Keep it wholesome and safe (suitable for teens). No violence, romance is gentle.
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


def _user_prompt(language: str, level: str, genre: str, scene_count: int, theme: str = "", seed: str = "") -> str:
    lang_name = LANG_NAMES.get(language.lower(), language.title())
    theme_line = f"\nTheme hint: {theme}" if theme else ""
    seed_line = f"\n{seed}" if seed else ""
    return f"""Create one {genre} story world that teaches {lang_name}, for level {level},
with exactly {scene_count} scenes. ALL in-game spoken lines must be in {lang_name}.{theme_line}{seed_line}

ORIGINALITY (important): invent a FRESH character and setting. Do NOT default to
overused fantasy/AI names like Luna, Max, Lily, Aria, Nova, Leo, Sam, or Mia, and
avoid the generic "silver-haired magical forest guide" trope. Give the lead a
specific, ordinary, culturally-fitting name and a concrete, non-cliché setting.
Two stories of the same genre should feel clearly different from each other.

Return JSON with this EXACT shape:
{{
  "title": "evocative world title written in {lang_name} (the TARGET language — never any other language). If the target language is English, this is in English.",
  "title_en": "the same title in English for admin reference (identical to title when the target language is English)",
  "description": "one-line hook in English",
  "genre": "{genre}",
  "setting": "where it takes place (English, for the cover artist)",
  "character": {{ "name": "...", "role": "e.g. the vendor", "persona": "1 sentence" }},
  "style_bible": "the SERIES-wide visual identity for the cover artist (English): the lead character's exact appearance (age, hair, clothing, distinguishing features), the colour palette, and the art style — concrete enough that every episode cover shows the SAME character and look. No text.",
  "cover_prompt": "a rich, concrete visual description of THIS EPISODE's cover moment for an illustrator — feature the lead character in a scene that captures this episode's hook, cinematic, warm lighting, no text",
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
      "narr": "a one-line cliffhanger bridging to the next scene (English, italic story text)"
    }}
    // ... {scene_count} scenes total, final one resolves the story
  ]
}}"""


def _continuity_block(episode_number: int, total_episodes: int, continuity_hint: str, style_bible: str = "") -> str:
    """Extra prompt for episodes 2..N — keeps the season coherent."""
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
    return f"""

THIS IS EPISODE {episode_number} OF {total_episodes} in an ongoing series.
Previously: {continuity_hint}
Continue the SAME characters and world. You MUST:
- open with a short \"recap\" (English, 1 sentence, \"Last time: …\")
- pick up from where the previous episode left off (resolve or escalate its hook)
{style_rule}
- cover_prompt must show the SAME lead character (per style_bible) in THIS episode's new moment
- {finale_rule}
Add these top-level fields to the JSON: "recap" (string|null), "next_hook" (string|null)."""


async def generate_world(
    language: str,
    level: str,
    genre: str = "daily_life",
    theme: str = "",
    episode_number: int = 1,
    total_episodes: int = 1,
    continuity_hint: str = "",
    style_bible: str = "",
) -> Dict[str, Any]:
    """Generate one episode (world). For episode_number>1 it continues the series."""
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
    seed = ""
    if episode_number <= 1:
        seed = (
            f"Creative direction for THIS story (use as inspiration, not literal text): "
            f"tone — {random.choice(_SEED_TONES)}; setting — {random.choice(_SEED_SETTINGS)}; "
            f"the lead character is {random.choice(_SEED_LEADS)}."
        )

    user_prompt = _user_prompt(language, level, genre, scene_count, theme, seed=seed)
    user_prompt += _continuity_block(episode_number, total_episodes, continuity_hint, style_bible)

    resp = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": _system_prompt(language, level, scene_count)},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.8,  # a little spice for varied stories
        max_tokens=4000,
    )

    raw = resp.choices[0].message.content
    world = json.loads(raw)

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
    world["scene_count"] = len(scenes)

    # episode metadata
    is_finale = episode_number >= total_episodes
    world["episode_number"] = episode_number
    world["recap"] = world.get("recap") if episode_number > 1 else None
    # next_hook: model-provided for non-finale; else last scene narr; null on finale
    if is_finale:
        world["next_hook"] = None
    else:
        world["next_hook"] = world.get("next_hook") or (scenes[-1].get("narr") if scenes else None)
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
