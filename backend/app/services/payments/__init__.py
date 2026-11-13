"""Payment Gateway and Intent Provider registry."""

from typing import Union

from app.models.enums import PaymentProviderType
from app.services.payments.base import PaymentGatewayProvider
from app.services.payments.direct_upi import DirectUPIProvider
from app.services.payments.razorpay import RazorpayProvider

_direct_upi_instance = DirectUPIProvider()
_razorpay_instance = RazorpayProvider()


def get_payment_provider(
    provider_type: Union[PaymentProviderType, str] = PaymentProviderType.direct_upi,
) -> PaymentGatewayProvider:
    """Return the payment provider instance for the requested rail."""
    if isinstance(provider_type, str):
        try:
            provider_type = PaymentProviderType(provider_type)
        except ValueError:
            pass

    if provider_type == PaymentProviderType.direct_upi:
        return _direct_upi_instance
    elif provider_type == PaymentProviderType.razorpay:
        return _razorpay_instance
    else:
        raise ValueError(f"Unsupported payment provider: {provider_type}")


__all__ = [
    "PaymentGatewayProvider",
    "DirectUPIProvider",
    "RazorpayProvider",
    "get_payment_provider",
]
