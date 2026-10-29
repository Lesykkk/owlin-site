import Panel from "../../components/Panel";
import { formatDate, formatPlaytime } from "../../lib/format";
import styles from "./Stats.module.css";

export default function Stats({ stats }) {
  const items = [
    { label: "Launches", value: stats.launches },
    { label: "Playtime", value: formatPlaytime(stats.playtimeSeconds) },
    { label: "Last launch", value: formatDate(stats.lastLaunchAt) },
    { label: "Version", value: stats.version },
  ];

  return (
    <Panel title="Statistics">
      <dl className={styles.grid}>
        {items.map((item) => (
          <div key={item.label} className={styles.tile}>
            <dt>{item.label}</dt>
            <dd>{item.value}</dd>
          </div>
        ))}
      </dl>
    </Panel>
  );
}
