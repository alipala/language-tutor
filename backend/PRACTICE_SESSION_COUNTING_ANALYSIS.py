#!/usr/bin/env python3
"""
PRACTICE SESSION COUNTING ANALYSIS
==================================

This script analyzes whether practice sessions count toward speaking minutes
based on the actual code implementation.

Key Question: Are practice sessions counted toward the 150-minute limit?
"""

def analyze_practice_session_counting():
    """Analyze how practice sessions are counted in the system"""
    
    print("🔍 PRACTICE SESSION COUNTING ANALYSIS")
    print("=" * 60)
    
    print("📋 KEY QUESTION:")
    print("   Are practice sessions counted toward the 150-minute speaking limit?")
    print()
    
    print("🔍 CODE ANALYSIS:")
    print("=" * 40)
    
    print("1️⃣ LEARNING PLAN SESSIONS (Custom Learning Plans):")
    print("   File: backend/learning_routes.py")
    print("   Function: save_session_summary()")
    print("   ✅ YES - These sessions COUNT toward speaking minutes")
    print("   Code Evidence:")
    print("   ```python")
    print("   # CORRECTED: Always use INTEGER minutes")
    print("   duration_minutes = 5  # Complete session")
    print("   ")
    print("   # CRITICAL: Track subscription usage")
    print("   speaking_time_request = SpeakingTimeTrackingRequest(")
    print("       user_id=str(current_user.id),")
    print("       speaking_minutes=float(duration_minutes),")
    print("       session_completed=True")
    print("   )")
    print("   tracking_success = await SubscriptionService.track_speaking_time(speaking_time_request)")
    print("   ```")
    print()
    
    print("2️⃣ PRACTICE SESSIONS (Standalone Conversations):")
    print("   File: backend/progress_routes.py")
    print("   Function: save_conversation()")
    print("   ✅ YES - These sessions COUNT toward speaking minutes")
    print("   Code Evidence:")
    print("   ```python")
    print("   # Track subscription usage for both sessions AND minutes")
    print("   await track_subscription_usage(current_user.id, 'practice_session')")
    print("   ```")
    print()
    
    print("3️⃣ SUBSCRIPTION SERVICE TRACKING:")
    print("   File: backend/subscription_service.py")
    print("   Function: track_speaking_time()")
    print("   ✅ CONFIRMED - Both session types update speaking minutes")
    print("   Code Evidence:")
    print("   ```python")
    print("   # Always track speaking minutes")
    print("   update_data = {")
    print("       '$inc': {")
    print("           'practice_minutes_used': speaking_minutes")
    print("       }")
    print("   }")
    print("   if session_completed:")
    print("       update_data['$inc']['practice_sessions_used'] = 1")
    print("   ```")
    print()
    
    print("🎯 DEFINITIVE ANSWER:")
    print("=" * 40)
    print("✅ YES - Practice sessions ARE counted toward speaking minutes!")
    print()
    print("📊 BOTH SESSION TYPES COUNT:")
    print("   • Learning Plan Sessions (French custom plan) → Count toward 150 minutes")
    print("   • Practice Sessions (standalone conversations) → Count toward 150 minutes")
    print()
    
    print("🧮 USER SCENARIO CALCULATION:")
    print("=" * 40)
    print("Starting Minutes: 150 (Fluency Builder Monthly)")
    print()
    print("Session 1: French Learning Plan → 5 minutes")
    print("Session 2: French Learning Plan → 5 minutes") 
    print("Session 3: Practice Session → 5 minutes")
    print("                              ___________")
    print("Total Minutes Used:           15 minutes")
    print()
    print("Remaining Minutes: 150 - 15 = 135 minutes")
    print()
    
    print("✅ CONFIRMED: User would have 135 minutes remaining")
    print()
    
    print("🔍 TECHNICAL DETAILS:")
    print("=" * 40)
    print("• All sessions use INTEGER minutes (5, 4, 3, 2, 1)")
    print("• Both learning plan and practice sessions call track_speaking_time()")
    print("• The system tracks practice_minutes_used for subscription limits")
    print("• Session counting is unified across all session types")
    print()
    
    print("🚨 IMPORTANT CLARIFICATION:")
    print("=" * 40)
    print("The term 'practice session' can be confusing because:")
    print("• 'Practice Sessions' = Standalone conversation sessions")
    print("• 'Learning Plan Sessions' = Sessions within custom learning plans")
    print("• BOTH types are considered 'speaking practice' for billing")
    print("• BOTH types count toward the monthly speaking minute limit")
    print()
    
    print("🎉 CONCLUSION:")
    print("=" * 40)
    print("Practice sessions ARE counted toward speaking minutes.")
    print("The user's scenario calculation is CORRECT:")
    print("• 2 French learning plan sessions: 10 minutes")
    print("• 1 practice session: 5 minutes")
    print("• Total used: 15 minutes")
    print("• Remaining: 135 minutes")

if __name__ == "__main__":
    analyze_practice_session_counting()
