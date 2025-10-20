"""
OpenAI Organization Costs API Integration

This module provides functionality to fetch actual costs from OpenAI's organization costs API.
Reference: https://platform.openai.com/docs/api-reference/organization/costs
"""

import os
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


async def fetch_organization_costs(
    start_time: int,
    end_time: Optional[int] = None,
    limit: int = 1
) -> Optional[Dict[str, Any]]:
    """
    Fetch organization costs from OpenAI API for a specific time range.
    
    Args:
        start_time: Unix timestamp (seconds) for the start of the query range (inclusive)
        end_time: Unix timestamp (seconds) for the end of the query range (exclusive). 
                  If None, API will return daily bucket containing start_time.
        limit: Number of buckets to return (default: 1)
    
    Returns:
        Dictionary containing cost data or None if request fails
        
    Example response:
    {
        "object": "page",
        "data": [
            {
                "object": "bucket",
                "start_time": 1730419200,
                "end_time": 1730505600,
                "results": [
                    {
                        "object": "organization.costs.result",
                        "amount": {
                            "value": 0.06,
                            "currency": "usd"
                        },
                        "line_item": null,
                        "project_id": null
                    }
                ]
            }
        ],
        "has_more": false,
        "next_page": null
    }
    """
    try:
        # Get OpenAI admin key from environment
        admin_key = os.getenv("OPENAI_ADMIN_KEY")
        
        if not admin_key:
            logger.warning("[ORG_COSTS] OPENAI_ADMIN_KEY not configured - skipping organization cost fetch")
            return None
        
        # Build API URL with query parameters
        # Only include end_time if provided, otherwise let API use daily bucketing
        if end_time is not None:
            url = f"https://api.openai.com/v1/organization/costs?start_time={start_time}&end_time={end_time}&limit={limit}"
            logger.info(f"[ORG_COSTS] Fetching costs for time range: {start_time} to {end_time}")
        else:
            url = f"https://api.openai.com/v1/organization/costs?start_time={start_time}&limit={limit}"
            logger.info(f"[ORG_COSTS] Fetching costs for start_time: {start_time} (using daily bucket)")
        
        # Make request to OpenAI API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {admin_key}",
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )
        
        if response.status_code != 200:
            logger.error(f"[ORG_COSTS] API request failed with status {response.status_code}: {response.text}")
            return None
        
        data = response.json()
        
        # Extract total cost from response
        if data and "data" in data and len(data["data"]) > 0:
            bucket = data["data"][0]
            results = bucket.get("results", [])
            
            if results and len(results) > 0:
                amount_data = results[0].get("amount", {})
                cost_value = amount_data.get("value", 0.0)
                currency = amount_data.get("currency", "usd")
                
                logger.info(f"[ORG_COSTS] ✅ Fetched organization cost: ${cost_value} {currency.upper()}")
                
                return {
                    "cost": cost_value,
                    "currency": currency,
                    "start_time": bucket.get("start_time"),
                    "end_time": bucket.get("end_time"),
                    "raw_response": data
                }
        
        logger.warning("[ORG_COSTS] No cost data found in API response")
        return None
        
    except httpx.TimeoutException:
        logger.error("[ORG_COSTS] Request timeout while fetching organization costs")
        return None
    except Exception as e:
        logger.error(f"[ORG_COSTS] Error fetching organization costs: {str(e)}")
        return None


def datetime_to_unix_timestamp(dt: datetime) -> int:
    """
    Convert datetime to Unix timestamp (seconds since epoch).
    
    Args:
        dt: datetime object (should be timezone-aware)
    
    Returns:
        Unix timestamp as integer
    """
    # Ensure datetime is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return int(dt.timestamp())


def unix_timestamp_to_datetime(timestamp: int) -> datetime:
    """
    Convert Unix timestamp to datetime object.
    
    Args:
        timestamp: Unix timestamp (seconds since epoch)
    
    Returns:
        Timezone-aware datetime object in UTC
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)
