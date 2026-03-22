import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import settings
from app.middleware.auth import get_current_user
from app.db.supabase import get_supabase
from app.models import CheckoutRequest
from app.services import billing as billing_service
from app.services import users as users_service

router = APIRouter()


@router.post("/checkout")
async def create_checkout(body: CheckoutRequest, current_user=Depends(get_current_user)):
    supabase = get_supabase()
    profile = users_service.get_user_profile(supabase, current_user.id)
    try:
        url = billing_service.create_checkout_session(
            current_user.id,
            profile["email"],
            body.plan_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except stripe.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Payment service error: {str(e)}",
        )
    return {"url": url}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.errors.SignatureVerificationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")

    supabase = get_supabase()
    try:
        billing_service.handle_webhook_event(supabase, event)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook handling failed: {str(e)}",
        )

    return {"received": True}


@router.get("/subscription")
async def get_subscription(current_user=Depends(get_current_user)):
    supabase = get_supabase()
    subscription = billing_service.get_subscription(supabase, current_user.id)
    if not subscription:
        return {"subscription": None}
    return subscription
