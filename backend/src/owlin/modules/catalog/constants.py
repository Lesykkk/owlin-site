"""Allowed values shared by the database constraints and the services."""

# What can be bought. A bundle grants both of the single products.
PRODUCT_IDS = ("spoofer", "dlc-unlock", "bundle")
# What a subscription grant can be for.
GRANT_PRODUCT_IDS = ("spoofer", "dlc-unlock")
PERIOD_IDS = ("1m", "3m", "6m", "lifetime")
PAYMENT_METHOD_IDS = ("paypal", "crypto", "steam")

ORDER_STATUSES = ("pending", "review", "approved", "rejected")
PROMO_CLAIM_STATUSES = ("review", "approved", "rejected")
PROMO_PLATFORM_IDS = ("tiktok", "youtube", "other")

GRANT_SOURCES = ("order", "promo", "admin")
BALANCE_REASONS = ("order_overpay", "spent", "admin")

SCREENSHOT_CONTENT_TYPES = ("image/png", "image/jpeg", "image/webp")
MAX_SCREENSHOT_BYTES = 25 * 1024 * 1024
MAX_SCREENSHOTS_PER_ORDER = 3
