"""
GPT-4o Cost Tracking Module
Tracks and calculates costs for gpt-4o usage in conversation help and sentence assessment
"""
import os
from datetime import datetime, timezone
from typing import Dict, Optional
from database import database

# GPT-4o Pricing (per 1M tokens)
# Reference: https://openai.com/api/pricing/
GPT4O_PRICING = {
    "text_input": 2.50 / 1_000_000,        # $2.50 per 1M tokens
    "cached_input": 1.25 / 1_000_000,      # $1.25 per 1M tokens (50% discount)
    "text_output": 10.00 / 1_000_000,      # $10.00 per 1M tokens
}

class GPT4oCostTracker:
    """Track and calculate GPT-4o costs"""
    
    @staticmethod
    def calculate_cost(
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0
    ) -> Dict:
        """
        Calculate cost for GPT-4o usage
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cached_tokens: Number of cached input tokens (optional)
            
        Returns:
            Dict with cost breakdown
        """
        # Calculate costs
        regular_input_tokens = input_tokens - cached_tokens
        input_cost = regular_input_tokens * GPT4O_PRICING["text_input"]
        cached_cost = cached_tokens * GPT4O_PRICING["cached_input"]
        output_cost = output_tokens * GPT4O_PRICING["text_output"]
        total_cost = input_cost + cached_cost + output_cost
        
        return {
            "model": "gpt-4o",
            "input_tokens": input_tokens,
            "regular_input_tokens": regular_input_tokens,
            "cached_input_tokens": cached_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "input_cost": input_cost,
            "cached_cost": cached_cost,
            "output_cost": output_cost,
            "total_cost": total_cost
        }
    
    @staticmethod
    async def log_usage(
        user_id: Optional[str],
        session_id: str,
        usage_type: str,  # "conversation_help", "sentence_assessment", "speaking_assessment"
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
        language: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> str:
        """
        Log GPT-4o usage to database
        
        Args:
            user_id: User ID (optional for guest users)
            session_id: Session ID
            usage_type: Type of usage
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cached_tokens: Number of cached tokens
            language: Language being practiced
            context: Additional context data
            
        Returns:
            Log ID
        """
        try:
            # Calculate cost
            cost_data = GPT4oCostTracker.calculate_cost(
                input_tokens, output_tokens, cached_tokens
            )
            
            # Create log document
            gpt4o_logs_collection = database.gpt4o_usage_logs
            log_doc = {
                "user_id": user_id,
                "session_id": session_id,
                "usage_type": usage_type,
                "model": "gpt-4o",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cached_tokens": cached_tokens,
                "total_tokens": input_tokens + output_tokens,
                "language": language,
                "context": context or {},
                "cost_data": cost_data,
                "total_cost": cost_data["total_cost"],
                "logged_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = await gpt4o_logs_collection.insert_one(log_doc)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ [GPT4O_COST] Error logging usage: {str(e)}")
            return None
    
    @staticmethod
    async def get_session_costs(session_id: str) -> Dict:
        """
        Get all GPT-4o costs for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict with cost summary
        """
        try:
            gpt4o_logs_collection = database.gpt4o_usage_logs
            
            # Get all logs for this session
            logs = await gpt4o_logs_collection.find({"session_id": session_id}).to_list(None)
            
            # Calculate totals
            total_cost = sum(log.get("total_cost", 0) for log in logs)
            total_tokens = sum(log.get("total_tokens", 0) for log in logs)
            
            # Group by usage type
            usage_breakdown = {}
            for log in logs:
                usage_type = log.get("usage_type", "unknown")
                if usage_type not in usage_breakdown:
                    usage_breakdown[usage_type] = {
                        "count": 0,
                        "total_cost": 0,
                        "total_tokens": 0
                    }
                usage_breakdown[usage_type]["count"] += 1
                usage_breakdown[usage_type]["total_cost"] += log.get("total_cost", 0)
                usage_breakdown[usage_type]["total_tokens"] += log.get("total_tokens", 0)
            
            return {
                "session_id": session_id,
                "total_gpt4o_calls": len(logs),
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "usage_breakdown": usage_breakdown
            }
            
        except Exception as e:
            print(f"❌ [GPT4O_COST] Error getting session costs: {str(e)}")
            return {
                "error": str(e),
                "total_cost": 0
            }
    
    @staticmethod
    async def get_user_costs(
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Get GPT-4o costs for a user within a date range
        
        Args:
            user_id: User ID
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            Dict with cost summary
        """
        try:
            gpt4o_logs_collection = database.gpt4o_usage_logs
            
            # Build query
            query = {"user_id": user_id}
            if start_date or end_date:
                query["logged_at"] = {}
                if start_date:
                    query["logged_at"]["$gte"] = start_date.isoformat()
                if end_date:
                    query["logged_at"]["$lte"] = end_date.isoformat()
            
            # Get logs
            logs = await gpt4o_logs_collection.find(query).to_list(None)
            
            # Calculate totals
            total_cost = sum(log.get("total_cost", 0) for log in logs)
            total_tokens = sum(log.get("total_tokens", 0) for log in logs)
            
            # Group by usage type
            usage_breakdown = {}
            for log in logs:
                usage_type = log.get("usage_type", "unknown")
                if usage_type not in usage_breakdown:
                    usage_breakdown[usage_type] = {
                        "count": 0,
                        "total_cost": 0,
                        "total_tokens": 0
                    }
                usage_breakdown[usage_type]["count"] += 1
                usage_breakdown[usage_type]["total_cost"] += log.get("total_cost", 0)
                usage_breakdown[usage_type]["total_tokens"] += log.get("total_tokens", 0)
            
            return {
                "user_id": user_id,
                "total_gpt4o_calls": len(logs),
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "average_cost_per_call": total_cost / len(logs) if logs else 0,
                "usage_breakdown": usage_breakdown
            }
            
        except Exception as e:
            print(f"❌ [GPT4O_COST] Error getting user costs: {str(e)}")
            return {
                "error": str(e),
                "total_cost": 0
            }
