# Quick Start: Regenerate Challenges

## TL;DR - Fast Track

```bash
cd /home/user/language-tutor/scripts

# 1. Analyze current quality
python analyze_challenge_quality.py

# 2. Delete existing challenges
python delete_all_challenges.py --dry-run
python delete_all_challenges.py --confirm

# 3. Generate English first (test quality)
python generate_reference_challenges_improved.py --language english --challenges-per-type 50

# 4. Verify quality
python analyze_challenge_quality.py --collection reference_challenges

# 5. If satisfied, generate other languages
python generate_reference_challenges_improved.py --all-languages --challenges-per-type 50
```

## Estimated Times

- **English only**: 45-60 minutes, ~1,800 challenges
- **All languages**: 4-5 hours, ~10,800 challenges

## Estimated Costs (GPT-4o)

- **English only**: $15-30
- **All languages**: $90-180

## What Gets Fixed

✅ Answer position bias (no more "always Option B")
✅ Content errors (e.g., incorrect Spanish grammar)
✅ CEFR level calibration
✅ Language field issues
✅ Overall challenge quality

## Key Improvements

1. **Detailed CEFR Guidelines**: AI gets specific instructions for each level
2. **Answer Randomization**: Post-processing ensures even distribution
3. **Quality Validation**: Automatic filtering of invalid challenges
4. **Better Prompts**: Challenge-type specific instructions

## Safety Features

- `--dry-run` flag to preview deletions
- Confirmation required before actual deletion
- Quality validation during generation
- Progress tracking and error handling

## For Detailed Instructions

See [CHALLENGE_GENERATION_GUIDE.md](./CHALLENGE_GENERATION_GUIDE.md)

## Support

Issues? Check:
1. Console output for errors
2. Analysis report for quality metrics
3. MongoDB directly to inspect generated challenges
4. Adjust prompts in `challenge_generator_improved.py` if needed

---

**Ready to start?** Run the first command above! 🚀
