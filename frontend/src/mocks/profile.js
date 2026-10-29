// Demo data for the profile page. Replace with API responses once the backend exists.
const daysFromNow = (days) => new Date(Date.now() + days * 86_400_000).toISOString();

export const MOCK_PROFILE = {
  balanceCents: 350,

  // Keyed by product id; a missing key means "no active subscription".
  subscriptions: {
    "dlc-unlock": { startedAt: daysFromNow(-67), expiresAt: daysFromNow(23) },
    spoofer: null,
  },

  stats: {
    launches: 128,
    playtimeSeconds: 48 * 3600 + 12 * 60,
    lastLaunchAt: daysFromNow(-1),
    version: "1.5.11",
  },

  // Newest first. Approved claims carry the date their free days run out.
  promoClaims: [
    {
      id: "claim-4",
      createdAt: daysFromNow(-0.2),
      platformId: "tiktok",
      rewardId: "spoofer",
      url: "https://www.tiktok.com/@driver_max/video/7701293106699698176",
      status: "review",
    },
    {
      id: "claim-3",
      createdAt: daysFromNow(-3),
      platformId: "youtube",
      rewardId: "dlc-unlock",
      url: "https://www.youtube.com/watch?v=dKiSnET6eNs",
      status: "approved",
      expiresAt: daysFromNow(4),
    },
    {
      id: "claim-2",
      createdAt: daysFromNow(-12),
      platformId: "other",
      rewardId: "spoofer",
      url: "https://example.com/clip",
      status: "approved",
      expiresAt: daysFromNow(-5),
    },
    {
      id: "claim-1",
      createdAt: daysFromNow(-15),
      platformId: "tiktok",
      rewardId: "spoofer",
      url: "https://www.tiktok.com/@driver_max/video/7690000000000000000",
      status: "rejected",
      reason: "Owlin is not mentioned in the video.",
    },
  ],

  orders: [
    {
      id: "order-3",
      createdAt: daysFromNow(-0.1),
      product: "Spoofer",
      period: "3 months",
      method: "USDT (TRC20)",
      amountCents: 900,
      status: "review",
    },
    {
      id: "order-2",
      createdAt: daysFromNow(-67),
      product: "DLC Unlock",
      period: "3 months",
      method: "PayPal",
      amountCents: 499,
      status: "approved",
      balanceAddedCents: 101,
    },
    {
      id: "order-1",
      createdAt: daysFromNow(-120),
      product: "DLC Unlock",
      period: "1 month",
      method: "BTC",
      amountCents: 199,
      status: "rejected",
      reason: "Amount does not match the order.",
    },
  ],
};
