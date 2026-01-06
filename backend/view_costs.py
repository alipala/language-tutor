#!/usr/bin/env python3
"""
View Challenge Generation Costs
================================

Displays cost reports for CrewAI challenge generation.

Usage:
    python view_costs.py                  # Today's costs
    python view_costs.py today            # Today's costs
    python view_costs.py month            # This month's costs
    python view_costs.py month 2026 1     # Specific month
"""

import asyncio
import sys
from datetime import datetime
from cost_tracker import get_daily_costs, get_monthly_costs, print_cost_report


async def main():
    if len(sys.argv) == 1 or sys.argv[1] == "today":
        # Today's costs
        await print_cost_report()

    elif sys.argv[1] == "month":
        # Monthly costs
        if len(sys.argv) >= 4:
            year = int(sys.argv[2])
            month = int(sys.argv[3])
        else:
            now = datetime.utcnow()
            year = now.year
            month = now.month

        costs = await get_monthly_costs(year, month)

        print("\n" + "="*80)
        print(f"💰 MONTHLY COST REPORT - {costs['month_name']} {costs['year']}")
        print("="*80)

        if costs["operations"]:
            for op_type, data in costs["operations"].items():
                print(f"\n{op_type.upper().replace('_', ' ')}:")
                print(f"  Cost: ${data['cost']:.2f}")
                print(f"  Challenges: {data['challenges']:,}")
                print(f"  Tokens: {data['tokens']:,}")
                print(f"  Days Active: {data['days_active']}")
                print(f"  Avg per Day: ${data['cost'] / data['days_active']:.2f}")
        else:
            print("\nNo operations this month")

        print(f"\nMONTHLY TOTAL: ${costs['total_cost']:.2f}")
        print(f"Total Challenges: {costs['total_challenges']:,}")
        print(f"Total Tokens: {costs['total_tokens']:,}")
        print("="*80 + "\n")

    else:
        print("Usage:")
        print("  python view_costs.py              # Today's costs")
        print("  python view_costs.py today        # Today's costs")
        print("  python view_costs.py month        # This month")
        print("  python view_costs.py month 2026 1 # January 2026")


if __name__ == "__main__":
    asyncio.run(main())
