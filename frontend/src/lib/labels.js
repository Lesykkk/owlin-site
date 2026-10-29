import { PAYMENT_METHODS, resolvePaymentOption } from "../config/paymentMethods";
import { PERIODS, PRODUCTS } from "../config/plans";

// Turns the ids the API stores into the names shown to people. Unknown ids show as they are.
export const productName = (id) => PRODUCTS.find((product) => product.id === id)?.name ?? id;
export const periodLabel = (id) => PERIODS.find((period) => period.id === id)?.label ?? id;

export function methodLabel(methodId, coinId) {
  const method = PAYMENT_METHODS.find((item) => item.id === methodId);
  if (!method) return methodId;
  return resolvePaymentOption(method, coinId).label;
}

// What the payment method asks the user to write, without the "(optional)" hint.
export function proofLabel(methodId, coinId) {
  const method = PAYMENT_METHODS.find((item) => item.id === methodId);
  if (!method) return "Proof";
  return resolvePaymentOption(method, coinId).proofField.label.replace(/\s*\(optional\)$/, "");
}
