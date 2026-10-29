import { startingPriceCents } from "../config/plans";
import { formatPrice } from "../lib/format";
import Button from "./Button";
import styles from "./ProductCard.module.css";

export default function ProductCard({ product, href }) {
  return (
    <div className={`${styles.card} ${product.highlighted ? styles.highlighted : ""}`}>
      <div className={styles.top}>
        <span className={styles.label}>{product.name}</span>
        {product.badge && <span className={styles.badge}>{product.badge}</span>}
      </div>
      <p className={styles.description}>{product.description}</p>
      <div className={styles.from}>From</div>
      <div className={styles.price}>{formatPrice(startingPriceCents(product))}</div>
      <Button href={href} variant={product.highlighted ? "primary" : "secondary"} className={styles.action}>
        See plans
      </Button>
    </div>
  );
}
