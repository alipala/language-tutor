"""
Final Assessment Handler
Processes final speaking assessments for learning plans with comprehensive evaluation
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx
from bson import ObjectId

async def process_final_assessment(
    plan: Dict[str, Any],
    conversation_data: Optional[Dict[str, Any]],
    basic_summary: str,
    user_id: str,
    learning_plans_collection
) -> Dict[str, Any]:
    """
    Process a final assessment session and generate comprehensive evaluation scores.

    This function:
    1. Analyzes the conversation using GPT-4o to generate assessment scores
    2. Evaluates grammar, vocabulary, fluency, coherence, and pronunciation
    3. Determines if the student passed or failed
    4. Stores results in final_assessment.attempts[]
    5. Updates plan status to 'completed' or 'failed_assessment'
    """

    print(f"[FINAL_ASSESSMENT] 🎓 Starting final assessment processing")

    # Extract plan details
    plan_id = plan.get("id")
    language = plan.get("language", "english")
    current_level = plan.get("proficiency_level", "A1")

    # Get next level for context
    level_progression = {
        'A1': 'A2', 'A2': 'B1', 'B1': 'B2',
        'B2': 'C1', 'C1': 'C2', 'C2': 'C2'
    }
    next_level = level_progression.get(current_level.upper(), 'B1')

    # Extract conversation messages
    if not conversation_data or 'messages' not in conversation_data:
        raise ValueError("Conversation data with messages is required for assessment")

    messages = conversation_data.get('messages', [])
    duration_minutes = conversation_data.get('duration_minutes', 2.0)

    # Extract user messages for analysis
    user_messages = [msg['content'] for msg in messages if msg.get('role') == 'user']

    print(f"[FINAL_ASSESSMENT] Analyzing {len(user_messages)} user messages")
    print(f"[FINAL_ASSESSMENT] Duration: {duration_minutes} minutes")
    print(f"[FINAL_ASSESSMENT] Current level: {current_level}, Next level: {next_level}")

    # Generate comprehensive assessment using GPT-4o
    assessment_scores = await generate_assessment_scores(
        user_messages=user_messages,
        language=language,
        current_level=current_level,
        next_level=next_level,
        duration_minutes=duration_minutes
    )

    # Determine pass/fail based on dual criteria
    overall_score = assessment_scores['overall_score']
    current_level_mastery = assessment_scores['current_level_mastery']
    next_level_readiness = assessment_scores['next_level_readiness']

    # Passing criteria: Overall >= 60 AND current level mastery >= 70
    passed = overall_score >= 60 and current_level_mastery >= 70

    print(f"[FINAL_ASSESSMENT] Scores: Overall={overall_score}, Mastery={current_level_mastery}, Readiness={next_level_readiness}")
    print(f"[FINAL_ASSESSMENT] Result: {'PASSED ✅' if passed else 'NOT PASSED ❌'}")

    # Create attempt record
    attempt = {
        "attempt_number": len(plan.get("final_assessment", {}).get("attempts", [])) + 1,
        "date": datetime.utcnow().isoformat(),
        "duration_minutes": duration_minutes,
        "overall_score": overall_score,
        "current_level_mastery": current_level_mastery,
        "next_level_readiness": next_level_readiness,
        "scores": {
            "grammar": assessment_scores['grammar_score'],
            "vocabulary": assessment_scores['vocabulary_score'],
            "fluency": assessment_scores['fluency_score'],
            "coherence": assessment_scores['coherence_score'],
            "pronunciation": assessment_scores['pronunciation_score']
        },
        "feedback": assessment_scores['feedback'],
        "strengths": assessment_scores['strengths'],
        "areas_for_improvement": assessment_scores['areas_for_improvement'],
        "passed": passed
    }

    # Update plan with assessment results
    update_data = {
        "$push": {
            "final_assessment.attempts": attempt
        },
        "$set": {
            "final_assessment.completed": passed,
            "final_assessment.passed": passed,
            "final_assessment.last_attempt_date": datetime.utcnow().isoformat(),
            "status": "completed" if passed else "failed_assessment",
            "updated_at": datetime.utcnow().isoformat()
        }
    }

    # Update the plan in database
    result = await learning_plans_collection.update_one(
        {"id": plan_id},
        update_data
    )

    if result.modified_count == 0:
        print(f"[FINAL_ASSESSMENT] ⚠️ Warning: Plan update affected 0 documents")
    else:
        print(f"[FINAL_ASSESSMENT] ✅ Plan updated successfully")

    # Return response with assessment results
    return {
        "success": True,
        "message": "Final assessment completed",
        "is_final_assessment": True,
        "assessment_result": {
            "passed": passed,
            "overall_score": overall_score,
            "current_level_mastery": current_level_mastery,
            "next_level_readiness": next_level_readiness,
            "current_level": current_level,
            "next_level": next_level,
            "attempt_number": attempt["attempt_number"],
            "scores": attempt["scores"],
            "feedback": attempt["feedback"],
            "strengths": attempt["strengths"],
            "areas_for_improvement": attempt["areas_for_improvement"]
        },
        "plan_status": "completed" if passed else "failed_assessment"
    }


async def generate_assessment_scores(
    user_messages: List[str],
    language: str,
    current_level: str,
    next_level: str,
    duration_minutes: float
) -> Dict[str, Any]:
    """
    Use GPT-4o to analyze the conversation and generate comprehensive assessment scores.
    """

    # Combine all user messages into conversation transcript
    transcript = "\n".join([f"Student: {msg}" for msg in user_messages])

    # Build assessment prompt
    prompt = f"""You are an expert {language} language assessor evaluating a final speaking assessment.

