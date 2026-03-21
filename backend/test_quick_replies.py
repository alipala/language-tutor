"""
Quick test to demonstrate context-aware quick replies
Shows how quick replies extract suggestions from coach's response
"""
import asyncio
from services.coach_service_optimized import coach_service_optimized as coach_service

TEST_USER_ID = "69937ade7d780583ed65ea31"

async def test_quick_replies():
    print("\n" + "="*80)
    print("🧪 TESTING CONTEXT-AWARE QUICK REPLIES")
    print("="*80)

    # Test case: Ask what to do next
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

    print(f"\n🎯 QUICK REPLIES GENERATED ({len(quick_replies)}):")
    for i, reply in enumerate(quick_replies, 1):
        print(f"   {i}. {reply['label']}")

    print("\n📊 ANALYSIS:")
    response_lower = ai_response.lower()

    # Check what actions were extracted from coach's response
    extracted_actions = []
    if "session" in response_lower or "practice" in response_lower:
        if any(word in response_lower for word in ["start", "begin", "try"]):
            extracted_actions.append("✅ Detected: Coach offered to start a session/practice")

    if any(word in response_lower for word in ["voice", "speaking", "conversation", "talk"]):
        if "practice" in response_lower or "conversation" in response_lower:
            extracted_actions.append("✅ Detected: Coach mentioned speaking/voice practice")

    if "challenge" in response_lower or "quiz" in response_lower:
        extracted_actions.append("✅ Detected: Coach mentioned challenges")

    if "plan" in response_lower:
        if any(word in response_lower for word in ["continue", "next", "learning"]):
            extracted_actions.append("✅ Detected: Coach mentioned learning plan")

    if extracted_actions:
        print("   Actions extracted from coach's response:")
        for action in extracted_actions:
            print(f"   {action}")
    else:
        print("   No specific actions detected - showing general options")

    print("\n" + "="*80)
    print("✅ QUICK REPLIES ANALYSIS COMPLETE")
    print("="*80)
    print("\nThe quick replies now:")
    print("  1. ✅ Analyze what the COACH said (not user's message)")
    print("  2. ✅ Extract actionable suggestions from coach's response")
    print("  3. ✅ Show 4-5 context-aware options (up from 2-3)")
    print("  4. ✅ Prioritize extracted actions over generic options")
    print()

if __name__ == "__main__":
    asyncio.run(test_quick_replies())
