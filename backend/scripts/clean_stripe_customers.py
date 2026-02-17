"""
Clean Stripe Customers Script
Safely delete orphaned Stripe customers after MongoDB user deletion

Usage:
    python scripts/clean_stripe_customers.py

Features:
    - Lists all Stripe customers first
    - Confirms before deletion
    - Dry-run mode (preview without deleting)
    - Test mode by default (safer)
"""

import os
import sys

# Check if stripe is installed
try:
    import stripe
except ImportError:
    print("❌ Error: stripe package not installed")
    print("Run: pip install stripe")
    sys.exit(1)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


def list_customers(test_mode=True):
    """List all Stripe customers"""

    # Use test or live API key
    if test_mode:
        api_key = os.getenv("STRIPE_SECRET_KEY")  # Test key
        mode = "TEST MODE"
    else:
        api_key = os.getenv("STRIPE_SECRET_KEY_LIVE")  # Live key (if you have one)
        mode = "LIVE MODE"

    if not api_key:
        print(f"❌ Error: Stripe API key not found in .env")
        return []

    stripe.api_key = api_key

    print(f"\n🔍 Fetching customers from Stripe ({mode})...")

    try:
        customers = stripe.Customer.list(limit=100)

        print(f"\n📊 Found {len(customers.data)} customers:\n")
        print(f"{'ID':<25} {'Email':<35} {'Created':<20}")
        print("-" * 80)

        for customer in customers.data:
            email = customer.get("email", "No email")
            created = customer.get("created", 0)

            # Convert timestamp to readable date
            from datetime import datetime
            created_date = datetime.fromtimestamp(created).strftime('%Y-%m-%d %H:%M')

            print(f"{customer.id:<25} {email:<35} {created_date:<20}")

        return customers.data

    except Exception as e:
        print(f"❌ Error fetching customers: {str(e)}")
        return []


def delete_customers(customers, dry_run=True):
    """Delete Stripe customers"""

    if len(customers) == 0:
        print("\n✅ No customers to delete")
        return 0

    if dry_run:
        print(f"\n🔍 DRY RUN MODE - No actual deletions will occur")
        print(f"Would delete {len(customers)} customers:\n")

        for customer in customers:
            email = customer.get("email", "No email")
            print(f"  - {customer.id} ({email})")

        print(f"\n💡 To actually delete, run with dry_run=False")
        return 0

    # Real deletion - ask for confirmation
    print(f"\n⚠️  WARNING: About to DELETE {len(customers)} Stripe customers!")
    print("This action cannot be undone!")

    confirmation = input(f"\nType 'DELETE {len(customers)} CUSTOMERS' to confirm: ")
    if confirmation != f"DELETE {len(customers)} CUSTOMERS":
        print("❌ Operation cancelled")
        return 0

    deleted_count = 0
    error_count = 0

    print(f"\n🗑️  Deleting customers...\n")

    for customer in customers:
        email = customer.get("email", "No email")
        try:
            stripe.Customer.delete(customer.id)
            print(f"  ✓ Deleted: {customer.id} ({email})")
            deleted_count += 1
        except Exception as e:
            print(f"  ✗ Error deleting {customer.id}: {str(e)}")
            error_count += 1

    print(f"\n✅ Cleanup complete:")
    print(f"   - Deleted: {deleted_count} customers")
    print(f"   - Errors: {error_count}")

    return deleted_count


def main():
    """Main entry point"""

    print("\n" + "=" * 80)
    print("🧹 STRIPE CUSTOMER CLEANUP SCRIPT")
    print("=" * 80)

    print("\nOptions:")
    print("  1. List customers (TEST MODE)")
    print("  2. Delete customers - DRY RUN (TEST MODE)")
    print("  3. Delete customers - REAL DELETION (TEST MODE)")
    print("  4. List customers (LIVE MODE)")
    print("  5. Delete customers - REAL DELETION (LIVE MODE)")
    print("  6. Cancel")
    print()

    choice = input("Enter your choice (1-6): ").strip()

    if choice == "1":
        customers = list_customers(test_mode=True)
        print(f"\n✅ Listed {len(customers)} test mode customers")

    elif choice == "2":
        customers = list_customers(test_mode=True)
        if customers:
            delete_customers(customers, dry_run=True)

    elif choice == "3":
        customers = list_customers(test_mode=True)
        if customers:
            delete_customers(customers, dry_run=False)

    elif choice == "4":
        customers = list_customers(test_mode=False)
        print(f"\n✅ Listed {len(customers)} live mode customers")

    elif choice == "5":
        print("\n⚠️  WARNING: LIVE MODE DELETION IS PERMANENT!")
        confirm = input("Type 'I UNDERSTAND' to continue: ")
        if confirm == "I UNDERSTAND":
            customers = list_customers(test_mode=False)
            if customers:
                delete_customers(customers, dry_run=False)
        else:
            print("❌ Operation cancelled")

    elif choice == "6":
        print("\n❌ Operation cancelled")

    else:
        print("\n❌ Invalid choice")

    print()


if __name__ == "__main__":
    main()
