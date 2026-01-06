"""
Cost Tracking Module for CrewAI Challenge Generation
====================================================

Tracks OpenAI API usage and costs for challenge generation.
Logs to MongoDB for analysis and reporting.
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional
from database import database


# Model pricing (as of 2026-01-06)
MODEL_PRICING = {
    "gpt-4o": {
        "input": 2.50 / 1_000_000,   # $2.50 per 1M tokens
        "output": 10.00 / 1_000_000,  # $10.00 per 1M tokens
    },
    "gpt-4o-mini": {
        "input": 0.15 / 1_000_000,    # $0.15 per 1M tokens
        "output": 0.60 / 1_000_000,   # $0.60 per 1M tokens
    },
    "gpt-4-turbo": {
        "input": 10.00 / 1_000_000,   # $10.00 per 1M tokens
        "output": 30.00 / 1_000_000,  # $30.00 per 1M tokens
    },
    "gpt-3.5-turbo": {
        "input": 0.50 / 1_000_000,    # $0.50 per 1M tokens
        "output": 1.50 / 1_000_000,   # $1.50 per 1M tokens
    },
}


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int
) -> float:
    """
    Calculate cost for API usage

    Args:
        model: Model name (e.g., "gpt-4o")
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Total cost in USD
    """
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["gpt-4o"])

    input_cost = input_tokens * pricing["input"]
    output_cost = output_tokens * pricing["output"]

    return input_cost + output_cost


async def log_challenge_generation_cost(
    operation_type: str,
    user_id: Optional[str],
    model: str,
    input_tokens: int,
    output_tokens: int,
    challenges_generated: int,
    language: str,
    level: str,
    challenge_type: Optional[str] = None,
    duration_seconds: float = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Log challenge generation cost to database

    Args:
        operation_type: "user_pool" or "reference_pool"
        user_id: User ID (or "reference_user" for reference challenges)
        model: Model used
        input_tokens: Input tokens used
        output_tokens: Output tokens used
        challenges_generated: Number of challenges generated
        language: Language
        level: CEFR level
        challenge_type: Optional challenge type
        duration_seconds: How long it took
        metadata: Additional metadata

    Returns:
        Cost log entry
    """
    try:
        # Calculate cost
        cost = calculate_cost(model, input_tokens, output_tokens)

        # Create log entry
        log_entry = {
            "operation_type": operation_type,
            "user_id": user_id,
            "model": model,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens
            },
            "cost_usd": round(cost, 6),
            "challenges_generated": challenges_generated,
            "cost_per_challenge": round(cost / challenges_generated, 6) if challenges_generated > 0 else 0,
            "language": language,
            "level": level,
            "challenge_type": challenge_type,
            "duration_seconds": round(duration_seconds, 2),
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }

        # Insert to database
        await database.challenge_generation_costs.insert_one(log_entry)

        # Print summary
        print(f"[COST] 💰 Operation: {operation_type}")
        print(f"[COST] 🤖 Model: {model}")
        print(f"[COST] 📊 Tokens: {input_tokens:,} in + {output_tokens:,} out = {input_tokens + output_tokens:,} total")
        print(f"[COST] 💵 Cost: ${cost:.6f} (${cost / challenges_generated:.6f} per challenge)")
        print(f"[COST] ⏱️  Duration: {duration_seconds:.2f}s")
        print(f"[COST] ✅ Challenges: {challenges_generated}")

        return log_entry

    except Exception as e:
        print(f"[COST] ❌ Error logging cost: {str(e)}")
        return {}


