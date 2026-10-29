import { useState } from "react";
import Eyebrow from "../components/Eyebrow";
import SegmentedControl from "../components/SegmentedControl";
import PricingCard from "../components/PricingCard";
import MethodIcon from "../components/MethodIcon";
import PromoBanner from "../components/PromoBanner";
import { FAQ } from "../config/faq";
import { PAYMENT_METHODS } from "../config/paymentMethods";
import { DEFAULT_PERIOD_ID, PERIODS, PRODUCTS } from "../config/plans";
import styles from "./Pricing.module.css";

export default function Pricing() {
  const [periodId, setPeriodId] = useState(DEFAULT_PERIOD_ID);
  const period = PERIODS.find((item) => item.id === periodId);

  return (
    <>
      <section className={`container ${styles.intro}`}>
        <Eyebrow className={styles.center}>Go a little further</Eyebrow>
        <h1 className={styles.title}>Choose your plan.</h1>
        <p className={styles.text}>Spoofer, DLC Unlock or both together. Everything else in Owlin stays free.</p>
        <SegmentedControl label="Billing period" options={PERIODS} value={periodId} onChange={setPeriodId} />
      </section>

      <section className={`container ${styles.plans}`}>
        {PRODUCTS.map((product) => (
          <PricingCard key={product.id} product={product} period={period} />
        ))}
      </section>

      <PromoBanner />

      <section className={`container ${styles.methods}`}>
        <h2 className={styles.heading}>Payment methods</h2>
        <p className={styles.note}>
          Pay, then upload a screenshot as proof. Sign in with Discord when you buy. We check payments manually.
        </p>
        <ul className={styles.chips}>
          {PAYMENT_METHODS.map((method) => (
            <li key={method.id}>
              <MethodIcon methodId={method.id} />
              {method.label}
            </li>
          ))}
        </ul>
      </section>

      <section className={`container ${styles.faq}`}>
        <h2 className={styles.heading}>Questions</h2>
        {FAQ.map((item) => (
          <details key={item.question} className={styles.item}>
            <summary>{item.question}</summary>
            <p>{item.answer}</p>
          </details>
        ))}
      </section>
    </>
  );
}
