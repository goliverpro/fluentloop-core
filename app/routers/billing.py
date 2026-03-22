from fastapi import APIRouter, Depends, Request
from app.middleware.auth import get_current_user

router = APIRouter()


@router.post("/checkout")
async def create_checkout(current_user=Depends(get_current_user)):
    # TODO: create Stripe checkout session
    raise NotImplementedError


@router.post("/webhook")
async def stripe_webhook(request: Request):
    # TODO: validate stripe-signature, handle events
    # No auth middleware — authenticated via Stripe signature
    raise NotImplementedError


@router.get("/subscription")
async def get_subscription(current_user=Depends(get_current_user)):
    # TODO: get current subscription details
    raise NotImplementedError
