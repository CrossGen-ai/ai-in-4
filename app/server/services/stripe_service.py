"""Stripe service layer for payment integration using Stripe MCP."""
from typing import List, Optional, Dict, Any
from core.config import settings
import hashlib
import hmac


class StripeService:
    """Service for interacting with Stripe via MCP."""

    def __init__(self):
        """Initialize Stripe service with configuration."""
        self.secret_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        self.test_mode = settings.STRIPE_TEST_MODE

        # Validate test mode
        if self.test_mode and self.secret_key and not self.secret_key.startswith("sk_test_"):
            raise ValueError("STRIPE_TEST_MODE is True but secret key is not a test key")

    async def create_checkout_session(
        self,
        price_id: str,
        user_email: str,
        referrer_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a Stripe checkout session.

        Args:
            price_id: Stripe price ID
            user_email: Customer email
            referrer_code: Optional referrer code for tracking

        Returns:
            Dict with checkout session details including URL
        """
        # Get or create Stripe customer
        customer_id = await self.get_or_create_customer(user_email)

        # Build metadata
        metadata = {"user_email": user_email}
        if referrer_code:
            metadata["referrer_code"] = referrer_code

        # In actual implementation, this would call Stripe MCP
        # For now, this is a placeholder that will be connected via MCP tools
        # The actual MCP call would be made from the route layer

        return {
            "customer_id": customer_id,
            "price_id": price_id,
            "metadata": metadata,
            "success_url": f"{settings.FRONTEND_URL}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{settings.FRONTEND_URL}/checkout/cancel",
        }

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify Stripe webhook signature.

        Args:
            payload: Raw request body
            signature: Stripe signature header

        Returns:
            True if signature is valid
        """
        try:
            # Extract timestamp and signatures from header
            parts = signature.split(",")
            timestamp = None
            signatures = []

            for part in parts:
                if part.startswith("t="):
                    timestamp = part[2:]
                elif part.startswith("v1="):
                    signatures.append(part[3:])

            if not timestamp or not signatures:
                return False

            # Compute expected signature
            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            expected_sig = hmac.new(
                self.webhook_secret.encode("utf-8"),
                signed_payload.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            # Compare signatures (constant time comparison)
            return any(
                hmac.compare_digest(expected_sig, sig) for sig in signatures
            )
        except Exception:
            return False

    async def get_or_create_customer(self, email: str) -> str:
        """
        Get existing Stripe customer or create new one.

        Args:
            email: Customer email

        Returns:
            Stripe customer ID
        """
        # This would use Stripe MCP to search for customer and create if needed
        # Placeholder implementation
        return f"cus_{email.replace('@', '_').replace('.', '_')}"

    async def sync_products(self) -> List[Dict[str, Any]]:
        """
        Fetch all products from Stripe.

        Returns:
            List of product dictionaries
        """
        # This would call Stripe MCP list_products
        # Placeholder for now
        return []

    async def sync_prices(self) -> List[Dict[str, Any]]:
        """
        Fetch all prices from Stripe.

        Returns:
            List of price dictionaries
        """
        # This would call Stripe MCP list_prices
        # Placeholder for now
        return []

    async def get_customer_payment_intents(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get payment history for a customer.

        Args:
            customer_id: Stripe customer ID

        Returns:
            List of payment intent dictionaries
        """
        # This would call Stripe MCP list_payment_intents
        # Placeholder for now
        return []

    async def create_refund(
        self, payment_intent_id: str, amount: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a refund for a payment intent.

        Args:
            payment_intent_id: Stripe payment intent ID
            amount: Optional partial refund amount in cents

        Returns:
            Refund dictionary
        """
        # This would call Stripe MCP create_refund
        # Placeholder for now
        return {"id": "re_placeholder", "amount": amount, "status": "succeeded"}


# Global instance
stripe_service = StripeService()