async def get_daily_costs(date: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Get cost summary for a specific day

    Args:
        date: Date to query (defaults to today)

    Returns:
        Cost summary
    """
    if date is None:
        date = datetime.utcnow()

    # Start and end of day
    start_of_day = datetime(date.year, date.month, date.day, 0, 0, 0)
    end_of_day = datetime(date.year, date.month, date.day, 23, 59, 59)

    # Query costs
    pipeline = [
        {
            "$match": {
                "timestamp": {
                    "$gte": start_of_day,
                    "$lte": end_of_day
                }
            }
        },
        {
            "$group": {
                "_id": "$operation_type",
                "total_cost": {"$sum": "$cost_usd"},
                "total_tokens": {"$sum": "$tokens.total"},
                "total_challenges": {"$sum": "$challenges_generated"},
                "count": {"$sum": 1}
            }
        }
    ]

    results = await database.challenge_generation_costs.aggregate(pipeline).to_list(length=None)

    # Format results
    summary = {
        "date": start_of_day.strftime("%Y-%m-%d"),
        "operations": {},
        "total_cost": 0,
        "total_tokens": 0,
        "total_challenges": 0
    }

    for result in results:
        op_type = result["_id"]
        summary["operations"][op_type] = {
            "cost": round(result["total_cost"], 6),
            "tokens": result["total_tokens"],
            "challenges": result["total_challenges"],
            "api_calls": result["count"]
        }
        summary["total_cost"] += result["total_cost"]
        summary["total_tokens"] += result["total_tokens"]
        summary["total_challenges"] += result["total_challenges"]

    summary["total_cost"] = round(summary["total_cost"], 6)

    return summary


async def get_monthly_costs(year: int, month: int) -> Dict[str, Any]:
    """
    Get cost summary for a specific month

    Args:
        year: Year
        month: Month (1-12)

    Returns:
        Monthly cost summary
    """
    from calendar import monthrange

    # Start and end of month
    start_of_month = datetime(year, month, 1, 0, 0, 0)
    days_in_month = monthrange(year, month)[1]
    end_of_month = datetime(year, month, days_in_month, 23, 59, 59)

    # Query costs
    pipeline = [
        {
            "$match": {
                "timestamp": {
                    "$gte": start_of_month,
                    "$lte": end_of_month
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "operation_type": "$operation_type",
                    "day": {"$dayOfMonth": "$timestamp"}
                },
                "daily_cost": {"$sum": "$cost_usd"},
                "daily_tokens": {"$sum": "$tokens.total"},
                "daily_challenges": {"$sum": "$challenges_generated"}
            }
        },
        {
            "$group": {
                "_id": "$_id.operation_type",
                "total_cost": {"$sum": "$daily_cost"},
                "total_tokens": {"$sum": "$daily_tokens"},
                "total_challenges": {"$sum": "$daily_challenges"},
                "days_with_activity": {"$sum": 1}
            }
        }
    ]

    results = await database.challenge_generation_costs.aggregate(pipeline).to_list(length=None)

    # Format results
    summary = {
        "year": year,
        "month": month,
        "month_name": datetime(year, month, 1).strftime("%B"),
        "operations": {},
        "total_cost": 0,
        "total_tokens": 0,
        "total_challenges": 0
    }

    for result in results:
        op_type = result["_id"]
        summary["operations"][op_type] = {
            "cost": round(result["total_cost"], 6),
            "tokens": result["total_tokens"],
            "challenges": result["total_challenges"],
            "days_active": result["days_with_activity"]
        }
        summary["total_cost"] += result["total_cost"]
        summary["total_tokens"] += result["total_tokens"]
        summary["total_challenges"] += result["total_challenges"]

    summary["total_cost"] = round(summary["total_cost"], 6)

    return summary


async def print_cost_report():
    """Print a formatted cost report for today"""
    today_costs = await get_daily_costs()

    print("\n" + "="*80)
    print(f"💰 COST REPORT - {today_costs['date']}")
    print("="*80)

    if today_costs["operations"]:
        for op_type, data in today_costs["operations"].items():
            print(f"\n{op_type.upper()}:")
            print(f"  Cost: ${data['cost']:.6f}")
            print(f"  Challenges: {data['challenges']}")
            print(f"  Tokens: {data['tokens']:,}")
            print(f"  API Calls: {data['api_calls']}")
    else:
        print("\nNo operations today")

    print(f"\nTOTAL: ${today_costs['total_cost']:.6f}")
    print("="*80 + "\n")
