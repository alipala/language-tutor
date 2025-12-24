# High-Quality Challenge Generation Guide

## Overview

This guide explains how to regenerate all language learning challenges with improved quality, fixing issues like answer position bias and CEFR level appropriateness.

## Problems with Current Challenges

Based on analysis of existing challenges, we identified several critical quality issues:

1. **Answer Position Bias**: Correct answers are predominantly in position 2 (Option B), making challenges predictable
2. **Content Errors**: Some challenges contain factually incorrect information (e.g., Spanish "ser vs estar" confusion)
3. **Poor CEFR Calibration**: Challenges don't always match the difficulty level they're tagged with
4. **Weak Randomization**: AI consistently places correct answers in predictable positions

## Solution: Improved Generator

The new `challenge_generator_improved.py` addresses these issues:

### Key Improvements

1. **Explicit Answer Randomization**
   - Post-processing step shuffles options after AI generation
   - Ensures even distribution across all positions
   - Validated in quality checks

2. **Detailed CEFR Guidelines**
   - Comprehensive level-specific instructions for AI
   - Grammar and vocabulary scope for each level
   - Example sentences demonstrating appropriate complexity

3. **Enhanced Quality Validation**
   - Automatic validation of generated challenges
   - Checks for required fields and structure
   - Validates correct answer count and distribution
   - Filters out invalid challenges

4. **Better AI Prompts**
   - Challenge-type specific instructions
   - Natural language requirements
   - Cultural appropriateness guidelines
   - Clear formatting expectations

## Step-by-Step Process

### Step 1: Analyze Current Challenge Quality

Before deleting anything, analyze what you currently have:

```bash
cd /home/user/language-tutor/scripts
python analyze_challenge_quality.py
```

This will show you:
- Answer position bias statistics
- Language field coverage
- CEFR level distribution
- Sample challenges for inspection

**Optional**: Save the analysis report for later comparison:

```bash
python analyze_challenge_quality.py --save-report
```

### Step 2: Backup Current Data (Optional but Recommended)

```bash
# Export current challenges to JSON backup
python backup_challenges.py --output challenge_backup_$(date +%Y%m%d).json
```

### Step 3: Delete Existing Challenges

**Important**: This action cannot be undone!

First, do a dry run to see what would be deleted:

```bash
python delete_all_challenges.py --dry-run
```

Review the output carefully. If you're ready to proceed:

```bash
python delete_all_challenges.py --confirm
```

This will:
- Show you current statistics
- Ask for confirmation (you must type 'DELETE')
- Delete all challenges from both `reference_challenges` and `challenge_pool`
- Verify deletion

### Step 4: Generate New High-Quality Challenges

#### Option A: Start with English Only (Recommended)

Generate and test English challenges first to verify quality:

```bash
python generate_reference_challenges_improved.py \
  --language english \
  --challenges-per-type 50
```

This will:
- Generate 50 challenges per type (6 types)
- For all 6 CEFR levels (A1-C2)
- Total: 1,800 English challenges
- Estimated time: ~45-60 minutes

**Review the generated challenges**:

```bash
python analyze_challenge_quality.py --collection reference_challenges
```

Check for:
- ✅ Even distribution of correct answer positions
- ✅ No language field issues
- ✅ Balanced CEFR levels
- ✅ High-quality content

#### Option B: Generate for All Languages

Once you're satisfied with English quality:

```bash
python generate_reference_challenges_improved.py \
  --all-languages \
  --challenges-per-type 50
```

This will generate for all 6 languages:
- english, spanish, dutch, german, french, portuguese
- Total: ~10,800 challenges
- Estimated time: ~4-5 hours

#### Option C: Generate for Specific Language and Level

For targeted generation:

```bash
# Just Spanish B1
python generate_reference_challenges_improved.py \
  --language spanish \
  --level B1 \
  --challenges-per-type 50
```

### Step 5: Verify Quality

After generation, run analysis again:

```bash
python analyze_challenge_quality.py --collection reference_challenges
```

Compare with your initial analysis:
- Answer position distribution should be ~33% per position
- No missing language fields
- All CEFR levels should be balanced
- Sample challenges should be high quality

### Step 6: Test in Application

1. Run your application
2. Test freestyle practice mode
3. Check challenges at different levels
4. Verify randomization is working
5. Confirm explanations are clear and helpful

## Configuration

### Using a Different Model

To use GPT-4.5 or a newer model:

```bash
export GPT_MODEL="gpt-4.5"  # Or whatever the model name is
python generate_reference_challenges_improved.py --language english --challenges-per-type 50
```

Or set in your `.env` file:

```
GPT_MODEL=gpt-4.5
```

### Adjusting Challenge Quantity

For testing or cost management:

```bash
# Generate fewer challenges per type
python generate_reference_challenges_improved.py \
  --language english \
  --challenges-per-type 10
```

## Cost Estimates

Using GPT-4o at current pricing ($2.50/1M input tokens, $10/1M output tokens):

- Per batch (6 challenges): ~$0.05-0.10
- Per level (300 challenges): ~$2.50-5.00
- Per language (1,800 challenges): ~$15-30
- All languages (10,800 challenges): ~$90-180

