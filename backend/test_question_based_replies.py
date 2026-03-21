"""
Test question-based quick replies (not action commands)
"""
import asyncio
from services.coach_service_optimized import coach_service_optimized as coach_service

TEST_USER_ID = "69937ade7d780583ed65ea31"

async def test_question_replies():
    print("\n" + "="*80)
    print("🧪 TESTING QUESTION-BASED QUICK REPLIES (NOT ACTIONS)")
    print("="*80)

    print("\n📝 User asks: 'What should I do next?'")
    print("-" * 80)

    response = await coach_service.chat(
        user_id=TEST_USER_ID,
        language="en",
        user_message="What should I do next?",
        conversation_history=[]
    )

    ai_response = response['raw_response']
    quick_replies = response['quick_replies']

    print(f"\n✅ COACH SAYS:")
    print(f"   {ai_response}")

    print(f"\n🎯 QUICK REPLIES ({len(quick_replies)}):")
    for i, reply in enumerate(quick_replies, 1):
        label = reply['label']
        is_question = "?" in label or any(word in label.lower() for word in ["what", "how", "show", "give"])
        is_action = any(word in label.lower() for word in ["start", "set up", "continue", "try"]) and "?" not in label

        status = "✅" if is_question and not is_action else "❌"
        print(f"   {i}. {status} {label}")
        if is_action:
            print(f"      ⚠️  WARNING: Looks like an action command!")

    print("\n📊 VALIDATION:")
    all_questions = all(
        "?" in reply['label'] or
        any(word in reply['label'].lower() for word in ["what", "how", "show", "give"])
        for reply in quick_replies
    )

    any_actions = any(
        any(word in reply['label'].lower() for word in ["start my", "set up", "continue my", "try a"])
        and "?" not in reply['label']
        for reply in quick_replies
    )

    if all_questions and not any_actions:
        print("   ✅ All quick replies are questions - CORRECT!")
    else:
        print("   ❌ Some quick replies are action commands - NEEDS FIX!")

    print("\n" + "="*80)
    print()

if __name__ == "__main__":
    asyncio.run(test_question_replies())
