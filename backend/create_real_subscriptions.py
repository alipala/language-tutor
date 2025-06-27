import asyncio
import os
import stripe
from database import database
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
print(f"🔑 Stripe API Key loaded: {stripe.api_key[:20]}..." if stripe.api_key else "❌ No Stripe API key found")

async def create_real_subscriptions():
    """Create real Stripe subscriptions for test users"""
    
    print("🚀 Creating REAL Stripe subscriptions for test users...")
    
    # John Monthly - Monthly Fluency Builder subscription
    john_customer_id = "cus_SZ9XawU9BEMA9a"
    john_price_id = "price_1Re01yJcquSiYwWNJRg7nyce"  # Monthly Fluency Builder
    
    # Jane Yearly - Yearly Fluency Builder subscription  
    jane_customer_id = "cus_SZ9YpIsvjT8eYJ"
    jane_price_id = "price_1Re06kJcquSiYwWN89Ra57wC"  # Yearly Fluency Builder
    
    try:
        # Create subscription for John Monthly
        print(f"\n📝 Creating subscription for John Monthly...")
        print(f"   Customer: {john_customer_id}")
        print(f"   Price: {john_price_id} (Monthly Fluency Builder)")
        
        john_subscription = stripe.Subscription.create(
            customer=john_customer_id,
            items=[
                {
                    "price": john_price_id,
                },
            ],
            payment_behavior="default_incomplete",
            payment_settings={"save_default_payment_method": "on_subscription"},
            expand=["latest_invoice.payment_intent"],
        )
        
        print(f"✅ John's subscription created: {john_subscription.id}")
        print(f"   Status: {john_subscription.status}")
        
        # Create subscription for Jane Yearly
        print(f"\n📝 Creating subscription for Jane Yearly...")
        print(f"   Customer: {jane_customer_id}")
        print(f"   Price: {jane_price_id} (Yearly Fluency Builder)")
        
        jane_subscription = stripe.Subscription.create(
            customer=jane_customer_id,
            items=[
                {
                    "price": jane_price_id,
                },
            ],
            payment_behavior="default_incomplete",
            payment_settings={"save_default_payment_method": "on_subscription"},
            expand=["latest_invoice.payment_intent"],
        )
        
        print(f"✅ Jane's subscription created: {jane_subscription.id}")
        print(f"   Status: {jane_subscription.status}")
        
        # For test mode, let's create test payment methods and complete the payments
        print(f"\n💳 Creating test payment methods and completing payments...")
        
        # Create test payment method for John
        john_pm = stripe.PaymentMethod.create(
            type="card",
            card={
                "number": "4242424242424242",
                "exp_month": 12,
                "exp_year": 2025,
                "cvc": "123",
            },
        )
        
        # Attach payment method to John's customer
        john_pm.attach(customer=john_customer_id)
        
        # Create test payment method for Jane
        jane_pm = stripe.PaymentMethod.create(
            type="card",
            card={
                "number": "4242424242424242",
                "exp_month": 12,
                "exp_year": 2025,
                "cvc": "123",
            },
        )
        
        # Attach payment method to Jane's customer
        jane_pm.attach(customer=jane_customer_id)
        
        # Update subscriptions with payment methods
        john_updated = stripe.Subscription.modify(
            john_subscription.id,
            default_payment_method=john_pm.id,
        )
        
        jane_updated = stripe.Subscription.modify(
            jane_subscription.id,
            default_payment_method=jane_pm.id,
        )
        
        # Try to confirm the latest invoices to complete the subscriptions
        try:
            if john_subscription.latest_invoice:
                john_invoice = stripe.Invoice.retrieve(john_subscription.latest_invoice)
                if john_invoice.payment_intent:
                    stripe.PaymentIntent.confirm(
                        john_invoice.payment_intent,
                        payment_method=john_pm.id
                    )
        except Exception as e:
            print(f"⚠️ John's payment confirmation: {str(e)}")
        
        try:
            if jane_subscription.latest_invoice:
                jane_invoice = stripe.Invoice.retrieve(jane_subscription.latest_invoice)
                if jane_invoice.payment_intent:
                    stripe.PaymentIntent.confirm(
                        jane_invoice.payment_intent,
                        payment_method=jane_pm.id
                    )
        except Exception as e:
            print(f"⚠️ Jane's payment confirmation: {str(e)}")
        
        print(f"✅ Payment methods created and attached")
        
        # Update our database with the real Stripe subscription data
        print(f"\n💾 Updating database with real subscription data...")
        
        # Update John in database
        john_update = {
            "subscription_status": john_updated.status,
            "subscription_id": john_updated.id,
            "subscription_plan": "fluency_builder",
            "subscription_period": "monthly",
            "subscription_price_id": john_price_id,
            "stripe_customer_id": john_customer_id
        }
        
        result1 = await database["users"].update_one(
            {"_id": ObjectId("685c6d8aa3412c0964ef47d0")},
            {"$set": john_update}
        )
        
        # Update Jane in database
        jane_update = {
            "subscription_status": jane_updated.status,
            "subscription_id": jane_updated.id,
            "subscription_plan": "fluency_builder",
            "subscription_period": "annual",
            "subscription_price_id": jane_price_id,
            "stripe_customer_id": jane_customer_id
        }
        
        result2 = await database["users"].update_one(
            {"_id": ObjectId("685c6dd2a3412c0964ef47d3")},
            {"$set": jane_update}
        )
        
        print(f"✅ Database updated - John: {result1.modified_count} record, Jane: {result2.modified_count} record")
        
        # Final verification
        print(f"\n🎉 REAL STRIPE SUBSCRIPTIONS CREATED SUCCESSFULLY!")
        print(f"\n📊 Final Status:")
        print(f"   John Monthly:")
        print(f"     - Subscription ID: {john_updated.id}")
        print(f"     - Status: {john_updated.status}")
        print(f"     - Plan: Monthly Fluency Builder")
        print(f"     - Customer: {john_customer_id}")
        
        print(f"\n   Jane Yearly:")
        print(f"     - Subscription ID: {jane_updated.id}")
        print(f"     - Status: {jane_updated.status}")
        print(f"     - Plan: Yearly Fluency Builder")
        print(f"     - Customer: {jane_customer_id}")
        
        print(f"\n🔍 You can now verify these subscriptions in your Stripe Dashboard!")
        
    except stripe.error.StripeError as e:
        print(f"❌ Stripe error: {str(e)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(create_real_subscriptions())
