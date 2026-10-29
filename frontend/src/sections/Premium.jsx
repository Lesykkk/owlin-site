import ProductCard from "../components/ProductCard";
import SectionHeading from "../components/SectionHeading";
import { PRODUCTS } from "../config/plans";
import styles from "./Premium.module.css";

export default function Premium() {
  return (
    <section id="premium" className={`container ${styles.section}`}>
      <SectionHeading
        eyebrow="Go a little further"
        title="Your next upgrade."
        aside="Get Spoofer, DLC Unlock or both together. Everything else stays free."
      />

      <div className={styles.products}>
        {PRODUCTS.map((product) => (
          <ProductCard key={product.id} product={product} href="/pricing" />
        ))}
      </div>

      <p className={styles.note}>
        Browse freely. You sign in with Discord only when you buy. PayPal, crypto or Steam gift card.
      </p>
    </section>
  );
}
