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

async def complete_subscription_payments():
    """Complete payments for existing incomplete subscriptions"""
    
    print("💳 Completing payments for incomplete subscriptions...")
    
    # Get the latest subscription IDs from our previous runs
    john_subscription_id = "sub_1Re1TkJcquSiYwWN7qrc7BWy"  # John Monthly
    jane_subscription_id = "sub_1Re1TmJcquSiYwWNJter5qq4"  # Jane Yearly
    
    john_customer_id = "cus_SZ9XawU9BEMA9a"
    jane_customer_id = "cus_SZ9YpIsvjT8eYJ"
    
    try:
        print(f"\n🔍 Checking current subscription statuses...")
        
        # Get current subscription details
        john_sub = stripe.Subscription.retrieve(john_subscription_id)
        jane_sub = stripe.Subscription.retrieve(jane_subscription_id)
        
        print(f"   John's subscription: {john_sub.status}")
        print(f"   Jane's subscription: {jane_sub.status}")
        
        # Create payment methods using test tokens (recommended approach)
        print(f"\n💳 Creating test payment methods...")
        
        # Create payment method for John using test token
        john_pm = stripe.PaymentMethod.create(
            type="card",
            card={
                "token": "tok_visa"  # Using test token instead of raw card data
            }
        )
        print(f"✅ John's payment method created: {john_pm.id}")
        
        # Create payment method for Jane using test token  
        jane_pm = stripe.PaymentMethod.create(
            type="card",
            card={
                "token": "tok_visa"  # Using test token instead of raw card data
            }
        )
        print(f"✅ Jane's payment method created: {jane_pm.id}")
        
        # Attach payment methods to customers
        print(f"\n🔗 Attaching payment methods to customers...")
        
        john_pm.attach(customer=john_customer_id)
        jane_pm.attach(customer=jane_customer_id)
        
        print(f"✅ Payment methods attached to customers")
        
        # Update subscriptions with default payment methods
        print(f"\n🔄 Updating subscriptions with payment methods...")
        
        john_updated = stripe.Subscription.modify(
            john_subscription_id,
            default_payment_method=john_pm.id
        )
        
        jane_updated = stripe.Subscription.modify(
            jane_subscription_id,
            default_payment_method=jane_pm.id
        )
        
        print(f"✅ Subscriptions updated with payment methods")
        
        # Try to pay the latest invoices
        print(f"\n💰 Attempting to pay outstanding invoices...")
        
        # Get and pay John's invoice
        if john_sub.latest_invoice:
            john_invoice = stripe.Invoice.retrieve(john_sub.latest_invoice)
            print(f"   John's invoice: {john_invoice.id} (Status: {john_invoice.status})")
            
            if john_invoice.status == "open":
                try:
                    paid_invoice = stripe.Invoice.pay(
                        john_invoice.id,
                        payment_method=john_pm.id
                    )
                    print(f"✅ John's invoice paid: {paid_invoice.status}")
                except Exception as e:
                    print(f"⚠️ John's invoice payment: {str(e)}")
        
        # Get and pay Jane's invoice
        if jane_sub.latest_invoice:
            jane_invoice = stripe.Invoice.retrieve(jane_sub.latest_invoice)
            print(f"   Jane's invoice: {jane_invoice.id} (Status: {jane_invoice.status})")
            
            if jane_invoice.status == "open":
                try:
                    paid_invoice = stripe.Invoice.pay(
                        jane_invoice.id,
                        payment_method=jane_pm.id
                    )
                    print(f"✅ Jane's invoice paid: {paid_invoice.status}")
                except Exception as e:
                    print(f"⚠️ Jane's invoice payment: {str(e)}")
        
        # Check final subscription statuses
        print(f"\n🔍 Checking final subscription statuses...")
        
        john_final = stripe.Subscription.retrieve(john_subscription_id)
        jane_final = stripe.Subscription.retrieve(jane_subscription_id)
        
        print(f"\n📊 Final Status:")
        print(f"   John Monthly:")
        print(f"     - Subscription ID: {john_final.id}")
        print(f"     - Status: {john_final.status}")
        print(f"     - Customer: {john_customer_id}")
        
        print(f"\n   Jane Yearly:")
        print(f"     - Subscription ID: {jane_final.id}")
        print(f"     - Status: {jane_final.status}")
        print(f"     - Customer: {jane_customer_id}")
        
        # Update our database with final status
        print(f"\n💾 Updating database with final subscription statuses...")
        
        # Update John in database
        john_update = {
            "subscription_status": john_final.status,
            "subscription_id": john_final.id,
            "subscription_plan": "fluency_builder",
            "subscription_period": "monthly",
            "subscription_price_id": "price_1Re01yJcquSiYwWNJRg7nyce",
            "stripe_customer_id": john_customer_id
        }
        
        result1 = await database["users"].update_one(
            {"_id": ObjectId("685c6d8aa3412c0964ef47d0")},
            {"$set": john_update}
        )
        
        # Update Jane in database
        jane_update = {
            "subscription_status": jane_final.status,
            "subscription_id": jane_final.id,
            "subscription_plan": "fluency_builder",
            "subscription_period": "annual",
            "subscription_price_id": "price_1Re06kJcquSiYwWN89Ra57wC",
            "stripe_customer_id": jane_customer_id
        }
        
        result2 = await database["users"].update_one(
            {"_id": ObjectId("685c6dd2a3412c0964ef47d3")},
            {"$set": jane_update}
        )
        
        print(f"✅ Database updated - John: {result1.modified_count} record, Jane: {result2.modified_count} record")
        
        print(f"\n🎉 PAYMENT COMPLETION PROCESS FINISHED!")
        print(f"🔍 Check your Stripe Dashboard to see the final subscription statuses!")
        
    except stripe.error.StripeError as e:
        print(f"❌ Stripe error: {str(e)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(complete_subscription_payments())
