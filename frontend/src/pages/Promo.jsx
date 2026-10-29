import { useState } from "react";
import Button from "../components/Button";
import Panel from "../components/Panel";
import PlatformIcon from "../components/PlatformIcon";
import SegmentedControl from "../components/SegmentedControl";
import TextField from "../components/TextField";
import {
  MAX_PROMO_SLOTS,
  MAX_VIDEO_AGE_DAYS,
  PROMO_DAYS,
  PROMO_PLATFORMS,
  PROMO_REWARDS,
  PROMO_RULES,
} from "../config/promo";
import { countOccupiedSlots } from "../lib/promo";
import { parseVideoLink } from "../lib/videoLinks";
import { isVideoUsed } from "../mocks/promo";
import { MOCK_PROFILE } from "../mocks/profile";
import Submitted from "../sections/checkout/Submitted";
import styles from "./Promo.module.css";

const PLATFORM_OPTIONS = PROMO_PLATFORMS.map((platform) => ({
  ...platform,
  icon: <PlatformIcon platformId={platform.id} />,
}));

function requirementLabel(platform) {
  return platform.minViews === null ? "reviewed manually" : `${platform.minViews.toLocaleString("en-US")}+ views`;
}

export default function Promo() {
  const [rewardId, setRewardId] = useState(PROMO_REWARDS[0].id);
  const [platformId, setPlatformId] = useState(PROMO_PLATFORMS[0].id);
  const [link, setLink] = useState("");
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [error, setError] = useState("");
  const [isChecking, setIsChecking] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  // Mock claims until the backend provides them.
  const usedSlots = countOccupiedSlots(MOCK_PROFILE.promoClaims);
  const isFull = usedSlots >= MAX_PROMO_SLOTS;
  const platform = PROMO_PLATFORMS.find((item) => item.id === platformId);

  function handlePlatformChange(id) {
    setPlatformId(id);
    setError("");
  }

  function handleLinkChange(value) {
    setLink(value);
    setError("");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const video = parseVideoLink(link, platformId);
    if (video.error) {
      setError(video.error);
      return;
    }
    if (!isConfirmed) {
      setError("Confirm that the video follows the rules.");
      return;
    }

    setIsChecking(true);
    const isUsed = await isVideoUsed(video.key);
    setIsChecking(false);

    if (isUsed) {
      setError("This video was already used for a promo reward. Submit a different one.");
      return;
    }

    // TODO: send { rewardId, platformId, url } to the backend.
    setIsSubmitted(true);
  }

  if (isSubmitted) {
    return (
      <Submitted>
        Your video is under review. We check it manually and add {PROMO_DAYS} days of the plan you chose to your
        account. You can follow the status in your profile.
      </Submitted>
    );
  }

  return (
    <form className={`container ${styles.page}`} onSubmit={handleSubmit}>
      <h1 className={styles.title}>Video promo</h1>
      <p className={styles.lead}>
        Make a video about Owlin and get {PROMO_DAYS} days of Spoofer or DLC Unlock for free.
      </p>

      <ul className={styles.requirements}>
        {PROMO_PLATFORMS.map((item) => (
          <li key={item.id}>
            <PlatformIcon platformId={item.id} />
            <strong>{item.label}</strong>
            {requirementLabel(item)}
          </li>
        ))}
      </ul>

      <Panel title="Rules">
        <ul className={styles.rules}>
          {PROMO_RULES.map((rule) => (
            <li key={rule}>{rule}</li>
          ))}
        </ul>
        <p className={styles.slots}>
          Your promo slots: {usedSlots} of {MAX_PROMO_SLOTS} in use
        </p>
      </Panel>

      <Panel title="1. Choose your reward">
        <SegmentedControl label="Reward" options={PROMO_REWARDS} value={rewardId} onChange={setRewardId} />
      </Panel>

      <Panel title="2. Video link" required>
        <div className={styles.platform}>
          <SegmentedControl label="Platform" options={PLATFORM_OPTIONS} value={platformId} onChange={handlePlatformChange} />
        </div>
        <TextField label={`${platform.label} link`} value={link} onChange={handleLinkChange} placeholder={platform.placeholder} />
        <p className={styles.hint}>
          Each video can be used only once, so use the video's own link, not a profile link.
          {platformId === "other" && " Videos on other sites are checked manually."}
        </p>

        <label className={styles.confirm}>
          <input type="checkbox" checked={isConfirmed} onChange={(event) => setIsConfirmed(event.target.checked)} />
          <span>
            The video mentions Owlin, does not advertise competitors and was published within the last{" "}
            {MAX_VIDEO_AGE_DAYS} days.
          </span>
        </label>

        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
        {isFull && (
          <p className={styles.error} role="alert">
            All {MAX_PROMO_SLOTS} promo slots are in use. A slot frees up when a video is rejected or its reward expires.
          </p>
        )}
        <Button type="submit" variant="primary" disabled={isChecking || isFull} className={styles.submit}>
          {isChecking ? "Checking…" : "Submit for review"}
        </Button>
      </Panel>
    </form>
  );
}
