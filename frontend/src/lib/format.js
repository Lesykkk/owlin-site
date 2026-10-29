const euro = new Intl.NumberFormat("en-IE", { style: "currency", currency: "EUR" });

export function formatPrice(cents) {
  return euro.format(cents / 100);
}

const date = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric" });

export function formatDate(value) {
  return date.format(new Date(value));
}

const dateTime = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export function formatDateTime(value) {
  return dateTime.format(new Date(value));
}

export function daysLeft(value) {
  return Math.max(0, Math.ceil((new Date(value) - Date.now()) / 86_400_000));
}

export function formatPlaytime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${hours} h ${minutes} min`;
}
