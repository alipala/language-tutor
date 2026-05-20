# Phase E — Pre-Index Baseline
**Captured:** 2026-05-21 | Before adding Phase E indexes

## Existing indexes (pre-Phase E)

| Collection | Existing indexes |
|---|---|
| conversation_sessions | `_id`, `(user_id,created_at desc)` ✓ already, `text_search` |
| flashcards | `_id` only |
| flashcard_sets | `_id` only |
| learning_plans | `_id`, `user_id`, `(user_id,created_at desc)` ✓ already, `id` unique |
| realtime_usage_logs | `_id` only |

## Query plan pre-Phase E

```
db.conversation_sessions.find({user_id: "6a0dee29cdf28f63a0b35aab"})
  .sort({created_at:-1}).limit(50).explain()
  → LIMIT → FETCH → IXSCAN  (already indexed — existing index used)
  totalDocsExamined: 50, nReturned: 50, executionTimeMillis: 0
```

Note: `(user_id, created_at desc)` already exists on `conversation_sessions`
and `learning_plans` from a previous migration. Phase E adds the remaining
missing indexes.

## Per-user max document counts

| Collection | Max count (user) | Safe bound applied |
|---|---|---|
| conversation_sessions | 500 (test), 67 (real) | 2000 |
| flashcards | 2000 (test), 210 (real) | 5000 |
| flashcard_sets | 46 (real) | 500 |
| learning_plans | 10 (real) | 200 |
| realtime_usage_logs | 227 total (null user_id) | 1000 |

No real user exceeds any planned bound. Safe to apply.

## Unbounded to_list(None) calls in production routes

| File | Line | Collection | Bound applied |
|---|---|---|---|
| progress_routes.py | 553 | flashcard_sets | 500 |
| progress_routes.py | 567 | flashcards (by id list) | 5000 |
| progress_routes.py | 619 | learning_plans | 200 |
| progress_routes.py | 1329 | conversation_sessions | 2000 |
| progress_routes.py | 1341 | learning_plans | 200 |
| progress_routes.py | 1892 | daily_stats | 1000 |
| flashcard_routes.py | 85 | flashcard_sets | 500 |
| flashcard_routes.py | 108 | flashcards | 5000 |
| flashcard_routes.py | 188 | flashcards | 5000 |
| flashcard_routes.py | 407 | flashcards | 5000 |
