"""Allowed values and the product catalog.

Values that are states (statuses, sources, reasons) are also enforced by CHECK constraints in the
database. The catalog (products, periods, payment methods, video platforms) changes over time, so
only this code validates it and adding an entry needs no migration.
"""

# The access modules a user can have. Each one has its own columns in user_subscriptions.
MODULE_IDS = ("spoofer", "dlc-unlock")

# What can be bought, and which modules each product unlocks. A bundle is named after what it contains and just lists several.
PRODUCTS: dict[str, tuple[str, ...]] = {
    "spoofer": ("spoofer",),
    "dlc-unlock": ("dlc-unlock",),
    "spoofer-dlc-unlock": ("spoofer", "dlc-unlock"),
}
PERIOD_IDS = ("1m", "3m", "6m", "lifetime")
PAYMENT_METHOD_IDS = ("paypal", "crypto", "steam")
PROMO_PLATFORM_IDS = ("tiktok", "youtube", "other")

ORDER_STATUSES = ("pending", "review", "approved", "rejected")
PROMO_CLAIM_STATUSES = ("review", "approved", "rejected")
GRANT_SOURCES = ("order", "promo", "admin")
BALANCE_REASONS = ("order_overpay", "spent", "admin")

SCREENSHOT_CONTENT_TYPES = ("image/png", "image/jpeg", "image/webp")
MAX_SCREENSHOT_BYTES = 25 * 1024 * 1024
MAX_SCREENSHOTS_PER_ORDER = 3
