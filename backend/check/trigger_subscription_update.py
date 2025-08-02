import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def trigger_subscription_update():
    """Trigger a subscription update to fix the dates"""
    
    # The user's Stripe customer ID
    customer_id = "cus_SaHw3oXyZFueFK"
    
    print(f"Looking for subscriptions for customer: {customer_id}")
    
    # Get the subscription
    subscriptions = stripe.Subscription.list(
        customer=customer_id,
        status="active",
        limit=1
    )
    
    if not subscriptions.data:
        print("No active subscriptions found")
        return
    
    subscription = subscriptions.data[0]
    print(f"Found subscription: {subscription.id}")
    print(f"Current period start: {subscription.current_period_start}")
    print(f"Current period end: {subscription.current_period_end}")
    
    # Convert to readable dates
    from datetime import datetime, timezone
    start_date = datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc)
    end_date = datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc)
    
    print(f"Start date: {start_date}")
    print(f"End date: {end_date}")
    
    # Trigger an update by adding metadata (this will trigger the webhook)
    print("Triggering subscription update webhook...")
    updated_subscription = stripe.Subscription.modify(
        subscription.id,
        metadata={"webhook_trigger": "fix_dates", "updated_at": str(datetime.now())}
    )
    
    print(f"✅ Subscription updated successfully!")
    print(f"This should trigger the webhook to update the database with correct dates:")
    print(f"- Start: {start_date}")
    print(f"- End: {end_date}")
    print(f"- Period: Annual (1 year)")

if __name__ == "__main__":
    trigger_subscription_update()
