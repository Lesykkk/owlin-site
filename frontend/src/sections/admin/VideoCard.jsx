import { useState } from "react";
import PlatformIcon from "../../components/PlatformIcon";
import TextField from "../../components/TextField";
import { PROMO_DAYS, PROMO_PLATFORMS, PROMO_REWARDS } from "../../config/promo";
import ReviewActions from "./ReviewActions";
import ReviewCard, { Details } from "./ReviewCard";
import styles from "./VideoCard.module.css";

const formatViews = (views) => views.toLocaleString("en-US");

export default function VideoCard({ video, onApprove, onReject }) {
  const [views, setViews] = useState("");

  const platform = PROMO_PLATFORMS.find((item) => item.id === video.platformId);
  const reward = PROMO_REWARDS.find((item) => item.id === video.rewardId);

  // Platforms with a fixed threshold need the checked view count; "Other" is up to the admin.
  const viewCount = Number(views.replace(/[\s,]/g, ""));
  const hasViews = views.trim() !== "" && Number.isInteger(viewCount) && viewCount >= 0;
  const needsViews = platform.minViews !== null;
  const meetsViews = !needsViews || (hasViews && viewCount >= platform.minViews);
  const canApprove = meetsViews && (views.trim() === "" || hasViews);

  let hint = "Check the video for an Owlin mention, no competitors and a publish date within 7 days.";
  if (needsViews && !hasViews) hint = `Enter the views you see (${formatViews(platform.minViews)}+ needed).`;
  else if (needsViews && !meetsViews) hint = `Below the ${formatViews(platform.minViews)} views needed. Reject it, or enter the real count.`;

  const details = [
    {
      label: "Platform",
      value: (
        <span className={styles.platform}>
          <PlatformIcon platformId={platform.id} />
          {platform.label}
        </span>
      ),
    },
    { label: "Reward", value: `${reward.label} · ${PROMO_DAYS} days` },
    {
      label: "Video",
      value: (
        <a href={video.url} target="_blank" rel="noopener noreferrer">
          {video.url}
        </a>
      ),
    },
  ];

  return (
    <ReviewCard user={video.user} createdAt={video.createdAt} status={video.status}>
      <Details items={details} />

      {video.reason && <p className={styles.reason}>Rejected: {video.reason}</p>}
      {video.status === "approved" && (
        <p className={styles.note}>
          {video.views !== null && `Views checked: ${formatViews(video.views)} · `}
          {PROMO_DAYS} days of {reward.label} granted
        </p>
      )}

      {video.status === "review" && (
        <ReviewActions
          canApprove={canApprove}
          hint={hint}
          hintIsError={needsViews && hasViews && !meetsViews}
          onApprove={() => onApprove(video.id, hasViews ? viewCount : null)}
          onReject={(reason) => onReject(video.id, reason)}
        >
          <div className={styles.viewsField}>
            <TextField label="Views" value={views} onChange={setViews} placeholder={needsViews ? formatViews(platform.minViews) : "optional"} />
          </div>
        </ReviewActions>
      )}
    </ReviewCard>
  );
}