**Note**: Actual costs may vary based on:
- Model used (GPT-4.5 may have different pricing)
- Challenge complexity
- API rate limits and retries

## Troubleshooting

### Error: "Rate limit exceeded"

If you hit OpenAI rate limits:

1. The script includes 1-second delays between batches
2. For strict limits, modify the delay in the script:
   ```python
   await asyncio.sleep(2)  # Increase to 2 seconds
   ```

### Error: "Invalid JSON response"

Occasionally the AI returns malformed JSON:

1. The script has retry logic built-in
2. Invalid challenges are logged and skipped
3. Check the output for specific error messages
4. Consider increasing temperature for variety (in `challenge_generator_improved.py`)

### Low Success Rate (< 80%)

If many challenges are marked invalid:

1. Check the validation criteria in the script
2. Review sample invalid challenges
3. Adjust the AI prompts if needed
4. Consider using a different model version

### Missing Language Fields

Old challenges might not have language fields. To migrate:

```bash
python migrate_add_language_fields.py
```

## Scripts Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `analyze_challenge_quality.py` | Analyze existing challenges for quality issues | `python analyze_challenge_quality.py` |
| `delete_all_challenges.py` | Safely delete challenges from database | `python delete_all_challenges.py --confirm` |
| `generate_reference_challenges_improved.py` | Generate new high-quality challenges | `python generate_reference_challenges_improved.py --language english --challenges-per-type 50` |

## Files Modified/Created

### New Files
- `backend/challenge_generator_improved.py` - Improved AI generator
- `scripts/analyze_challenge_quality.py` - Quality analysis tool
- `scripts/delete_all_challenges.py` - Safe deletion tool
- `scripts/generate_reference_challenges_improved.py` - Generation script
- `scripts/CHALLENGE_GENERATION_GUIDE.md` - This guide

### Files to Update Later
- `backend/seed_reference_challenges.py` - Should use improved generator
- `cron-service/phase2-crewai/challenge_crew_ai.py` - Should use improved prompts

## Next Steps After Generation

1. **Update Seed Script**
   - Modify `backend/seed_reference_challenges.py` to use `challenge_generator_improved.py`

2. **Update CrewAI Integration**
   - Apply the same improvements to CrewAI challenge generation
   - Use detailed CEFR guidelines
   - Add answer randomization

3. **Monitor in Production**
   - Track user completion rates
   - Monitor for feedback about challenge quality
   - Analyze which levels/types need adjustment

4. **Iterate and Improve**
   - Collect data on which challenges are most effective
   - Refine prompts based on user performance
   - Add more sophisticated quality checks

## CEFR Level Guidelines Reference

### A1 - Beginner
- **Grammar**: Present simple, basic pronouns, singular/plural
- **Vocabulary**: 200-300 words (numbers, colors, family, food)
- **Sentences**: Very short (3-6 words)
- **Example**: "I am happy. She has a cat."

### A2 - Elementary
- **Grammar**: Past simple, future with 'going to', comparatives
- **Vocabulary**: 400-600 words (personal info, shopping, hobbies)
- **Sentences**: Short (5-10 words)
- **Example**: "I went to the park yesterday."

### B1 - Intermediate
- **Grammar**: Present perfect, conditionals (type 1), passive voice
- **Vocabulary**: 1000-1500 words (travel, opinions, feelings)
- **Sentences**: Medium (8-15 words)
- **Example**: "I have lived here for five years."

### B2 - Upper Intermediate
- **Grammar**: All tenses, conditionals (types 2, 3), reported speech
- **Vocabulary**: 2000-2500 words (abstract concepts, idioms)
- **Sentences**: Longer (12-20 words)
- **Example**: "Having finished the project, she decided to celebrate."

### C1 - Advanced
- **Grammar**: Advanced structures, inversion, cleft sentences
- **Vocabulary**: 3000-4000 words (specialized terminology)
- **Sentences**: Long and complex (15-25+ words)
- **Example**: "Rarely had she encountered such a perplexing situation."

### C2 - Mastery
- **Grammar**: All advanced structures, subtle semantic distinctions
- **Vocabulary**: 5000+ words (including rare terms)
- **Sentences**: Very complex with sophisticated rhetoric
- **Example**: "Notwithstanding the overwhelming evidence to the contrary..."

## Support

If you encounter issues:

1. Check the console output for specific error messages
2. Review the generated challenges in MongoDB
3. Run the analysis tool to identify patterns
4. Adjust prompts in `challenge_generator_improved.py` as needed

## Success Metrics

After completion, you should see:

- ✅ **Answer distribution**: ~33% per position for multiple choice
- ✅ **CEFR balance**: Equal number of challenges per level
- ✅ **Language coverage**: All 6 languages with complete data
- ✅ **Quality validation**: >90% of generated challenges passing validation
- ✅ **No bias**: Statistical tests show random distribution
- ✅ **User feedback**: Improved challenge quality and engagement

---

**Last Updated**: 2025-12-24
**Version**: 1.0
**Author**: Language Tutor Development Team
