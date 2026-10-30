import { PRODUCTS } from "../config/plans";
import { formatDate } from "./format";

const MODULE_NAMES = Object.fromEntries(PRODUCTS.filter((product) => !product.includes).map((product) => [product.id, product.name]));

// The modules a product unlocks. A bundle lists them; a single product is its own module.
const modulesOf = (product) => product.includes ?? [product.id];

// For each module that a promotion opens for everyone right now: the date that promotion ends.
// When several promotions open the same module, the latest end counts.
export function freeUntilByModule(promotions = []) {
  const until = {};
  promotions.forEach((promotion) => {
    promotion.modules.forEach((moduleId) => {
      if (!until[moduleId] || promotion.endsAt > until[moduleId]) until[moduleId] = promotion.endsAt;
    });
  });
  return until;
}

// What is free right now inside a product: `modules` are their names, `until` the date the last one ends.
// Null when nothing in the product is free.
export function freeNowInProduct(product, promotions) {
  const until = freeUntilByModule(promotions);
  const free = modulesOf(product).filter((moduleId) => until[moduleId]);
  if (free.length === 0) return null;

  const names = free.map((moduleId) => MODULE_NAMES[moduleId] ?? moduleId);
  const ends = free.map((moduleId) => until[moduleId]).sort().at(-1);
  return { names, endsAt: ends, isEverything: free.length === modulesOf(product).length };
}

export function freeSentence({ names, endsAt }) {
  return `${names.join(" and ")} ${names.length > 1 ? "are" : "is"} free for everyone until ${formatDate(endsAt)}.`;
}
