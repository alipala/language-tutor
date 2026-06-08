"""
Profile Story V1 — services package.

Composes existing services (lifetime_progress, recent_performance,
calculate_milestones, build_daily_breakdown) and adds:
  - language_normalizer: ISO ↔ English-name canonicalization
  - timezone_resolver:   user.timezone → notif_prefs → daily_stats → UTC
  - confidence_ladder:   enhanced_analysis → journey_state → empty
  - rhythm_streak:       28-day strip + TZ-correct streak (new path only)
  - memory_mapper:       deterministic moment generation
  - proof_builder:       de-rainbowed semantic proof block

All read-only. No DB mutations. Feeds GET /api/profile/story.
"""
