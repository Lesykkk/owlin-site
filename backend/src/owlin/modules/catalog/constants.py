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
# Price in euro cents for each product and period. The server always recomputes the amount from this.
PRICES_CENTS: dict[str, dict[str, int]] = {
    "dlc-unlock": {"1m": 199, "3m": 499, "6m": 799, "lifetime": 1499},
    "spoofer": {"1m": 400, "3m": 900, "6m": 1400, "lifetime": 1999},
    "spoofer-dlc-unlock": {"1m": 500, "3m": 1300, "6m": 2099, "lifetime": 3099},
}
# Coins and networks offered when paying with crypto.
CRYPTO_COIN_IDS = ("sol", "usdc-solana", "usdc-base", "usdt-trc20", "btc")
# Orders a user may have waiting for review at the same time.
MAX_OPEN_ORDERS = 4

# How long each period lasts. A month counts as 30 days; None means no end date.
PERIOD_DAYS: dict[str, int | None] = {"1m": 30, "3m": 90, "6m": 180, "lifetime": None}
PERIOD_IDS = tuple(PERIOD_DAYS)
# Free days given for an approved promo video.
PROMO_DAYS = 7
PAYMENT_METHOD_IDS = ("paypal", "crypto", "steam")
# Views a video needs per platform. None means there is no fixed number and an admin decides.
PROMO_MIN_VIEWS: dict[str, int | None] = {"tiktok": 5000, "youtube": 1000, "other": None}
PROMO_PLATFORM_IDS = tuple(PROMO_MIN_VIEWS)
# A video must not be older than this when it is submitted.
MAX_VIDEO_AGE_DAYS = 7
# Promo claims a user may have under review or still running at the same time.
MAX_PROMO_SLOTS = 8

ORDER_STATUSES = ("review", "approved", "rejected")
PROMO_CLAIM_STATUSES = ("review", "approved", "rejected")
GRANT_SOURCES = ("order", "promo", "admin")
BALANCE_REASONS = ("order_overpay", "spent", "admin")

SCREENSHOT_CONTENT_TYPES = ("image/png", "image/jpeg", "image/webp")
MAX_SCREENSHOT_BYTES = 5 * 1024 * 1024
MAX_SCREENSHOTS_PER_ORDER = 3
# The largest order request: every screenshot at its limit plus room for the text fields.
MAX_ORDER_REQUEST_BYTES = MAX_SCREENSHOTS_PER_ORDER * MAX_SCREENSHOT_BYTES + 64 * 1024
