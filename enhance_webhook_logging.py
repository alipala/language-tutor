"""
Enhancement to add better webhook logging and error handling to prevent future sync issues.
This will help us debug webhook delivery problems and ensure subscription status stays in sync.
"""

webhook_enhancement = '''
# Add this to the beginning of the webhook handler in stripe_routes.py

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None)
):
    try:
        # Get the webhook data
        payload = await request.body()
        
        # Log webhook receipt
        logger.info(f"[WEBHOOK] Received webhook with signature: {stripe_signature[:20] if stripe_signature else 'None'}...")
        
        # Verify the webhook signature
        if not stripe_signature or not stripe_webhook_secret:
            logger.error("[WEBHOOK] Missing Stripe signature or webhook secret")
            return JSONResponse(status_code=400, content={"error": "Missing Stripe signature or webhook secret"})

        try:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, stripe_webhook_secret
            )
            logger.info(f"[WEBHOOK] Successfully verified event: {event['type']} (ID: {event['id']})")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"[WEBHOOK] Invalid Stripe signature: {str(e)}")
            return JSONResponse(status_code=400, content={"error": "Invalid signature"})

        # Log event details
        event_type = event["type"]
        event_id = event["id"]
        logger.info(f"[WEBHOOK] Processing event {event_type} (ID: {event_id})")
        
        # Handle the event with enhanced logging
        try:
            if event_type == "customer.subscription.created":
                logger.info(f"[WEBHOOK] Handling subscription.created for event {event_id}")
                await handle_subscription_created(event["data"]["object"])
            elif event_type == "customer.subscription.updated":
                logger.info(f"[WEBHOOK] Handling subscription.updated for event {event_id}")
                await handle_subscription_updated(event["data"]["object"])
            elif event_type == "customer.subscription.deleted":
                logger.info(f"[WEBHOOK] Handling subscription.deleted for event {event_id}")
                await handle_subscription_deleted(event["data"]["object"])
            elif event_type == "checkout.session.completed":
                logger.info(f"[WEBHOOK] Handling checkout.session.completed for event {event_id}")
                await handle_checkout_completed(event["data"]["object"])
            elif event_type == "invoice.payment_succeeded":
                logger.info(f"[WEBHOOK] Handling invoice.payment_succeeded for event {event_id}")
                await handle_invoice_payment_succeeded(event["data"]["object"])
            elif event_type == "invoice_payment.paid":
                logger.info(f"[WEBHOOK] Handling invoice_payment.paid for event {event_id}")
                await handle_invoice_payment_paid(event["data"]["object"])
            elif event_type == "payment_intent.succeeded":
                logger.info(f"[WEBHOOK] Handling payment_intent.succeeded for event {event_id}")
                await handle_payment_intent_succeeded(event["data"]["object"])
            else:
                logger.info(f"[WEBHOOK] Unhandled event type: {event_type} (ID: {event_id})")
            
            logger.info(f"[WEBHOOK] Successfully processed event {event_type} (ID: {event_id})")
            
        except Exception as handler_error:
            logger.error(f"[WEBHOOK] Error handling event {event_type} (ID: {event_id}): {str(handler_error)}")
            # Still return success to Stripe to avoid retries for application errors
            # But log the error for investigation
            import traceback
            logger.error(f"[WEBHOOK] Full traceback: {traceback.format_exc()}")

        return {"status": "success", "event_id": event_id, "event_type": event_type}
        
    except Exception as e:
        logger.error(f"[WEBHOOK] Critical error processing webhook: {str(e)}")
        import traceback
        logger.error(f"[WEBHOOK] Full traceback: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"error": str(e)})
'''

