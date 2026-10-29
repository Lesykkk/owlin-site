// Demo data for the admin page. Replace with API responses once the backend exists.
const hoursAgo = (hours) => new Date(Date.now() - hours * 3_600_000).toISOString();

export const MOCK_ADMIN_VIDEOS = [
  {
    id: "video-3",
    createdAt: hoursAgo(1),
    user: { username: "driver_max", discordId: "580797344010731543" },
    platformId: "tiktok",
    rewardId: "spoofer",
    url: "https://www.tiktok.com/@driver_max/video/7701293106699698176",
    views: null,
    status: "review",
  },
  {
    id: "video-2",
    createdAt: hoursAgo(5),
    user: { username: "trucker_anna", discordId: "412345678901234567" },
    platformId: "youtube",
    rewardId: "dlc-unlock",
    url: "https://www.youtube.com/watch?v=dKiSnET6eNs",
    views: null,
    status: "review",
  },
  {
    id: "video-1",
    createdAt: hoursAgo(30),
    user: { username: "nightrider", discordId: "398765432109876543" },
    platformId: "other",
    rewardId: "spoofer",
    url: "https://example.com/clip",
    views: 2400,
    status: "approved",
  },
];

export const MOCK_ADMIN_ORDERS = [
  {
    id: "order-3",
    createdAt: hoursAgo(2),
    user: { username: "driver_max", discordId: "580797344010731543" },
    product: "Spoofer",
    period: "3 months",
    method: "USDT (TRC20)",
    amountCents: 900,
    proof: { label: "Transaction hash", value: "a1f3c9e07b52d84c6e01f9a3b7d2c5e8" },
    screenshots: ["/owl.png"],
    status: "review",
  },
  {
    id: "order-2",
    createdAt: hoursAgo(9),
    user: { username: "trucker_anna", discordId: "412345678901234567" },
    product: "Spoofer + DLC Unlock",
    period: "Lifetime",
    method: "PayPal",
    amountCents: 2499,
    proof: { label: "PayPal username", value: "anna.k" },
    screenshots: ["/owl.png", "/owl.png"],
    status: "review",
  },
  {
    id: "order-1",
    createdAt: hoursAgo(51),
    user: { username: "nightrider", discordId: "398765432109876543" },
    product: "DLC Unlock",
    period: "1 month",
    method: "Steam Gift Card",
    amountCents: 199,
    proof: null,
    screenshots: ["/owl.png"],
    status: "approved",
  },
];
