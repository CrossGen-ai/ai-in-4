"""Payment routes for Stripe integration."""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import json
import logging
import stripe
from stripe import StripeError

from core.config import settings
from db.database import get_db
from db.models import User, StripeProduct, StripePrice
from models.schemas import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    EntitlementResponse,
    ReferralResponse,
)
from api.routes.users import get_current_user
from services import entitlement_service, referral_service

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create Stripe checkout session with employment-based pricing.

    Args:
        request: Checkout request with product_id and optional referrer_code
        current_user: Authenticated user
        db: Database session

    Returns:
        CheckoutSessionResponse with checkout URL and session ID

    Note:
        This endpoint automatically selects the appropriate price based on the user's
        employment status stored in their UserExperience profile.
    """
    from db.models import UserExperience

    # Validate product exists
    product_result = await db.execute(
        select(StripeProduct).where(StripeProduct.id == request.product_id)
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Get user's employment status
    experience_result = await db.execute(
        select(UserExperience).where(UserExperience.user_id == current_user.id)
    )
    experience = experience_result.scalar_one_or_none()
    if not experience or not experience.employment_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User employment status not found. Please complete your profile."
        )

    employment_status = experience.employment_status

    # Get all active prices for this product
    prices_result = await db.execute(
        select(StripePrice)
        .where(StripePrice.product_id == request.product_id)
        .where(StripePrice.active)
    )
    prices = prices_result.scalars().all()

    if not prices:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active prices found for this product"
        )

    # Select price based on employment eligibility
    selected_price = None
    for price in prices:
        if price.stripe_metadata and "eligible_employment_statuses" in price.stripe_metadata:
            eligible_statuses = price.stripe_metadata["eligible_employment_statuses"]
            if employment_status in eligible_statuses:
                selected_price = price
                break

    if not selected_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No price available for employment status: {employment_status}"
        )

    # Validate referrer code if provided
    referrer_user = None
    if request.referrer_code:
        referrer_user = await referral_service.validate_referral_code(
            request.referrer_code, db
        )
        if not referrer_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid referrer code"
            )

        # Prevent self-referral
        if referrer_user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot use your own referral code"
            )

    # Build metadata for checkout session
    metadata = {
        "user_id": str(current_user.id),
        "user_email": current_user.email,
        "price_id": selected_price.id,
    }
    if referrer_user:
        metadata["referrer_id"] = str(referrer_user.id)
        metadata["referrer_code"] = request.referrer_code

    # Create Stripe Checkout Session
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": selected_price.id,
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{settings.FRONTEND_URL}/purchase/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/purchase/cancelled",
            payment_intent_data={
                "metadata": metadata,
            },
            metadata=metadata,
        )

        logger.info(
            f"Created Stripe checkout session {checkout_session.id} for user {current_user.id}, "
            f"product {product.name}, price {selected_price.id} "
            f"(${selected_price.amount/100:.2f}), employment: {employment_status}"
        )

        return CheckoutSessionResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id,
        )
    except StripeError as e:
        logger.error(f"Stripe error creating checkout session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str = Header(None, alias="stripe-signature"),
):
    """
    Handle Stripe webhook events.

    Args:
        request: Raw request for signature verification
        db: Database session
        stripe_signature: Stripe signature header

    Returns:
        Success response

    Note:
        Handles payment_intent.succeeded events to grant entitlements
    """
    # Get raw body for signature verification
    body = await request.body()

    # TODO: Verify webhook signature
    # if not stripe_service.verify_webhook_signature(body, stripe_signature):
    #     raise HTTPException(status_code=400, detail="Invalid signature")

    # Parse event
    try:
        event_data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = event_data.get("type")
    logger.info(f"Received webhook event: {event_type}")

    # Handle payment_intent.succeeded
    if event_type == "payment_intent.succeeded":
        payment_intent = event_data.get("data", {}).get("object", {})
        payment_intent_id = payment_intent.get("id")
        metadata = payment_intent.get("metadata", {})

        user_id = metadata.get("user_id")
        price_id = metadata.get("price_id")
        referrer_id = metadata.get("referrer_id")

        if not user_id or not price_id:
            logger.error(f"Missing metadata in payment intent {payment_intent_id}")
            return {"status": "error", "message": "Missing metadata"}

        # Grant entitlement
        try:
            await entitlement_service.grant_entitlement(
                user_id=int(user_id),
                price_id=price_id,
                payment_intent_id=payment_intent_id,
                db=db,
            )
            logger.info(f"Granted entitlement for user {user_id}, price {price_id}")
        except Exception as e:
            logger.error(f"Error granting entitlement: {str(e)}")
            return {"status": "error", "message": str(e)}

        # Process referral if present
        if referrer_id:
            try:
                user_email = metadata.get("user_email")
                amount = payment_intent.get("amount", 0)
                credit_amount = int(amount * 0.25)  # 25% credit

                # Create referral record
                referral = await referral_service.create_referral(
                    referrer_id=int(referrer_id),
                    referee_email=user_email,
                    payment_intent_id=payment_intent_id,
                    course_id=None,
                    db=db,
                )

                # Apply credit
                await referral_service.apply_referral_credit(
                    referrer_id=int(referrer_id),
                    amount=credit_amount,
                    referral_id=referral.id,
                    db=db,
                )

                logger.info(f"Applied referral credit {credit_amount} to user {referrer_id}")
            except Exception as e:
                logger.error(f"Error processing referral: {str(e)}")

    return {"status": "success"}


@router.get("/entitlements", response_model=List[EntitlementResponse])
async def get_user_entitlements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's entitlements.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        List of user entitlements with product details
    """
    entitlements = await entitlement_service.get_user_entitlements(
        current_user.id, db
    )

    # Enrich with product/price details
    result = []
    for ent in entitlements:
        # Get price and product
        price_result = await db.execute(
            select(StripePrice).where(StripePrice.id == ent.stripe_price_id)
        )
        price = price_result.scalar_one_or_none()

        if price:
            product_result = await db.execute(
                select(StripeProduct).where(StripeProduct.id == price.product_id)
            )
            product = product_result.scalar_one_or_none()

            if product:
                result.append(
                    EntitlementResponse(
                        price_id=ent.stripe_price_id,
                        product_id=product.id,
                        product_name=product.name,
                        status=ent.status,
                        created_at=ent.created_at,
                    )
                )

    return result


@router.get("/referrals", response_model=ReferralResponse)
async def get_referral_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's referral statistics.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        Referral statistics including code, counts, and credits
    """
    stats = await referral_service.get_referral_stats(current_user.id, db)
    return ReferralResponse(**stats)


@router.post("/sync-products")
async def sync_stripe_products(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin endpoint to sync products from Stripe.

    Args:
        current_user: Authenticated user (should be admin)
        db: Database session

    Returns:
        Count of synced products

    Note:
        This endpoint should be protected with admin-only access in production.
        For now, any authenticated user can trigger sync for testing.
    """
    # TODO: Implement actual Stripe MCP sync
    # products = await stripe_service.sync_products()
    # prices = await stripe_service.sync_prices()

    # For now, return placeholder
    return {"count": 0, "message": "Sync functionality to be implemented"}
