// Claims that still occupy a slot: waiting for review, or approved and not yet expired.
export function countOccupiedSlots(claims, now = Date.now()) {
  return claims.filter(
    (claim) => claim.status === "review" || (claim.status === "approved" && new Date(claim.expiresAt) > now),
  ).length;
}
