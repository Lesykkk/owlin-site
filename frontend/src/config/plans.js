// Prices are in euro cents, keyed by period id.
export const PERIODS = [
  { id: "1m", label: "1 month", months: 1 },
  { id: "3m", label: "3 months", months: 3 },
  { id: "6m", label: "6 months", months: 6 },
  { id: "lifetime", label: "Lifetime", months: null },
];

export const DEFAULT_PERIOD_ID = "3m";

export const PRODUCTS = [
  {
    id: "dlc-unlock",
    name: "DLC Unlock",
    description: "Access DLC content with Owlin DLC Unlock.",
    features: ["DLC Unlock module", "All free Owlin tools"],
    prices: { "1m": 199, "3m": 499, "6m": 799, lifetime: 1499 },
  },
  {
    id: "spoofer",
    name: "Spoofer",
    description: "The Spoofer module to Bypass Bans.",
    features: ["Spoofer module", "All free Owlin tools"],
    prices: { "1m": 399, "3m": 899, "6m": 1399, lifetime: 1999 },
  },
  {
    id: "spoofer-dlc-unlock",
    name: "Spoofer + DLC Unlock",
    description: "Both modules together at a better price.",
    features: ["Spoofer module", "DLC Unlock module", "All free Owlin tools"],
    includes: ["spoofer", "dlc-unlock"],
    badge: "Best value",
    highlighted: true,
    prices: { "1m": 499, "3m": 1299, "6m": 1900, lifetime: 3099 },
  },
];

export function startingPriceCents(product) {
  return Math.min(...Object.values(product.prices));
}
