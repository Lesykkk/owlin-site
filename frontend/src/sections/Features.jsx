import FeatureCard from "../components/FeatureCard";
import SectionHeading from "../components/SectionHeading";
import { FEATURES } from "../config/features";
import styles from "./Features.module.css";

export default function Features() {
  return (
    <section id="features" className={`container ${styles.section}`}>
      <SectionHeading
        eyebrow="Built around your drive"
        title="Small menu. Big possibilities."
        aside="Everyday tools and optional premium features, together in one familiar interface."
      />
      <div className={styles.grid}>
        {FEATURES.map((feature) => (
          <FeatureCard key={feature.id} {...feature} />
        ))}
      </div>
    </section>
  );
}
