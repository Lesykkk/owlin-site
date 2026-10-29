import { useState } from "react";
import { Navigate, useSearchParams } from "react-router-dom";
import Button from "../components/Button";
import Panel from "../components/Panel";
import TextField from "../components/TextField";
import { PAYMENT_METHODS, resolvePaymentOption } from "../config/paymentMethods";
import { PERIODS, PRODUCTS } from "../config/plans";
import { createOrder, submitOrder, uploadProof } from "../lib/api";
import { formatPrice } from "../lib/format";
import MethodPicker from "../sections/checkout/MethodPicker";
import OrderSummary from "../sections/checkout/OrderSummary";
import PaymentDetails from "../sections/checkout/PaymentDetails";
import ScreenshotUpload from "../sections/checkout/ScreenshotUpload";
import Submitted from "../sections/checkout/Submitted";
import styles from "./Checkout.module.css";

export default function Checkout() {
  const [params] = useSearchParams();
  const product = PRODUCTS.find((item) => item.id === params.get("product"));
  const period = PERIODS.find((item) => item.id === params.get("period"));

  // Without a valid plan in the link there is nothing to pay for.
  if (!product || !period || product.prices[period.id] === undefined) return <Navigate to="/pricing" replace />;
  return <CheckoutForm product={product} period={period} />;
}

function CheckoutForm({ product, period }) {
  const [methodId, setMethodId] = useState(PAYMENT_METHODS[0].id);
  const [coinId, setCoinId] = useState(PAYMENT_METHODS.find((item) => item.coins).coins[0].id);
  const [screenshots, setScreenshots] = useState([]);
  // One value per payment option, so a PayPal name never ends up in a transaction hash field.
  const [proofValues, setProofValues] = useState({});
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const method = PAYMENT_METHODS.find((item) => item.id === methodId);
  const option = resolvePaymentOption(method, coinId);
  const priceCents = product.prices[period.id];

  function handleScreenshotsChange(items) {
    setScreenshots(items);
    setError("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (screenshots.length === 0) {
      setError("Attach at least one screenshot as proof.");
      return;
    }

    setError("");
    setIsSubmitting(true);
    try {
      const files = screenshots.map((item) => item.file);
      // 1. The server prices the order and hands out one upload slot per file.
      const order = await createOrder({
        product: product.id,
        period: period.id,
        method: method.id,
        coin: method.coins ? coinId : null,
        files,
      });
      // 2. The files go straight to storage, then 3. the order is sent for review.
      await Promise.all(order.uploads.map((slot, index) => uploadProof(slot, files[index])));
      await submitOrder(order.id, {
        paths: order.uploads.map((slot) => slot.path),
        proofText: proofValues[option.id]?.trim() || null,
        note: note.trim() || null,
      });
      setIsSubmitted(true);
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isSubmitted) {
    return (
      <Submitted>
        Your payment is under review. We check screenshots manually and activate your plan afterwards. You can follow
        the status in your profile.
      </Submitted>
    );
  }

  return (
    <form className={`container ${styles.page}`} onSubmit={handleSubmit}>
      <div className={styles.main}>
        <h1 className={styles.title}>Checkout</h1>

        <Panel title="1. Payment method">
          <MethodPicker
            methods={PAYMENT_METHODS}
            methodId={methodId}
            onMethodChange={setMethodId}
            coinId={coinId}
            onCoinChange={setCoinId}
          />
        </Panel>

        <Panel title="2. Send payment">
          <PaymentDetails option={option} priceCents={priceCents} />
        </Panel>

        <Panel title="3. Upload proof" required>
          <ScreenshotUpload items={screenshots} onChange={handleScreenshotsChange} />
          <div className={styles.fields}>
            <TextField
              key={option.id}
              label={option.proofField.label}
              value={proofValues[option.id] ?? ""}
              onChange={(value) => setProofValues({ ...proofValues, [option.id]: value })}
              placeholder={option.proofField.placeholder}
            />
            <TextField label="Additional notes (optional)" value={note} onChange={setNote} placeholder="Anything we should know" />
          </div>
          {error && (
            <p className={styles.error} role="alert">
              {error}
            </p>
          )}
          <Button type="submit" variant="primary" disabled={isSubmitting} className={styles.submit}>
            {isSubmitting ? "Sending…" : "Submit for review"}
          </Button>
        </Panel>
      </div>

      <aside className={styles.aside}>
        <OrderSummary
          productName={product.name}
          periodLabel={period.label}
          totalLabel={formatPrice(priceCents)}
          features={product.features}
        />
      </aside>
    </form>
  );
}
