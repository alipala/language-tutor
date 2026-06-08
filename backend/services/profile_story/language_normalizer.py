"""
Language normalization for PROFILE_STORY_V1.

Production data stores language as a mix of ISO codes (`en`, `nl`, `de`, …)
and English names (`english`, `dutch`, `german`, …). `users.stats.lifetime.by_language`
only keys by English name; `conversation_sessions.language` and `challenge_sessions.language`
use both inconsistently — even within the same user.

This is the one place we map raw → canonical for the new Profile Story path.
Read-only. Never written back to the DB.
"""

from typing import Optional, TypedDict


class CanonicalLanguage(TypedDict):
    code: str  # ISO 639-1, lowercase
    name: str  # English name, lowercase


_ISO_TO_NAME = {
    "en": "english",
    "nl": "dutch",
    "es": "spanish",
    "fr": "french",
    "de": "german",
    "pt": "portuguese",
    "it": "italian",
    "tr": "turkish",
}

_NAME_TO_ISO = {v: k for k, v in _ISO_TO_NAME.items()}


def normalize_language(raw: Optional[str]) -> Optional[CanonicalLanguage]:
    """
    Resolve any raw language string to {code, name}.

    - ISO code (`en`)        → {code:"en", name:"english"}
    - English name (`english`) → {code:"en", name:"english"}
    - Unknown               → {code: raw_lower, name: titleCase(raw)} — safe pass-through
    - Empty / None          → None  (caller skips)
    """
    if raw is None:
        return None
    s = str(raw).strip().lower()
    if not s:
        return None

    if s in _ISO_TO_NAME:
        return {"code": s, "name": _ISO_TO_NAME[s]}
    if s in _NAME_TO_ISO:
        return {"code": _NAME_TO_ISO[s], "name": s}

    # Unknown — pass through with safe defaults; UI falls back to globe.
    return {"code": s, "name": s.capitalize()}


def canonical_name(raw: Optional[str]) -> Optional[str]:
    """Return the English-name form (matches users.stats.lifetime.by_language keys), or None."""
    c = normalize_language(raw)
    return c["name"] if c else None


def canonical_code(raw: Optional[str]) -> Optional[str]:
    """Return the ISO code form (used in API responses), or None."""
    c = normalize_language(raw)
    return c["code"] if c else None


def language_match_filter(raw: Optional[str]) -> list[str]:
    """
    Given any language input, return the list of raw strings that should be matched in
    Mongo queries to capture activity stored under either spelling.

    Example: normalize "nl" → ["nl", "dutch"]; normalize "italian" → ["it", "italian"].
    Unknown languages return just the lowered input.
    Empty/None returns [].
    """
    c = normalize_language(raw)
    if not c:
        return []
    # Capture both spellings (ISO + English-name) when both exist.
    candidates = {c["code"], c["name"]}
    return sorted(candidates)
