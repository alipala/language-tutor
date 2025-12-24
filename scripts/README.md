# Challenge Generation Scripts

This directory contains scripts for managing and generating high-quality language learning challenges.

## Quick Access

📖 **New User?** Start here: [QUICK_START.md](./QUICK_START.md)

📚 **Detailed Guide**: [CHALLENGE_GENERATION_GUIDE.md](./CHALLENGE_GENERATION_GUIDE.md)

📊 **Analysis Report**: [CHALLENGE_QUALITY_ANALYSIS_SUMMARY.md](./CHALLENGE_QUALITY_ANALYSIS_SUMMARY.md)

## Scripts Overview

### 1. analyze_challenge_quality.py
**Purpose**: Analyze existing challenges for quality issues

**Usage**:
```bash
python analyze_challenge_quality.py
python analyze_challenge_quality.py --collection reference_challenges
```

**What it checks**:
- Answer position bias
- Language field coverage
- CEFR level distribution
- Sample challenge quality

### 2. delete_all_challenges.py
**Purpose**: Safely delete challenges from database

**Usage**:
```bash
# Preview what would be deleted
python delete_all_challenges.py --dry-run

# Actually delete (requires confirmation)
python delete_all_challenges.py --confirm

# Delete specific collection only
python delete_all_challenges.py --confirm --collection reference_challenges
```

**Safety features**:
- Dry-run mode
- Requires typing 'DELETE' to confirm
- Shows statistics before deletion
- Verifies deletion after completion

### 3. generate_reference_challenges_improved.py
**Purpose**: Generate high-quality challenges using improved AI

**Usage**:
```bash
# English only (recommended first)
python generate_reference_challenges_improved.py --language english --challenges-per-type 50

# All languages
python generate_reference_challenges_improved.py --all-languages --challenges-per-type 50

# Specific level
python generate_reference_challenges_improved.py --language spanish --level B1 --challenges-per-type 50
```

**Features**:
- Detailed CEFR level guidelines
- Answer randomization
- Quality validation
- Progress tracking
- Error handling

## Typical Workflow

```bash
# 1. Analyze current state
python analyze_challenge_quality.py

# 2. Delete old challenges
python delete_all_challenges.py --dry-run
python delete_all_challenges.py --confirm

# 3. Generate new challenges (English first)
python generate_reference_challenges_improved.py --language english --challenges-per-type 50

# 4. Verify quality
python analyze_challenge_quality.py --collection reference_challenges

# 5. Generate other languages
python generate_reference_challenges_improved.py --all-languages --challenges-per-type 50
```

## Documentation Files

- **QUICK_START.md**: Fast track guide (TL;DR)
- **CHALLENGE_GENERATION_GUIDE.md**: Comprehensive documentation
- **CHALLENGE_QUALITY_ANALYSIS_SUMMARY.md**: Problem analysis and solutions
- **README.md**: This file

## Configuration

### Environment Variables

Set in `.env` file:
```bash
MONGODB_URL=your_mongodb_connection_string
OPENAI_API_KEY=your_openai_api_key
GPT_MODEL=gpt-4o  # or gpt-4.5 when available
```

### Cost Control

Adjust challenges per type to control costs:
```bash
# Fewer challenges for testing
python generate_reference_challenges_improved.py --language english --challenges-per-type 10

# Production volume
python generate_reference_challenges_improved.py --language english --challenges-per-type 50
```

## Troubleshooting

### "No module named 'challenge_generator_improved'"

Make sure you're running from the `scripts/` directory and the backend is in your path.

### "Rate limit exceeded"

The scripts include delays between batches. If you still hit limits:
1. Increase the delay in the script
2. Run in smaller batches
3. Check your OpenAI rate limits

### "Invalid JSON response"

Occasionally happens with AI generation:
1. Script automatically retries
2. Invalid challenges are filtered out
3. Check console for specific errors

### Low Success Rate

If many challenges are marked invalid:
1. Check validation criteria
2. Review error messages
3. May need to adjust prompts

## Support Files

### Backend Files

- `backend/challenge_generator_improved.py`: Improved AI generator
- `backend/challenge_generator_ai.py`: Original generator (for reference)
- `backend/seed_reference_challenges.py`: Legacy seed script

### CrewAI Files

- `cron-service/phase2-crewai/challenge_crew_ai.py`: Multi-agent system

## Next Steps

After generating new challenges:

1. **Test in application**
   - Verify freestyle practice works
   - Check different CEFR levels
   - Confirm randomization

2. **Monitor quality**
   - Track user completion rates
   - Collect feedback
   - Analyze effectiveness

3. **Iterate**
   - Refine prompts based on data
   - Add more challenge types
   - Improve validation

4. **Update other systems**
   - Apply improvements to CrewAI
   - Update seed script
   - Enhance quality checks

## Important Notes

⚠️ **Deletion is permanent**: Always use `--dry-run` first

💰 **Cost awareness**: Full generation (~10,800 challenges) costs $90-180

⏱️ **Time required**: Allow 4-5 hours for complete generation

✅ **Quality first**: Start with English to verify quality before scaling

## Success Metrics

After using these scripts, you should see:

- ✅ Answer position distribution: ~33% per option
- ✅ No content errors in challenges
- ✅ Precise CEFR level calibration
- ✅ 100% language field coverage
- ✅ >90% validation success rate
- ✅ Improved user engagement and learning

---

**Questions?** See the detailed guides linked at the top.

**Ready to start?** Follow [QUICK_START.md](./QUICK_START.md)

**Last Updated**: 2025-12-24
