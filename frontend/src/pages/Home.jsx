import PromoBanner from "../components/PromoBanner";
import Hero from "../sections/Hero";
import Features from "../sections/Features";
import Showcase from "../sections/Showcase";
import Premium from "../sections/Premium";
import BottomCta from "../sections/BottomCta";

export default function Home() {
  return (
    <>
      <Hero />
      <Features />
      <Showcase />
      <Premium />
      <PromoBanner />
      <BottomCta />
    </>
  );
}
