import { formatPrice } from "./format";

export function amountLabel(method, priceCents) {
  const euro = formatPrice(priceCents);

  switch (method.amount.kind) {
    case "fiat":
      return euro;
    case "stable":
      return `${(priceCents / 100).toFixed(2)} ${method.amount.symbol}`;
    case "atLeast":
      return `${euro} or more`;
    default:
      return `${euro} in ${method.amount.symbol} at the current rate`;
  }
}

// What the Copy button puts on the clipboard for the amount: the bare number, without currency.
// Coins converted at the current rate have no fixed number, so there is nothing to copy.
function amountCopyValue(method, priceCents) {
  return method.amount.kind === "manual" ? null : (priceCents / 100).toFixed(2);
}

// Everything the user needs to see and copy when paying with a given method.
// `copyValue` defaults to `value`; null hides the Copy button.
export function paymentRows(method, priceCents) {
  return [
    ...method.details,
    { label: "Amount", value: amountLabel(method, priceCents), copyValue: amountCopyValue(method, priceCents) },
  ];
}
