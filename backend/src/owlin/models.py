"""Imports every model so that Base.metadata is complete. Alembic reads it from here."""

from owlin.modules.access_promotions.models import AccessPromotion
from owlin.modules.balance.models import BalanceTransaction
from owlin.modules.devices.models import UserDevice
from owlin.modules.orders.models import Order, OrderScreenshot
from owlin.modules.promo.models import PromoClaim
from owlin.modules.subscriptions.models import SubscriptionGrant, UserSubscription

__all__ = [
    "AccessPromotion",
    "BalanceTransaction",
    "Order",
    "OrderScreenshot",
    "PromoClaim",
    "SubscriptionGrant",
    "UserDevice",
    "UserSubscription",
]