ASSESSMENT CONTEXT:
- Current CEFR Level: {current_level}
- Next Level: {next_level}
- Assessment Duration: {duration_minutes} minutes
- Number of Student Responses: {len(user_messages)}

CONVERSATION TRANSCRIPT:
{transcript}

TASK:
Evaluate this student's speaking performance using the DUAL-CRITERIA system:

1. CURRENT LEVEL MASTERY ({current_level}):
   - How well does the student demonstrate command of {current_level} competencies?
   - Score 0-100 (70+ indicates strong mastery)

2. NEXT LEVEL READINESS ({next_level}):
   - Does the student show potential for {next_level} level work?
   - Score 0-100 (60+ indicates readiness)

EVALUATION CRITERIA (each scored 0-100):
- Grammar: Accuracy of grammatical structures appropriate for {current_level}
- Vocabulary: Range and appropriateness of vocabulary for {current_level}
- Fluency: Natural flow, hesitations, self-corrections
- Coherence: Logical connections and organization of ideas
- Pronunciation: Clarity and accuracy of pronunciation

Provide your evaluation in JSON format:
{{
  "current_level_mastery": <0-100>,
  "next_level_readiness": <0-100>,
  "grammar_score": <0-100>,
  "vocabulary_score": <0-100>,
  "fluency_score": <0-100>,
  "coherence_score": <0-100>,
  "pronunciation_score": <0-100>,
  "overall_score": <0-100 (weighted average)>,
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "areas_for_improvement": ["area 1", "area 2", "area 3"],
  "feedback": "2-3 sentence comprehensive feedback explaining the assessment"
}}

Be objective and fair. Base scores on demonstrated abilities in the conversation."""

    # Call GPT-4o for assessment
    openai_api_key = os.getenv("OPENAI_API_KEY")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openai_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": "You are an expert language assessment specialist."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.3  # Lower temperature for consistent assessment
            },
            timeout=60.0
        )

    if response.status_code != 200:
        raise Exception(f"GPT-4o assessment failed: {response.text}")

    result = response.json()
    assessment_data = result['choices'][0]['message']['content']

    # Parse JSON response
    import json
    scores = json.loads(assessment_data)

    print(f"[FINAL_ASSESSMENT] 📊 Assessment scores generated:")
    print(f"  Current Level Mastery: {scores['current_level_mastery']}")
    print(f"  Next Level Readiness: {scores['next_level_readiness']}")
    print(f"  Overall Score: {scores['overall_score']}")

    return scores
