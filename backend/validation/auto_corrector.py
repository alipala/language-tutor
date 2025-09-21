#!/usr/bin/env python3
"""
Auto Corrector
Coordinates validation checks and applies automatic fixes to prevent dashboard bugs
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from .subscription_validator import SubscriptionValidator
from .session_validator import SessionValidator

logger = logging.getLogger(__name__)

class AutoCorrector:
    """Coordinates validation checks and applies automatic corrections"""
    
    @staticmethod
    async def run_comprehensive_validation(user_id: str) -> Dict[str, Any]:
        """
        Run all validation checks for a user and provide comprehensive report
        """
        try:
            validation_report = {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "unknown",
                "validations": {},
                "issues_found": [],
                "fixes_available": [],
                "confidence_impact": "neutral"
            }
            
            logger.info(f"[AUTO_CORRECTOR] Running comprehensive validation for user {user_id}")
            
            # 1. Subscription Period Validation
            try:
                subscription_validation = await SubscriptionValidator.validate_subscription_period(user_id)
                validation_report["validations"]["subscription_period"] = subscription_validation
                
                if not subscription_validation.get("is_valid"):
                    validation_report["issues_found"].extend([
                        f"Subscription: {issue}" for issue in subscription_validation.get("issues", [])
                    ])
                    validation_report["fixes_available"].extend([
                        f"Subscription: {fix}" for fix in subscription_validation.get("corrections_needed", [])
                    ])
                
            except Exception as e:
                logger.error(f"[AUTO_CORRECTOR] Subscription validation failed: {str(e)}")
                validation_report["validations"]["subscription_period"] = {"error": str(e)}
                validation_report["issues_found"].append("Subscription validation failed")
            
            # 2. Session Completeness Validation
            try:
                session_validation = await SessionValidator.validate_session_completeness(user_id)
                validation_report["validations"]["session_completeness"] = session_validation
                
                if not session_validation.get("is_valid"):
                    validation_report["issues_found"].extend([
                        f"Sessions: {disc['type']} ({disc['difference']})" 
                        for disc in session_validation.get("discrepancies", [])
                    ])
                    validation_report["fixes_available"].extend([
                        f"Sessions: {fix}" for fix in session_validation.get("corrections_needed", [])
                    ])
                
            except Exception as e:
                logger.error(f"[AUTO_CORRECTOR] Session validation failed: {str(e)}")
                validation_report["validations"]["session_completeness"] = {"error": str(e)}
                validation_report["issues_found"].append("Session validation failed")
            
            # 3. Missing Sessions Detection
            try:
                missing_sessions = await SessionValidator.detect_missing_sessions(user_id)
                validation_report["validations"]["missing_sessions"] = missing_sessions
                
                potential_issues = missing_sessions.get("potential_issues", [])
                if potential_issues:
                    validation_report["issues_found"].extend([
                        f"Missing sessions: {issue}" for issue in potential_issues
                    ])
                
            except Exception as e:
                logger.error(f"[AUTO_CORRECTOR] Missing sessions detection failed: {str(e)}")
                validation_report["validations"]["missing_sessions"] = {"error": str(e)}
            
            # Determine overall status
            if not validation_report["issues_found"]:
                validation_report["overall_status"] = "healthy"
                validation_report["confidence_impact"] = "positive"
            elif len(validation_report["fixes_available"]) >= len(validation_report["issues_found"]):
                validation_report["overall_status"] = "fixable"
                validation_report["confidence_impact"] = "neutral"
            else:
                validation_report["overall_status"] = "problematic"
                validation_report["confidence_impact"] = "negative"
            
            logger.info(f"[AUTO_CORRECTOR] Validation complete for user {user_id}: "
                       f"{validation_report['overall_status']} "
                       f"({len(validation_report['issues_found'])} issues, "
                       f"{len(validation_report['fixes_available'])} fixes available)")
            
            return validation_report
            
        except Exception as e:
            logger.error(f"[AUTO_CORRECTOR] Comprehensive validation failed: {str(e)}")
            return {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "error",
                "error": str(e)
            }
    
    @staticmethod
    async def apply_automatic_fixes(user_id: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        Apply all available automatic fixes for a user
        """
        try:
            # First, run validation to see what needs fixing
            validation_report = await AutoCorrector.run_comprehensive_validation(user_id)
            
            if validation_report.get("overall_status") == "healthy":
                return {
                    "user_id": user_id,
                    "fixes_applied": False,
                    "message": "No fixes needed - all validations passed",
                    "validation_report": validation_report
                }
            
            fix_report = {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "dry_run": dry_run,
                "fixes_attempted": [],
                "fixes_successful": [],
                "fixes_failed": [],
                "overall_success": False
            }
            
            logger.info(f"[AUTO_CORRECTOR] Applying automatic fixes for user {user_id} (dry_run: {dry_run})")
            
            # 1. Fix Subscription Period Issues
            subscription_validation = validation_report["validations"].get("subscription_period", {})
            if not subscription_validation.get("is_valid") and subscription_validation.get("corrections_needed"):
                fix_report["fixes_attempted"].append("subscription_period")
                
                if not dry_run:
                    try:
                        subscription_fix = await SubscriptionValidator.auto_fix_subscription_period(user_id)
                        if subscription_fix.get("fixes_applied"):
                            fix_report["fixes_successful"].append({
                                "type": "subscription_period",
                                "fixes": subscription_fix.get("fixes", [])
                            })
                        else:
                            fix_report["fixes_failed"].append({
                                "type": "subscription_period",
                                "reason": subscription_fix.get("message", "Unknown error")
                            })
                    except Exception as e:
                        fix_report["fixes_failed"].append({
                            "type": "subscription_period",
                            "reason": str(e)
                        })
                else:
                    # Dry run - just record what would be fixed
                    fix_report["fixes_successful"].append({
                        "type": "subscription_period",
                        "fixes": ["DRY RUN: Would fix subscription period issues"]
                    })
            
            # 2. Fix Session Discrepancies
            session_validation = validation_report["validations"].get("session_completeness", {})
            if not session_validation.get("is_valid") and session_validation.get("corrections_needed"):
                fix_report["fixes_attempted"].append("session_discrepancies")
                
                if not dry_run:
                    try:
                        session_fix = await SessionValidator.fix_session_discrepancies(user_id)
                        if session_fix.get("fixes_applied"):
                            fix_report["fixes_successful"].append({
                                "type": "session_discrepancies",
                                "fixes": session_fix.get("fixes", [])
                            })
                        else:
                            fix_report["fixes_failed"].append({
                                "type": "session_discrepancies",
                                "reason": session_fix.get("message", "Unknown error")
                            })
                    except Exception as e:
                        fix_report["fixes_failed"].append({
                            "type": "session_discrepancies",
                            "reason": str(e)
                        })
                else:
                    # Dry run - just record what would be fixed
                    fix_report["fixes_successful"].append({
                        "type": "session_discrepancies",
                        "fixes": ["DRY RUN: Would fix session data discrepancies"]
                    })
            
            # Determine overall success
            if fix_report["fixes_successful"] and not fix_report["fixes_failed"]:
                fix_report["overall_success"] = True
            elif fix_report["fixes_successful"] and len(fix_report["fixes_successful"]) > len(fix_report["fixes_failed"]):
                fix_report["overall_success"] = True  # Mostly successful
            
            success_count = len(fix_report["fixes_successful"])
            failed_count = len(fix_report["fixes_failed"])
            
            logger.info(f"[AUTO_CORRECTOR] Fixes complete for user {user_id}: "
                       f"{success_count} successful, {failed_count} failed "
                       f"(dry_run: {dry_run})")
            
            return fix_report
            
        except Exception as e:
            logger.error(f"[AUTO_CORRECTOR] Error applying automatic fixes: {str(e)}")
            return {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "overall_success": False
            }
    
    @staticmethod
    async def validate_and_fix_user(user_id: str, auto_fix: bool = True) -> Dict[str, Any]:
        """
        One-stop method to validate a user and optionally apply fixes
        """
        try:
            # Run validation first
            validation_report = await AutoCorrector.run_comprehensive_validation(user_id)
            
            result = {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "validation": validation_report,
                "fixes": None,
                "dashboard_confidence": "unknown"
            }
            
            # If issues found and auto_fix enabled, apply fixes
            if auto_fix and validation_report.get("issues_found"):
                fix_report = await AutoCorrector.apply_automatic_fixes(user_id, dry_run=False)
                result["fixes"] = fix_report
                
                # Re-run validation after fixes to confirm improvements
                if fix_report.get("overall_success"):
                    post_fix_validation = await AutoCorrector.run_comprehensive_validation(user_id)
                    result["post_fix_validation"] = post_fix_validation
                    
                    # Determine dashboard confidence impact
                    if post_fix_validation.get("overall_status") == "healthy":
                        result["dashboard_confidence"] = "high"
                    elif post_fix_validation.get("overall_status") == "fixable":
                        result["dashboard_confidence"] = "medium"
                    else:
                        result["dashboard_confidence"] = "low"
                else:
                    result["dashboard_confidence"] = "low"
            else:
                # No fixes applied
                if validation_report.get("overall_status") == "healthy":
                    result["dashboard_confidence"] = "high"
                elif validation_report.get("overall_status") == "fixable":
                    result["dashboard_confidence"] = "medium"
                else:
                    result["dashboard_confidence"] = "low"
            
            return result
            
        except Exception as e:
            logger.error(f"[AUTO_CORRECTOR] Error in validate_and_fix_user: {str(e)}")
            return {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "dashboard_confidence": "low"
            }
    
    @staticmethod
    def get_confidence_boost_estimate(validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate how much confidence boost would be gained by fixing issues
        """
        try:
            issues_count = len(validation_report.get("issues_found", []))
            fixes_available = len(validation_report.get("fixes_available", []))
            
            if issues_count == 0:
                confidence_boost = 0
                message = "No issues found - confidence already high"
            elif fixes_available >= issues_count:
                # All issues can be fixed
                if "subscription" in str(validation_report.get("issues_found", [])).lower():
                    confidence_boost = 3  # Subscription fixes provide significant boost
                else:
                    confidence_boost = 2  # Session fixes provide moderate boost
                message = f"All {issues_count} issues can be automatically fixed"
            elif fixes_available > 0:
                # Some issues can be fixed
                confidence_boost = 1
                message = f"{fixes_available} of {issues_count} issues can be automatically fixed"
            else:
                # No automatic fixes available
                confidence_boost = 0
                message = f"{issues_count} issues found but no automatic fixes available"
            
            return {
                "confidence_boost": confidence_boost,
                "current_issues": issues_count,
                "fixable_issues": fixes_available,
                "message": message,
                "estimated_confidence_after_fix": min(95, 90 + confidence_boost)  # Current 90% + boost, max 95%
            }
            
        except Exception as e:
            logger.error(f"[AUTO_CORRECTOR] Error estimating confidence boost: {str(e)}")
            return {
                "confidence_boost": 0,
                "error": str(e)
            }

if __name__ == "__main__":
    # Test the auto corrector
    import asyncio
    
    async def test_auto_corrector():
        user_id = "688921c268819565ef1ce3dc"
        
        print("🧪 TESTING AUTO CORRECTOR")
        print("=" * 50)
        
        # Test comprehensive validation
        validation_report = await AutoCorrector.run_comprehensive_validation(user_id)
        print(f"✅ Comprehensive Validation: {validation_report['overall_status']}")
        print(f"   Issues Found: {len(validation_report['issues_found'])}")
        print(f"   Fixes Available: {len(validation_report['fixes_available'])}")
        
        # Test confidence boost estimation
        confidence_boost = AutoCorrector.get_confidence_boost_estimate(validation_report)
        print(f"✅ Confidence Boost Estimate: +{confidence_boost['confidence_boost']}%")
        print(f"   Estimated Confidence After Fix: {confidence_boost['estimated_confidence_after_fix']}%")
        
        # Test dry run fixes
        if validation_report['fixes_available']:
            print("\n🔧 Testing Dry Run Fixes...")
            dry_run_result = await AutoCorrector.apply_automatic_fixes(user_id, dry_run=True)
            print(f"   Fixes Attempted: {len(dry_run_result['fixes_attempted'])}")
            print(f"   Would Succeed: {len(dry_run_result['fixes_successful'])}")
        
        # Test full validate and fix
        print("\n🎯 Testing Full Validate and Fix...")
        full_result = await AutoCorrector.validate_and_fix_user(user_id, auto_fix=True)
        print(f"   Dashboard Confidence: {full_result['dashboard_confidence']}")
        
    asyncio.run(test_auto_corrector())
