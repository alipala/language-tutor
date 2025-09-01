#!/usr/bin/env python3
"""
PRODUCTION DATABASE VALIDATION
=============================

This script validates the fix by checking the actual production database
for user Ali Pala (ID: 688921c268819565ef1ce3dc, email: alipala.ist@gmail.com)
to ensure all duration tracking issues have been resolved.

IMPORTANT: This connects to PRODUCTION Railway MongoDB, not local DB!
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
from bson import ObjectId

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import database
from subscription_service import SubscriptionService

# Target user information
TARGET_USER_ID = "688921c268819565ef1ce3dc"
TARGET_USER_EMAIL = "alipala.ist@gmail.com"
TARGET_LEARNING_PLAN_ID = "688b531449449925afb0d481"

class ProductionValidation:
    """Production database validation for the duration tracking fix"""
    
    def __init__(self):
        self.validation_results = {}
    
    async def validate_production_fix(self):
        """Validate the fix in production database"""
        print("🔍 PRODUCTION DATABASE VALIDATION")
        print("=" * 60)
        print(f"Target User: {TARGET_USER_EMAIL}")
        print(f"User ID: {TARGET_USER_ID}")
        print(f"Learning Plan ID: {TARGET_LEARNING_PLAN_ID}")
        print(f"Validation Time: {datetime.utcnow().isoformat()}")
        print(f"Database: PRODUCTION (Railway MongoDB)")
        print("=" * 60)
        
        # Step 1: Validate user subscription data
        await self._validate_user_subscription_data()
        
        # Step 2: Validate learning plan data
        await self._validate_learning_plan_data()
        
        # Step 3: Validate session 13 exists
        await self._validate_session_13_exists()
        
        # Step 4: Validate duration calculations
        await self._validate_duration_calculations()
        
        # Step 5: Validate no decimal durations
        await self._validate_no_decimal_durations()
        
        # Step 6: Generate validation report
        await self._generate_validation_report()
        
        print("\n🎯 PRODUCTION VALIDATION COMPLETE")
        return self.validation_results
    
    async def _validate_user_subscription_data(self):
        """Validate user's subscription data in production"""
        print("\n📊 STEP 1: VALIDATING USER SUBSCRIPTION DATA")
        print("-" * 40)
        
        try:
            # Get user data from production
            user = await database["users"].find_one({"_id": ObjectId(TARGET_USER_ID)})
            
            if not user:
                print(f"❌ User not found in production: {TARGET_USER_ID}")
                self.validation_results['user_found'] = False
                return
            
            print(f"✅ User found in production: {user.get('email', 'No email')}")
            
            # Check subscription data
            practice_sessions = user.get('practice_sessions_used', 0)
            practice_minutes = user.get('practice_minutes_used', 0.0)
            assessments_used = user.get('assessments_used', 0)
            subscription_plan = user.get('subscription_plan', 'unknown')
            subscription_status = user.get('subscription_status', 'unknown')
            
            print(f"📋 Current Subscription Data:")
            print(f"   Plan: {subscription_plan}")
            print(f"   Status: {subscription_status}")
            print(f"   Sessions Used: {practice_sessions}")
            print(f"   Minutes Used: {practice_minutes}")
            print(f"   Assessments Used: {assessments_used}")
            
            # Get subscription status from service
            subscription_status_obj = await SubscriptionService.get_user_subscription_status(TARGET_USER_ID)
            
            if subscription_status_obj.limits:
                limits = subscription_status_obj.limits
                print(f"📋 Calculated Limits:")
                print(f"   Sessions: {limits.sessions_used}/{limits.sessions_limit} (Remaining: {limits.sessions_remaining})")
                print(f"   Minutes: {limits.minutes_used:.2f}/{limits.minutes_limit} (Remaining: {limits.minutes_remaining:.2f})")
                print(f"   Assessments: {limits.assessments_used}/{limits.assessments_limit} (Remaining: {limits.assessments_remaining})")
                
                # Store validation results
                self.validation_results['user_subscription'] = {
                    'found': True,
                    'plan': subscription_plan,
                    'status': subscription_status,
                    'sessions_used': practice_sessions,
                    'minutes_used': practice_minutes,
                    'assessments_used': assessments_used,
                    'calculated_limits': {
                        'sessions_used': limits.sessions_used,
                        'sessions_remaining': limits.sessions_remaining,
                        'minutes_used': limits.minutes_used,
                        'minutes_remaining': limits.minutes_remaining,
                        'assessments_used': limits.assessments_used,
                        'assessments_remaining': limits.assessments_remaining
                    }
                }
                
                # Validate expected values after fix
                expected_sessions = 2  # Should be 2 after our fix
                expected_minutes = 17.0  # Should be 17.0 after our fix
                
                sessions_correct = limits.sessions_used == expected_sessions
                minutes_correct = abs(limits.minutes_used - expected_minutes) < 0.1
                
                print(f"\n✅ VALIDATION RESULTS:")
                print(f"   Sessions: {limits.sessions_used} (Expected: {expected_sessions}) {'✅' if sessions_correct else '❌'}")
                print(f"   Minutes: {limits.minutes_used:.2f} (Expected: {expected_minutes}) {'✅' if minutes_correct else '❌'}")
                
                self.validation_results['user_subscription']['validation'] = {
                    'sessions_correct': sessions_correct,
                    'minutes_correct': minutes_correct,
                    'expected_sessions': expected_sessions,
                    'expected_minutes': expected_minutes
                }
            
        except Exception as e:
            print(f"❌ Error validating user subscription data: {e}")
            self.validation_results['user_subscription'] = {'found': False, 'error': str(e)}
    
    async def _validate_learning_plan_data(self):
        """Validate learning plan data in production"""
        print("\n📚 STEP 2: VALIDATING LEARNING PLAN DATA")
        print("-" * 40)
        
        try:
            # Get learning plan from production
            learning_plan = await database["learning_plans"].find_one({"_id": ObjectId(TARGET_LEARNING_PLAN_ID)})
            
            if not learning_plan:
                print(f"❌ Learning plan not found in production: {TARGET_LEARNING_PLAN_ID}")
                self.validation_results['learning_plan_found'] = False
                return
            
            print(f"✅ Learning plan found: {learning_plan.get('language', 'Unknown')} {learning_plan.get('proficiency_level', 'Unknown')}")
            
            # Check learning plan data
            completed_sessions = learning_plan.get('completed_sessions', 0)
            practice_minutes_used = learning_plan.get('practice_minutes_used', 0.0)
            progress_percentage = learning_plan.get('progress_percentage', 0.0)
            total_sessions = learning_plan.get('total_sessions', 0)
            
            print(f"📋 Learning Plan Progress:")
            print(f"   Completed Sessions: {completed_sessions}")
            print(f"   Practice Minutes Used: {practice_minutes_used}")
            print(f"   Progress Percentage: {progress_percentage:.1f}%")
            print(f"   Total Sessions: {total_sessions}")
            
            # Check sessions in weekly schedule
            weekly_schedule = learning_plan.get('plan_content', {}).get('weekly_schedule', [])
            total_learning_sessions = 0
            total_learning_minutes = 0.0
            
            for week in weekly_schedule:
                session_details = week.get('session_details', [])
                for session in session_details:
                    total_learning_sessions += 1
                    duration = session.get('duration_minutes', 0)
                    total_learning_minutes += duration
                    
                    session_num = session.get('global_session_number', 'Unknown')
                    status = session.get('status', 'unknown')
                    print(f"   Session {session_num}: {duration} min, Status: {status}")
            
            print(f"📊 Weekly Schedule Summary:")
            print(f"   Total Sessions in Schedule: {total_learning_sessions}")
            print(f"   Total Minutes in Schedule: {total_learning_minutes}")
            
            # Store validation results
            self.validation_results['learning_plan'] = {
                'found': True,
                'completed_sessions': completed_sessions,
                'practice_minutes_used': practice_minutes_used,
                'progress_percentage': progress_percentage,
                'total_sessions': total_sessions,
                'schedule_sessions': total_learning_sessions,
                'schedule_minutes': total_learning_minutes
            }
            
        except Exception as e:
            print(f"❌ Error validating learning plan data: {e}")
            self.validation_results['learning_plan'] = {'found': False, 'error': str(e)}
    
    async def _validate_session_13_exists(self):
        """Validate that session 13 exists in the learning plan"""
        print("\n🎯 STEP 3: VALIDATING SESSION 13 EXISTS")
        print("-" * 40)
        
        try:
            learning_plan = await database["learning_plans"].find_one({"_id": ObjectId(TARGET_LEARNING_PLAN_ID)})
            
            if not learning_plan:
                print("❌ Learning plan not found")
                return
            
            # Search for session 13
            weekly_schedule = learning_plan.get('plan_content', {}).get('weekly_schedule', [])
            session_13_found = False
            session_13_data = None
            
            for week in weekly_schedule:
                session_details = week.get('session_details', [])
                for session in session_details:
                    if session.get('global_session_number') == 13:
                        session_13_found = True
                        session_13_data = session
                        break
                if session_13_found:
                    break
            
            if session_13_found:
                print("✅ Session 13 found in production!")
                print(f"   Duration: {session_13_data.get('duration_minutes', 0)} minutes")
                print(f"   Status: {session_13_data.get('status', 'unknown')}")
                print(f"   Completed At: {session_13_data.get('completed_at', 'unknown')}")
                print(f"   Summary: {session_13_data.get('summary', 'No summary')[:100]}...")
                
                self.validation_results['session_13'] = {
                    'found': True,
                    'data': session_13_data
                }
            else:
                print("❌ Session 13 NOT found in production")
                self.validation_results['session_13'] = {'found': False}
            
        except Exception as e:
            print(f"❌ Error validating session 13: {e}")
            self.validation_results['session_13'] = {'found': False, 'error': str(e)}
    
    async def _validate_duration_calculations(self):
        """Validate that duration calculations are working correctly"""
        print("\n🧮 STEP 4: VALIDATING DURATION CALCULATIONS")
        print("-" * 40)
        
        try:
            # Get all session data for the user
            conversation_sessions = await database["conversation_sessions"].find({
                "user_id": TARGET_USER_ID
            }).to_list(length=None)
            
            regular_sessions = await database["sessions"].find({
                "user_id": TARGET_USER_ID
            }).to_list(length=None)
            
            learning_plan = await database["learning_plans"].find_one({"_id": ObjectId(TARGET_LEARNING_PLAN_ID)})
            
            # Calculate totals from all sources
            conv_minutes = sum(s.get('duration_minutes', 0) for s in conversation_sessions)
            conv_completed = sum(1 for s in conversation_sessions if s.get('session_completed', False))
            
            reg_minutes = sum(s.get('duration_minutes', 0) for s in regular_sessions)
            reg_completed = sum(1 for s in regular_sessions if s.get('session_completed', False))
            
            learning_minutes = 0
            learning_completed = 0
            if learning_plan:
                weekly_schedule = learning_plan.get('plan_content', {}).get('weekly_schedule', [])
                for week in weekly_schedule:
                    session_details = week.get('session_details', [])
                    for session in session_details:
                        learning_minutes += session.get('duration_minutes', 0)
                        if session.get('status') == 'completed':
                            learning_completed += 1
            
            total_actual_minutes = conv_minutes + reg_minutes + learning_minutes
            total_actual_sessions = conv_completed + reg_completed + learning_completed
            
            print(f"📊 ACTUAL SESSION DATA:")
            print(f"   Conversation: {len(conversation_sessions)} sessions, {conv_minutes:.2f} min, {conv_completed} completed")
            print(f"   Regular: {len(regular_sessions)} sessions, {reg_minutes:.2f} min, {reg_completed} completed")
            print(f"   Learning Plan: {learning_completed} sessions, {learning_minutes:.2f} min")
            print(f"   TOTAL: {total_actual_sessions} completed sessions, {total_actual_minutes:.2f} minutes")
            
            # Compare with user subscription data
            user = await database["users"].find_one({"_id": ObjectId(TARGET_USER_ID)})
            if user:
                user_minutes = user.get('practice_minutes_used', 0.0)
                user_sessions = user.get('practice_sessions_used', 0)
                
                print(f"📊 USER SUBSCRIPTION DATA:")
                print(f"   Sessions: {user_sessions}")
                print(f"   Minutes: {user_minutes:.2f}")
                
                # Check consistency
                minutes_match = abs(total_actual_minutes - user_minutes) < 0.1
                sessions_match = total_actual_sessions == user_sessions
                
                print(f"\n✅ CONSISTENCY CHECK:")
                print(f"   Minutes Match: {'✅' if minutes_match else '❌'} (Diff: {total_actual_minutes - user_minutes:.2f})")
                print(f"   Sessions Match: {'✅' if sessions_match else '❌'} (Diff: {total_actual_sessions - user_sessions})")
                
                self.validation_results['duration_calculations'] = {
                    'actual_minutes': total_actual_minutes,
                    'actual_sessions': total_actual_sessions,
                    'user_minutes': user_minutes,
                    'user_sessions': user_sessions,
                    'minutes_match': minutes_match,
                    'sessions_match': sessions_match,
                    'minutes_diff': total_actual_minutes - user_minutes,
                    'sessions_diff': total_actual_sessions - user_sessions
                }
            
        except Exception as e:
            print(f"❌ Error validating duration calculations: {e}")
            self.validation_results['duration_calculations'] = {'error': str(e)}
    
    async def _validate_no_decimal_durations(self):
        """Validate that there are no decimal durations in the database"""
        print("\n🔢 STEP 5: VALIDATING NO DECIMAL DURATIONS")
        print("-" * 40)
        
        try:
            decimal_durations_found = []
            
            # Check learning plan sessions
            learning_plan = await database["learning_plans"].find_one({"_id": ObjectId(TARGET_LEARNING_PLAN_ID)})
            if learning_plan:
                weekly_schedule = learning_plan.get('plan_content', {}).get('weekly_schedule', [])
                for week_idx, week in enumerate(weekly_schedule):
                    session_details = week.get('session_details', [])
                    for session_idx, session in enumerate(session_details):
                        duration = session.get('duration_minutes', 5)
                        if isinstance(duration, float) and duration != int(duration):
                            decimal_durations_found.append({
                                'location': f'learning_plan_week_{week_idx}_session_{session_idx}',
                                'duration': duration,
                                'session_number': session.get('global_session_number', 'unknown')
                            })
            
            # Check conversation sessions
            conversation_sessions = await database["conversation_sessions"].find({
                "user_id": TARGET_USER_ID
            }).to_list(length=None)
            
            for idx, session in enumerate(conversation_sessions):
                duration = session.get('duration_minutes', 0)
                if isinstance(duration, float) and duration != int(duration):
                    decimal_durations_found.append({
                        'location': f'conversation_session_{idx}',
                        'duration': duration,
                        'session_id': str(session.get('_id', 'unknown'))
                    })
            
            # Check regular sessions
            regular_sessions = await database["sessions"].find({
                "user_id": TARGET_USER_ID
            }).to_list(length=None)
            
            for idx, session in enumerate(regular_sessions):
                duration = session.get('duration_minutes', 0)
                if isinstance(duration, float) and duration != int(duration):
                    decimal_durations_found.append({
                        'location': f'regular_session_{idx}',
                        'duration': duration,
                        'session_id': str(session.get('_id', 'unknown'))
                    })
            
            # Check user data
            user = await database["users"].find_one({"_id": ObjectId(TARGET_USER_ID)})
            if user:
                practice_minutes = user.get('practice_minutes_used', 0.0)
                if isinstance(practice_minutes, float) and practice_minutes != int(practice_minutes):
                    decimal_durations_found.append({
                        'location': 'user_practice_minutes_used',
                        'duration': practice_minutes
                    })
            
            if decimal_durations_found:
                print(f"❌ Found {len(decimal_durations_found)} decimal durations:")
                for decimal in decimal_durations_found:
                    print(f"   {decimal['location']}: {decimal['duration']}")
            else:
                print("✅ No decimal durations found - all durations are integers!")
            
            self.validation_results['decimal_durations'] = {
                'found': len(decimal_durations_found),
                'details': decimal_durations_found
            }
            
        except Exception as e:
            print(f"❌ Error validating decimal durations: {e}")
            self.validation_results['decimal_durations'] = {'error': str(e)}
    
    async def _generate_validation_report(self):
        """Generate comprehensive validation report"""
        print("\n📋 STEP 6: GENERATING VALIDATION REPORT")
        print("-" * 40)
        
        report = {
            'validation_timestamp': datetime.utcnow().isoformat(),
            'target_user': {
                'user_id': TARGET_USER_ID,
                'email': TARGET_USER_EMAIL,
                'learning_plan_id': TARGET_LEARNING_PLAN_ID
            },
            'database': 'PRODUCTION (Railway MongoDB)',
            'validation_results': self.validation_results
        }
        
        # Save report to file
        report_filename = f"production_validation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"✅ Validation report saved to: {report_filename}")
        
        # Generate summary
        print(f"\n📊 VALIDATION SUMMARY:")
        
        user_sub = self.validation_results.get('user_subscription', {})
        if user_sub.get('found'):
            validation = user_sub.get('validation', {})
            sessions_ok = validation.get('sessions_correct', False)
            minutes_ok = validation.get('minutes_correct', False)
            print(f"   User Subscription: {'✅' if sessions_ok and minutes_ok else '❌'}")
            print(f"     Sessions: {'✅' if sessions_ok else '❌'}")
            print(f"     Minutes: {'✅' if minutes_ok else '❌'}")
        
        learning_plan_ok = self.validation_results.get('learning_plan', {}).get('found', False)
        print(f"   Learning Plan: {'✅' if learning_plan_ok else '❌'}")
        
        session_13_ok = self.validation_results.get('session_13', {}).get('found', False)
        print(f"   Session 13: {'✅' if session_13_ok else '❌'}")
        
        duration_calc = self.validation_results.get('duration_calculations', {})
        duration_ok = duration_calc.get('minutes_match', False) and duration_calc.get('sessions_match', False)
        print(f"   Duration Calculations: {'✅' if duration_ok else '❌'}")
        
        decimal_dur = self.validation_results.get('decimal_durations', {})
        no_decimals = decimal_dur.get('found', 1) == 0
        print(f"   No Decimal Durations: {'✅' if no_decimals else '❌'}")
        
        # Overall validation result
        all_checks_passed = (
            user_sub.get('validation', {}).get('sessions_correct', False) and
            user_sub.get('validation', {}).get('minutes_correct', False) and
            learning_plan_ok and
            session_13_ok and
            duration_ok and
            no_decimals
        )
        
        print(f"\n🎯 OVERALL VALIDATION: {'✅ PASSED' if all_checks_passed else '❌ FAILED'}")
        
        self.validation_results['overall_validation'] = {
            'passed': all_checks_passed,
            'report_filename': report_filename
        }

async def main():
    """Main validation function"""
    print("🚀 Starting Production Database Validation...")
    print("⚠️  IMPORTANT: This connects to PRODUCTION Railway MongoDB!")
    
    validation = ProductionValidation()
    results = await validation.validate_production_fix()
    
    print("\n" + "="*60)
    print("🎯 PRODUCTION VALIDATION COMPLETE")
    print("="*60)
    
    overall_passed = results.get('overall_validation', {}).get('passed', False)
    report_file = results.get('overall_validation', {}).get('report_filename', 'No report')
    
    print(f"Overall Result: {'✅ ALL CHECKS PASSED' if overall_passed else '❌ SOME CHECKS FAILED'}")
    print(f"Report File: {report_file}")
    
    if overall_passed:
        print("\n🎉 SUCCESS: All duration tracking issues have been resolved in production!")
        print("   - User Ali Pala's data is correct")
        print("   - Session 13 exists and is properly recorded")
        print("   - Duration calculations are accurate")
        print("   - No decimal durations found")
    else:
        print("\n⚠️  WARNING: Some validation checks failed")
        print("   Please review the detailed report for specific issues")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
