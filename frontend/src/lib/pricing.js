import { PRODUCTS } from "../config/plans";

export function perMonthCents(priceCents, period) {
  return period.months ? Math.round(priceCents / period.months) : null;
}

// How much a bundle saves compared with buying its parts separately for the same period.
export function bundleSavingsPercent(product, periodId) {
  if (!product.includes) return 0;

  const separateCents = product.includes.reduce(
    (sum, id) => sum + PRODUCTS.find((part) => part.id === id).prices[periodId],
    0,
  );
  return Math.round((1 - product.prices[periodId] / separateCents) * 100);
}
