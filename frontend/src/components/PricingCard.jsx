import { useActivePromotions } from "../hooks/queries";
import { freeNowInProduct, freeSentence } from "../lib/freeNow";
import { bundleSavingsPercent, perMonthCents } from "../lib/pricing";
import { formatPrice } from "../lib/format";
import Button from "./Button";
import { CheckIcon } from "./Icons";
import styles from "./PricingCard.module.css";

export default function PricingCard({ product, period }) {
  const priceCents = product.prices[period.id];
  const monthly = perMonthCents(priceCents, period);
  const savings = bundleSavingsPercent(product, period.id);
  const { data: promotions } = useActivePromotions();
  const free = freeNowInProduct(product, promotions?.promotions);

  return (
    <div className={`${styles.card} ${product.highlighted ? styles.highlighted : ""}`}>
      <div className={styles.top}>
        <span className={styles.label}>{product.name}</span>
        {product.badge && <span className={styles.badge}>{product.badge}</span>}
      </div>

      <p className={styles.description}>{product.description}</p>

      <div className={styles.price}>{formatPrice(priceCents)}</div>
      <div className={styles.hint}>{monthly ? `${formatPrice(monthly)} / month` : "One-time payment"}</div>
      {savings > 0 && <div className={styles.savings}>Save {savings}% vs buying separately</div>}
      {free && <div className={styles.free}>{freeSentence(free)}</div>}

      <ul className={styles.features}>
        {product.features.map((feature) => (
          <li key={feature}>
            <CheckIcon />
            {feature}
          </li>
        ))}
      </ul>

      <Button href={`/checkout?product=${product.id}&period=${period.id}`} variant={product.highlighted ? "primary" : "secondary"} className={styles.buy}>
        Buy {period.label.toLowerCase()}
      </Button>
    </div>
  );
}
