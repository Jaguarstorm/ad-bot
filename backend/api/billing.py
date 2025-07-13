# backend/api/billing.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional
import stripe
import logging
from datetime import datetime

from backend.utils.database import get_supabase_client, update_user_plan, get_user_by_id
from backend.api.auth import get_current_user
from backend.config import STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize Stripe
stripe.api_key = STRIPE_SECRET_KEY

# Pydantic models
class CreateSubscriptionRequest(BaseModel):
    plan: str  # "basic" or "pro"
    payment_method_id: Optional[str] = None

class SubscriptionResponse(BaseModel):
    subscription_id: str
    plan: str
    status: str
    current_period_end: str
    cancel_at_period_end: bool

class BillingPortalRequest(BaseModel):
    return_url: str

# Subscription plans
SUBSCRIPTION_PLANS = {
    "basic": {
        "stripe_price_id": "price_basic_monthly",  # Replace with actual Stripe price ID
        "amount": 1500,  # $15.00 in cents
        "currency": "usd",
        "interval": "month"
    },
    "pro": {
        "stripe_price_id": "price_pro_monthly",  # Replace with actual Stripe price ID
        "amount": 4000,  # $40.00 in cents
        "currency": "usd",
        "interval": "month"
    }
}

@router.post("/create-subscription", response_model=SubscriptionResponse)
async def create_subscription(request: CreateSubscriptionRequest, user_id: str = Depends(get_current_user)):
    """Create a new subscription"""
    try:
        supabase = get_supabase_client()
        
        # Get user profile
        user_profile = await get_user_by_id(user_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Check if user already has a subscription
        existing_sub = supabase.table("subscriptions").select("*").eq("user_id", user_id).eq("status", "active").execute()
        if existing_sub.data:
            raise HTTPException(status_code=400, detail="User already has an active subscription")
        
        # Get plan details
        plan_details = SUBSCRIPTION_PLANS.get(request.plan)
        if not plan_details:
            raise HTTPException(status_code=400, detail="Invalid plan")
        
        # Create Stripe customer if doesn't exist
        customer_id = user_profile.get("stripe_customer_id")
        if not customer_id:
            customer = stripe.Customer.create(
                email=user_profile["email"],
                metadata={"user_id": user_id}
            )
            customer_id = customer.id
            
            # Update user profile with customer ID
            supabase.table("user_profiles").update({
                "stripe_customer_id": customer_id
            }).eq("id", user_id).execute()
        
        # Create subscription
        subscription_data = {
            "customer": customer_id,
            "items": [{"price": plan_details["stripe_price_id"]}],
            "payment_behavior": "default_incomplete",
            "expand": ["latest_invoice.payment_intent"],
            "metadata": {"user_id": user_id, "plan": request.plan}
        }
        
        if request.payment_method_id:
            subscription_data["default_payment_method"] = request.payment_method_id
        
        subscription = stripe.Subscription.create(**subscription_data)
        
        # Store subscription in database
        supabase.table("subscriptions").insert({
            "user_id": user_id,
            "stripe_subscription_id": subscription.id,
            "plan": request.plan,
            "status": subscription.status,
            "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
            "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "created_at": "now()"
        }).execute()
        
        # Update user plan
        await update_user_plan(user_id, request.plan)
        
        return SubscriptionResponse(
            subscription_id=subscription.id,
            plan=request.plan,
            status=subscription.status,
            current_period_end=datetime.fromtimestamp(subscription.current_period_end).isoformat(),
            cancel_at_period_end=subscription.cancel_at_period_end
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Subscription creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subscription")

@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(user_id: str = Depends(get_current_user)):
    """Get current user subscription"""
    try:
        supabase = get_supabase_client()
        
        result = supabase.table("subscriptions").select("*").eq("user_id", user_id).eq("status", "active").execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        subscription = result.data[0]
        
        return SubscriptionResponse(
            subscription_id=subscription["stripe_subscription_id"],
            plan=subscription["plan"],
            status=subscription["status"],
            current_period_end=subscription["current_period_end"],
            cancel_at_period_end=subscription["cancel_at_period_end"]
        )
        
    except Exception as e:
        logger.error(f"Get subscription error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get subscription")

@router.post("/cancel-subscription")
async def cancel_subscription(user_id: str = Depends(get_current_user)):
    """Cancel subscription at period end"""
    try:
        supabase = get_supabase_client()
        
        # Get subscription
        result = supabase.table("subscriptions").select("*").eq("user_id", user_id).eq("status", "active").execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        subscription = result.data[0]
        
        # Cancel in Stripe
        stripe_subscription = stripe.Subscription.modify(
            subscription["stripe_subscription_id"],
            cancel_at_period_end=True
        )
        
        # Update in database
        supabase.table("subscriptions").update({
            "cancel_at_period_end": True,
            "updated_at": "now()"
        }).eq("id", subscription["id"]).execute()
        
        return {"message": "Subscription will be canceled at the end of the current period"}
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Cancel subscription error: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")

@router.post("/reactivate-subscription")
async def reactivate_subscription(user_id: str = Depends(get_current_user)):
    """Reactivate subscription"""
    try:
        supabase = get_supabase_client()
        
        # Get subscription
        result = supabase.table("subscriptions").select("*").eq("user_id", user_id).eq("status", "active").execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        subscription = result.data[0]
        
        # Reactivate in Stripe
        stripe_subscription = stripe.Subscription.modify(
            subscription["stripe_subscription_id"],
            cancel_at_period_end=False
        )
        
        # Update in database
        supabase.table("subscriptions").update({
            "cancel_at_period_end": False,
            "updated_at": "now()"
        }).eq("id", subscription["id"]).execute()
        
        return {"message": "Subscription reactivated"}
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Reactivate subscription error: {e}")
        raise HTTPException(status_code=500, detail="Failed to reactivate subscription")

@router.post("/create-portal-session")
async def create_portal_session(request: BillingPortalRequest, user_id: str = Depends(get_current_user)):
    """Create Stripe billing portal session"""
    try:
        supabase = get_supabase_client()
        
        # Get user profile
        user_profile = await get_user_by_id(user_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        customer_id = user_profile.get("stripe_customer_id")
        if not customer_id:
            raise HTTPException(status_code=400, detail="No billing account found")
        
        # Create portal session
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=request.return_url
        )
        
        return {"url": session.url}
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Portal session error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header:
            raise HTTPException(status_code=400, detail="No signature header")
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Handle webhook events
        if event["type"] == "invoice.payment_succeeded":
            await handle_payment_succeeded(event["data"]["object"])
        elif event["type"] == "invoice.payment_failed":
            await handle_payment_failed(event["data"]["object"])
        elif event["type"] == "customer.subscription.deleted":
            await handle_subscription_deleted(event["data"]["object"])
        elif event["type"] == "customer.subscription.updated":
            await handle_subscription_updated(event["data"]["object"])
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

async def handle_payment_succeeded(invoice):
    """Handle successful payment"""
    try:
        supabase = get_supabase_client()
        
        # Update subscription status
        supabase.table("subscriptions").update({
            "status": "active",
            "updated_at": "now()"
        }).eq("stripe_subscription_id", invoice["subscription"]).execute()
        
        logger.info(f"Payment succeeded for subscription: {invoice['subscription']}")
        
    except Exception as e:
        logger.error(f"Payment succeeded handler error: {e}")

async def handle_payment_failed(invoice):
    """Handle failed payment"""
    try:
        supabase = get_supabase_client()
        
        # Update subscription status
        supabase.table("subscriptions").update({
            "status": "past_due",
            "updated_at": "now()"
        }).eq("stripe_subscription_id", invoice["subscription"]).execute()
        
        logger.info(f"Payment failed for subscription: {invoice['subscription']}")
        
    except Exception as e:
        logger.error(f"Payment failed handler error: {e}")

async def handle_subscription_deleted(subscription):
    """Handle subscription deletion"""
    try:
        supabase = get_supabase_client()
        
        # Update subscription status
        supabase.table("subscriptions").update({
            "status": "canceled",
            "updated_at": "now()"
        }).eq("stripe_subscription_id", subscription["id"]).execute()
        
        # Downgrade user to trial
        user_id = subscription["metadata"].get("user_id")
        if user_id:
            await update_user_plan(user_id, "trial")
        
        logger.info(f"Subscription deleted: {subscription['id']}")
        
    except Exception as e:
        logger.error(f"Subscription deleted handler error: {e}")

async def handle_subscription_updated(subscription):
    """Handle subscription updates"""
    try:
        supabase = get_supabase_client()
        
        # Update subscription in database
        supabase.table("subscriptions").update({
            "status": subscription["status"],
            "current_period_start": datetime.fromtimestamp(subscription["current_period_start"]),
            "current_period_end": datetime.fromtimestamp(subscription["current_period_end"]),
            "cancel_at_period_end": subscription["cancel_at_period_end"],
            "updated_at": "now()"
        }).eq("stripe_subscription_id", subscription["id"]).execute()
        
        logger.info(f"Subscription updated: {subscription['id']}")
        
    except Exception as e:
        logger.error(f"Subscription updated handler error: {e}")

@router.get("/plans")
async def get_plans():
    """Get available subscription plans"""
    return {
        "plans": [
            {
                "id": "basic",
                "name": "Basic Plan",
                "price": 15.00,
                "currency": "usd",
                "interval": "month",
                "features": [
                    "Smart Video Editor",
                    "AI Captions & Hashtags",
                    "Manual Post Scheduling",
                    "2GB Storage",
                    "30 AI Captions/day"
                ]
            },
            {
                "id": "pro",
                "name": "Pro Plan",
                "price": 40.00,
                "currency": "usd",
                "interval": "month",
                "features": [
                    "Everything in Basic",
                    "AI Video Generator",
                    "Auto-Posting to All Platforms",
                    "10GB Storage",
                    "Unlimited AI Captions",
                    "Priority Support"
                ]
            }
        ]
    } 