# Enhanced subscription handlers with better logging
enhanced_handlers = '''
async def handle_subscription_updated(subscription):
    """Handle subscription updated event with enhanced logging"""
    try:
        customer_id = subscription.get("customer")
        subscription_id = subscription.get("id")
        status = subscription.get("status")
        
        logger.info(f"[WEBHOOK-SUB-UPDATED] Processing subscription {subscription_id} for customer {customer_id}, status: {status}")
        
        if not customer_id:
            logger.warning("[WEBHOOK-SUB-UPDATED] No customer ID in subscription updated event")
            return

        # Find user by multiple methods
        user = await find_user_by_customer_id(customer_id)
        if not user:
            logger.warning(f"[WEBHOOK-SUB-UPDATED] No user found for customer {customer_id}")
            return

        current_status = user.get("subscription_status")
        logger.info(f"[WEBHOOK-SUB-UPDATED] User {user['_id']} current status: {current_status}, new status: {status}")

        # Prepare update data
        update_data = {
            "subscription_status": status
        }
        
        # Add period dates from Stripe
        from datetime import datetime, timezone
        if subscription.get("current_period_start"):
            update_data["current_period_start"] = datetime.fromtimestamp(subscription.get("current_period_start"), tz=timezone.utc)
            update_data["subscription_started_at"] = datetime.fromtimestamp(subscription.get("current_period_start"), tz=timezone.utc)
        
        if subscription.get("current_period_end"):
            update_data["current_period_end"] = datetime.fromtimestamp(subscription.get("current_period_end"), tz=timezone.utc)
            update_data["subscription_expires_at"] = datetime.fromtimestamp(subscription.get("current_period_end"), tz=timezone.utc)
        
        # Get the plan details
        if subscription.get("items") and subscription.get("items").get("data"):
            price = subscription.get("items").get("data")[0].get("price")
            if price:
                update_data["subscription_price_id"] = price.get("id")
                
                # Get product details
                try:
                    product = stripe.Product.retrieve(price.get("product"))
                    update_data["subscription_plan"] = map_stripe_product_to_plan_id(product.name)
                    
                    # Determine if monthly or annual
                    if price.get("recurring") and price.get("recurring").get("interval"):
                        update_data["subscription_period"] = "monthly" if price.get("recurring").get("interval") == "month" else "annual"
                    
                    logger.info(f"[WEBHOOK-SUB-UPDATED] Plan details: {update_data.get('subscription_plan')} ({update_data.get('subscription_period')})")
                except Exception as e:
                    logger.error(f"[WEBHOOK-SUB-UPDATED] Error getting product details: {str(e)}")

        # Update user in MongoDB
        logger.info(f"[WEBHOOK-SUB-UPDATED] Updating user {user['_id']} with data: {update_data}")
        result = await database["users"].update_one(
            {"_id": user["_id"]},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"[WEBHOOK-SUB-UPDATED] Successfully updated user {user['_id']} subscription status from '{current_status}' to '{status}'")
        else:
            logger.warning(f"[WEBHOOK-SUB-UPDATED] No changes made to user {user['_id']} - data may be identical")
        
    except Exception as e:
        logger.error(f"[WEBHOOK-SUB-UPDATED] Error handling subscription updated: {str(e)}")
        import traceback
        logger.error(f"[WEBHOOK-SUB-UPDATED] Full traceback: {traceback.format_exc()}")
        raise  # Re-raise to be caught by main webhook handler
'''

print("=== WEBHOOK ENHANCEMENT RECOMMENDATIONS ===")
print()
print("1. 🔧 ENHANCED LOGGING:")
print("   - Add detailed logging for all webhook events")
print("   - Log event IDs for tracking")
print("   - Log before/after status changes")
print("   - Log user lookup results")
print()
print("2. 🔧 ERROR HANDLING:")
print("   - Catch and log all errors without failing webhook")
print("   - Return success to Stripe even on application errors")
print("   - Add full stack traces for debugging")
print()
print("3. 🔧 MONITORING:")
print("   - Add webhook event logging to database")
print("   - Create webhook health check endpoint")
print("   - Add alerts for failed webhook processing")
print()
print("4. 🔧 SYNC VERIFICATION:")
print("   - Add periodic sync job to check Stripe vs DB status")
print("   - Add manual sync endpoint for admin use")
print("   - Add webhook replay functionality")
print()
print("5. ✅ IMMEDIATE FIX APPLIED:")
print("   - User subscription status updated to 'active'")
print("   - Assessment counter now shows 23/24")
print("   - Root cause identified: webhook sync failure")
