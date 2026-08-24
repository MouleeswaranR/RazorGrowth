from app.schemas.agent_outputs import CampaignCopyOutput, LLMCopyGenerationInput
from app.services.llm_service import llm_service


class CampaignAgent:
    """Generates personalized multi-channel messaging copy structured as CampaignCopyOutput."""

    async def compose_personalized_copy(
        self,
        customer_name: str,
        offer_description: str,
        favorite_category: str,
        urgency: str = "Expires in 7 days",
    ) -> CampaignCopyOutput:
        """Invokes LLMService with structured input to generate individualized copy."""
        llm_input = LLMCopyGenerationInput(
            customer_name=customer_name,
            favorite_category=favorite_category,
            offer_description=offer_description,
            urgency_text=urgency,
        )
        llm_output = await llm_service.generate_personalized_copy(llm_input)
        return CampaignCopyOutput(
            channel="email",
            subject=llm_output.subject,
            email_body=llm_output.email_body,
            whatsapp_body=llm_output.whatsapp_body,
            template_type="personalized_ai",
        )

    def compose_personalized_email(
        self,
        customer_name: str,
        offer_description: str,
        favorite_category: str,
        urgency: str = "Expires in 7 days",
    ) -> CampaignCopyOutput:
        """Synchronous template builder producing validated CampaignCopyOutput."""
        subject = f"Special {favorite_category} gift for {customer_name}"
        email_body = (
            f"Hi {customer_name},\n\n"
            f"We have an exclusive offer on our {favorite_category} collection: {offer_description}.\n\n"
            f"⏰ {urgency}.\n\n"
            f"Use your code at checkout!"
        )
        whatsapp_body = f"Hey {customer_name}! Special offer on {favorite_category}: {offer_description}."
        return CampaignCopyOutput(
            channel="email",
            subject=subject,
            email_body=email_body,
            whatsapp_body=whatsapp_body,
            template_type="personalized_template",
        )

    def compose_payment_recovery_copy(
        self,
        customer_name: str,
        offer_description: str,
        urgency: str = "Complete checkout within 24 hours",
    ) -> CampaignCopyOutput:
        """Constructs 1-click UPI checkout retry communication for dropped payment attempts."""
        subject = f"Quick Action Needed: Complete your order in 1-Click with UPI, {customer_name}"
        email_body = (
            f"Hi {customer_name},\n\n"
            f"We noticed your recent Card transaction could not be processed. "
            f"No worries — your cart items are reserved for you!\n\n"
            f"⚡ {offer_description}.\n\n"
            f"Click below to complete your order seamlessly with instant Razorpay UPI verification:\n"
            f"https://stylekart.shop/checkout/retry\n\n"
            f"⏰ {urgency}."
        )
        whatsapp_body = (
            f"Hi {customer_name}, your cart is waiting! Complete your order with 1-Click UPI & get {offer_description}: "
            f"https://stylekart.shop/checkout/retry"
        )
        return CampaignCopyOutput(
            channel="email",
            subject=subject,
            email_body=email_body,
            whatsapp_body=whatsapp_body,
            template_type="payment_retry_nudge",
        )

    def compose_reengagement_email(
        self,
        customer_name: str,
        offer_description: str,
        urgency: str,
        favorite_category: str,
    ) -> CampaignCopyOutput:
        """Constructs structured re-engagement email copy for dormant VIP customers."""
        copy = self.compose_personalized_email(
            customer_name=customer_name,
            offer_description=offer_description,
            favorite_category=favorite_category,
            urgency=urgency,
        )
        copy.template_type = "reengagement"
        return copy
