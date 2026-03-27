import stripe
from supabase import Client

from app.config import settings

stripe.api_key = settings.stripe_secret_key

PRICE_MAP = {
    "monthly": settings.stripe_monthly_price_id,
    "annual": settings.stripe_annual_price_id,
}


def create_checkout_session(user_id: str, email: str, plan_type: str) -> str:
    price_id = PRICE_MAP.get(plan_type)
    if not price_id:
        raise ValueError(f"Invalid plan_type: {plan_type}")

    session = stripe.checkout.Session.create(
        customer_email=email,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{settings.frontend_url}/dashboard?checkout=success",
        cancel_url=f"{settings.frontend_url}/dashboard?checkout=cancelled",
        metadata={"user_id": user_id},
    )
    return session.url


def get_subscription(supabase: Client, user_id: str) -> dict | None:
    response = (
        supabase.table("subscriptions")
        .select("id, user_id, stripe_subscription_id, plan_type, status, current_period_start, current_period_end")
        .eq("user_id", user_id)
        .eq("status", "active")
        .order("current_period_end", desc=True)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0]
    return None


def handle_webhook_event(supabase: Client, event: dict) -> None:
    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "customer.subscription.created":
        _upsert_subscription(supabase, obj, "active")

    elif event_type == "customer.subscription.updated":
        status = obj.get("status", "active")
        _upsert_subscription(supabase, obj, status)

    elif event_type == "customer.subscription.deleted":
        _cancel_subscription(supabase, obj["id"])


def _get_user_id_from_subscription(supabase: Client, stripe_sub_id: str) -> str | None:
    response = (
        supabase.table("subscriptions")
        .select("user_id")
        .eq("stripe_subscription_id", stripe_sub_id)
        .single()
        .execute()
    )
    if response.data:
        return response.data["user_id"]
    return None


def _upsert_subscription(supabase: Client, obj: dict, status: str) -> None:
    from datetime import datetime, timezone

    stripe_sub_id = obj["id"]
    metadata = obj.get("metadata", {})
    user_id = metadata.get("user_id")

    if not user_id:
        user_id = _get_user_id_from_subscription(supabase, stripe_sub_id)

    if not user_id:
        return

    items = obj.get("items", {}).get("data", [])
    price_id = items[0]["price"]["id"] if items else ""
    plan_type = "annual" if price_id == settings.stripe_annual_price_id else "monthly"

    period_start = datetime.fromtimestamp(obj["current_period_start"], tz=timezone.utc).isoformat()
    period_end = datetime.fromtimestamp(obj["current_period_end"], tz=timezone.utc).isoformat()

    supabase.table("subscriptions").upsert(
        {
            "user_id": user_id,
            "stripe_subscription_id": stripe_sub_id,
            "plan_type": plan_type,
            "status": status,
            "current_period_start": period_start,
            "current_period_end": period_end,
        },
        on_conflict="stripe_subscription_id",
    ).execute()

    if status == "active":
        supabase.table("users").update({"plan": "pro"}).eq("id", user_id).execute()


def _cancel_subscription(supabase: Client, stripe_sub_id: str) -> None:
    user_id = _get_user_id_from_subscription(supabase, stripe_sub_id)

    supabase.table("subscriptions").update({"status": "cancelled"}).eq(
        "stripe_subscription_id", stripe_sub_id
    ).execute()

    if user_id:
        supabase.table("users").update({"plan": "free"}).eq("id", user_id).execute()
