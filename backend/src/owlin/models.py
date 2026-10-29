"""Imports every model so that Base.metadata is complete. Alembic reads it from here."""

from owlin.modules.access_promotions.models import AccessPromotion
from owlin.modules.devices.models import UserDevice
from owlin.modules.subscriptions.models import UserSubscription

__all__ = ["AccessPromotion", "UserDevice", "UserSubscription"]
