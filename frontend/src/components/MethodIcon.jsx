import { CardIcon, CoinIcon, GiftIcon } from "./Icons";

const ICONS = { paypal: CardIcon, crypto: CoinIcon, steam: GiftIcon };

export default function MethodIcon({ methodId, ...props }) {
  const Icon = ICONS[methodId];
  return Icon ? <Icon {...props} /> : null;
}
