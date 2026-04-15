# Vector DB (Pinecone) Deployment Guide for Railway

## Overview

The real-time embedding system enables TaalCoach semantic search for **all users** (including new users) from their **first conversation**. Embeddings are generated in the background automatically whenever a user completes a conversation.

## Architecture

### NO Additional Railway Service Needed! ✅

The vector embedding system runs within the **existing `web` service** as background tasks:

```
User completes conversation
  ↓
Save to MongoDB (instant response to user)
  ↓
Background task: Embed conversation to Pinecone (~200ms)
  ↓
TaalCoach can now semantic search this conversation
```

**Existing 3 Railway Services (unchanged):**
1. **web** - Main API + Real-time embeddings (NEW)
2. **scheduler** - Challenge pool replenishment
3. **news** - Daily news generation

## Railway Environment Variables

### Required for `web` Service:

Add this single environment variable to enable vector search:

```bash
PINECONE_API_KEY=pcsk_J1tv3_QRxKVi52sXNsj4JhmrKM7v1T4k4Taqoqh9uf5NxF4QVVQs5pX1bCAWs3hYA1Nz9
```

**Important:**
- `OPENAI_API_KEY` is already configured (reused for embeddings)
- If `PINECONE_API_KEY` is not set, the system gracefully degrades (semantic search disabled, TaalCoach still works)

### How to Add in Railway:

1. Go to Railway dashboard → Select **web** service
2. Click **Variables** tab
3. Click **+ New Variable**
4. Add:
   ```
   PINECONE_API_KEY = pcsk_J1tv3_QRxKVi52sXNsj4JhmrKM7v1T4k4Taqoqh9uf5NxF4QVVQs5pX1bCAWs3hYA1Nz9
   ```
5. Click **Deploy** (automatic redeploy)

## What Happens After Deployment

### For Existing Users (13 production users):
- ✅ Already embedded (323 vectors in Pinecone)
- ✅ Semantic search works immediately
- ✅ New conversations auto-embed in background

### For New Users:
- ✅ **First conversation** → Auto-embeds in background (~200ms)
- ✅ Semantic search works from their **second TaalCoach query**
- ✅ Every subsequent conversation auto-embeds

## Performance Impact

**Real-time embedding overhead:**
- OpenAI embedding API call: ~150-200ms
- Pinecone upsert: ~50ms
- **Total:** ~200-250ms added to background task (user doesn't wait)

**No impact on user experience:**
- User receives instant response (MongoDB save only)
- Embedding happens AFTER response is sent
- Non-blocking, non-fatal (app continues if embedding fails)

## Cost Analysis

**Current usage (13 users, 323 conversations):**
- Embeddings: $0.00 (free tier: $0.02/1M tokens, 323 conversations ≈ 50K tokens)
- Pinecone storage: $0.00 (free tier: 2GB, current: ~1MB)

**Projected at 300 users:**
- Embeddings: ~$0.50/month (25M tokens at $0.02/1M)
- Pinecone storage: $0.00 (free tier covers up to 300 users)

**Total: $0-1/month** (stays within free tiers)

## Monitoring & Logs

### Success Logs:
```
[VECTOR_EMBED] 🚀 Scheduled embedding for session 674abc123...
[VECTOR_EMBED_BG] ✅ Embedded conversation 674abc123 for user 69962fc9...
```

### Disabled Logs (if PINECONE_API_KEY not set):
```
⚠️  Pinecone vector DB is DISABLED (PINECONE_API_KEY or OPENAI_API_KEY not set)
⚠️  TaalCoach will work without semantic search capability
[VECTOR_EMBED_BG] ⏭️  Skipped embedding (Pinecone disabled or failed)
```

### Error Logs (non-fatal):
```
[VECTOR_EMBED_BG] ❌ Failed to embed conversation 674abc123: <error message>
```

**All errors are non-fatal** - the app continues to work, just without semantic search for that conversation.

## Testing After Deployment

### 1. Check Railway Logs:
```
# After deploying, check Railway logs for:
✅ Pinecone vector DB is ENABLED
✅ Connected to existing Pinecone index: taalcoach-semantic-search
📊 Index stats: 323 vectors, 1536 dimensions
```

### 2. Test with New User:
1. Create new user account
2. Complete 1 conversation (any language/level)
3. Check Railway logs for:
   ```
   [VECTOR_EMBED] 🚀 Scheduled embedding for NEW session <id>
   [VECTOR_EMBED_BG] ✅ Embedded conversation <id> for user <user_id>
   ```
4. Ask TaalCoach: "What did we talk about?" (should return relevant answer)

### 3. Test with Existing User:
1. Login as `mytacoai1@proton.me`
2. Ask TaalCoach: "What topics have I practiced?"
3. Should return semantic search results from past conversations

## Rollback Plan

If vector search causes issues:

### Option 1: Disable Pinecone (instant)
1. Go to Railway → **web** service → **Variables**
2. Delete `PINECONE_API_KEY` variable
3. Redeploy

**Result:** TaalCoach works without semantic search (MongoDB queries only)

### Option 2: Revert Code (rollback)
```bash
# Locally, revert to previous commit before vector embedding
git checkout <previous-commit-hash>
git push origin feature/improve-taalcoach --force

# Railway auto-deploys reverted code
```

## Optional: Batch Embedding for Historical Data

If you want to embed **all** historical conversations for existing users:

```bash
# Run locally (already done once):
python3 embed_user_data.py

# Or for specific user:
python3 embed_user_data.py --user-id <user_id>

# Or for recent data only:
python3 embed_user_data.py --since-date 2026-04-01
```

**Note:** This is optional - real-time embedding handles new conversations automatically.

## Support & Troubleshooting

### Issue: Embedding fails for all new conversations
**Solution:**
1. Check Railway logs for Pinecone initialization errors
2. Verify `PINECONE_API_KEY` is set correctly
3. Check Pinecone dashboard (pinecone.io) for API key validity

### Issue: Semantic search returns no results
**Possible causes:**
1. Conversations not yet embedded (check logs for successful embeddings)
2. User has no conversations yet (new user)
3. Query doesn't match conversation content (semantic mismatch)

**Debug:**
```python
# Check Pinecone index stats in Railway logs:
📊 Index stats: X vectors, 1536 dimensions

# Should increase after each new conversation
```

### Issue: Performance degradation
**Check:**
- OpenAI API rate limits (unlikely at current scale)
- Pinecone serverless cold starts (first request after idle)
- Network latency Railway → AWS us-east-1 (where Pinecone is hosted)

**Solution:** Both services are serverless and auto-scale, no manual intervention needed.

## Summary

✅ **No new Railway service needed** - runs in existing `web` service
✅ **One environment variable** - `PINECONE_API_KEY`
✅ **Graceful degradation** - works without Pinecone if not configured
✅ **Zero user impact** - embeddings happen in background
✅ **Low cost** - $0-1/month for 300 users
✅ **Instant rollback** - just delete environment variable

Ready to deploy! 🚀
