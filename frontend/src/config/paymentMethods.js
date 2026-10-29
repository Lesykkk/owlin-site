// `amount.kind`: fiat = exact euro amount, stable = 1:1 stablecoin,
// atLeast = gift card (extra goes to the balance), manual = converted at the current rate.
const SOLANA_ADDRESS = "2Pbf9k8am56pGL6SgcNjDwKQEo25ARs1Sa7LCEXn9aQR";

// The transaction hash (TXID) lets us find a crypto payment on the blockchain in seconds.
const TX_HASH_FIELD = { label: "Transaction hash (optional)", placeholder: "Paste the transaction hash (TXID)" };

const CRYPTO_COINS = [
  {
    id: "sol",
    label: "SOL",
    hint: "Send SOL on the Solana network only.",
    amount: { kind: "manual", symbol: "SOL" },
    proofField: TX_HASH_FIELD,
    details: [
      { label: "Network", value: "Solana" },
      { label: "Address", value: SOLANA_ADDRESS },
    ],
  },
  {
    id: "usdc-solana",
    label: "USDC (Solana)",
    hint: "Send USDC on the Solana network only.",
    amount: { kind: "stable", symbol: "USDC" },
    proofField: TX_HASH_FIELD,
    details: [
      { label: "Network", value: "Solana" },
      { label: "Address", value: SOLANA_ADDRESS },
    ],
  },
  {
    id: "usdc-base",
    label: "USDC (Base)",
    hint: "Send USDC on the Base network only.",
    amount: { kind: "stable", symbol: "USDC" },
    proofField: TX_HASH_FIELD,
    details: [
      { label: "Network", value: "Base" },
      { label: "Address", value: "0xb6D43Cce61939ebA1bC5021EA59A22426cA96728" },
    ],
  },
  {
    id: "usdt-trc20",
    label: "USDT (TRC20)",
    hint: "Send USDT on the TRON (TRC20) network only.",
    amount: { kind: "stable", symbol: "USDT" },
    proofField: TX_HASH_FIELD,
    details: [
      { label: "Network", value: "TRON (TRC20)" },
      { label: "Address", value: "TQ4YGK3X2Yu78EXkjjEmzHGsARDMZPRSWT" },
    ],
  },
  {
    id: "btc",
    label: "BTC",
    hint: "Send Bitcoin on the Bitcoin network only.",
    amount: { kind: "manual", symbol: "BTC" },
    proofField: TX_HASH_FIELD,
    details: [
      { label: "Network", value: "Bitcoin" },
      { label: "Address", value: "bc1qltu4kfg6n392e93z2g2cjxv09sdneazjwqsamu" },
    ],
  },
];

// Top-level choices. A method with `coins` asks for one more choice (which coin).
export const PAYMENT_METHODS = [
  {
    id: "paypal",
    label: "PayPal",
    summary: "Pay by PayPal",
    hint: "Send the exact amount to this PayPal address as Friends & Family.",
    amount: { kind: "fiat" },
    proofField: { label: "PayPal username (optional)", placeholder: "Your PayPal name" },
    details: [{ label: "PayPal email", value: "pedrokapucci@owlin.software" }],
  },
  {
    id: "crypto",
    label: "Crypto",
    summary: "SOL, USDC, USDT, BTC",
    coins: CRYPTO_COINS,
  },
  {
    id: "steam",
    label: "Steam Gift Card",
    summary: "Send a gift card",
    hint: "Send the gift card code to this Steam profile. Anything above the price is added to your balance.",
    amount: { kind: "atLeast" },
    proofField: { label: "Steam username (optional)", placeholder: "Your Steam name" },
    details: [
      {
        label: "Steam profile",
        value: "https://steamcommunity.com/id/lesykkk/",
        href: "https://steamcommunity.com/id/lesykkk/",
      },
    ],
  },
];

// The concrete thing the user pays with: the method itself, or the chosen coin of a crypto method.
export function resolvePaymentOption(method, coinId) {
  if (!method.coins) return method;
  return method.coins.find((coin) => coin.id === coinId) ?? method.coins[0];
}
