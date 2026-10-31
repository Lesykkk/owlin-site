import { useEffect, useState } from "react";
import Button from "../components/Button";
import { Chip, ChipList } from "../components/Chip";
import ExampleVideo from "../components/ExampleVideo";
import Panel from "../components/Panel";
import PlatformIcon from "../components/PlatformIcon";
import SegmentedControl from "../components/SegmentedControl";
import TextField from "../components/TextField";
import {
  PROMO_DAYS,
  PROMO_PLATFORMS,
  PROMO_REWARDS,
  PROMO_LINK_TARGETS,
  PROMO_RULES,
} from "../config/promo";
import { useAuth } from "../hooks/useAuth";
import { useMyPromo, useSubmitPromoClaim } from "../hooks/queries";
import { clearDraft, readDraft, saveDraft } from "../lib/promoDraft";
import { parseVideoLink } from "../lib/videoLinks";
import Submitted from "../sections/checkout/Submitted";
import styles from "./Promo.module.css";

const escapeForRegExp = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const LINK_PATTERN = new RegExp(`(${PROMO_LINK_TARGETS.map(escapeForRegExp).join("|")})`);

// Shows the Discord invite and the site address inside a rule as highlighted links.
function RuleText({ text }) {
  return text.split(LINK_PATTERN).map((part, index) => {
    if (index % 2 === 0) return part;
    const href = part.startsWith("http") ? part : `https://${part}`;
    return (
      <a key={part} className={styles.highlight} href={href} target="_blank" rel="noopener noreferrer">
        {part}
      </a>
    );
  });
}

const PLATFORM_OPTIONS = PROMO_PLATFORMS.map((platform) => ({
  ...platform,
  icon: <PlatformIcon platformId={platform.id} />,
}));

function requirementLabel(platform) {
  return platform.minViews === null ? "reviewed manually" : `${platform.minViews.toLocaleString("en-US")}+ views`;
}

export default function Promo() {
  const { user, isLoading: isAuthLoading, login } = useAuth();
  // A form filled in before the login redirect comes back once, and is deleted at once.
  const [draft] = useState(readDraft);
  useEffect(() => clearDraft(), []);

  const [rewardId, setRewardId] = useState(PROMO_REWARDS.some((item) => item.id === draft?.rewardId) ? draft.rewardId : PROMO_REWARDS[0].id);
  const [platformId, setPlatformId] = useState(PROMO_PLATFORMS.some((item) => item.id === draft?.platformId) ? draft.platformId : PROMO_PLATFORMS[0].id);
  const [link, setLink] = useState(typeof draft?.link === "string" ? draft.link : "");
  const [isConfirmed, setIsConfirmed] = useState(draft?.isConfirmed === true);
  const [error, setError] = useState("");
  const claim = useSubmitPromoClaim();
  const [isSubmitted, setIsSubmitted] = useState(false);

  // Only used to show the slots and to disable the button when all are taken. The server enforces the limit.
  const { data: promo } = useMyPromo();
  const slots = promo?.slots;
  const isFull = slots ? slots.used >= slots.max : false;
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

    // Quick feedback without a round trip; the server repeats every check.
    const video = parseVideoLink(link, platformId);
    if (video.error) {
      setError(video.error);
      return;
    }
    if (!isConfirmed) {
      setError("Confirm that the video follows the rules.");
      return;
    }

    // Guests are sent to log in first and come back to this form.
    if (!user) {
      if (isAuthLoading) return;
      saveDraft({ rewardId, platformId, link, isConfirmed });
      login();
      return;
    }

    try {
      await claim.mutateAsync({ platform: platformId, url: link.trim(), rewardProduct: rewardId });
      setIsSubmitted(true);
    } catch (claimError) {
      setError(claimError.message);
    }
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
    <div className={`container ${styles.page}`}>
      <h1 className={styles.title}>Video promo</h1>
      <p className={styles.lead}>
        Make a video about Owlin and get {PROMO_DAYS} days of Spoofer or DLC Unlock for free.
      </p>

      <div className={styles.requirements}>
        <ChipList>
          {PROMO_PLATFORMS.map((item) => (
            <Chip key={item.id}>
              <PlatformIcon platformId={item.id} />
              <strong>{item.label}</strong>
              {requirementLabel(item)}
            </Chip>
          ))}
        </ChipList>
      </div>

      <div className={styles.layout}>
        <form className={styles.form} onSubmit={handleSubmit}>
          <Panel title="Rules">
            <ul className={styles.rules}>
              {PROMO_RULES.map((rule) => (
                <li key={rule}>
                  <RuleText text={rule} />
                </li>
              ))}
            </ul>
            {slots && (
              <p className={styles.slots}>
                Your promo slots: {slots.used} of {slots.max} in use
              </p>
            )}
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
                The video mentions or shows Owlin, links to our Discord server or owlin.software, does not advertise competitors.
              </span>
            </label>

            {error && (
              <p className={styles.error} role="alert">
                {error}
              </p>
            )}
            {isFull && (
              <p className={styles.error} role="alert">
                All {slots.max} promo slots are in use. A slot frees up when a video is rejected or its reward expires.
              </p>
            )}
            <Button type="submit" variant="primary" loading={claim.isPending} disabled={isFull} className={styles.submit}>
              {claim.isPending ? "Sending…" : user || isAuthLoading ? "Submit for review" : "Log in to submit"}
            </Button>
          </Panel>
        </form>
        <ExampleVideo />
      </div>
    </div>
  );
}
