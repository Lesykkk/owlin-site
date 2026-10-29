export const MAX_SCREENSHOTS = 3;
export const MAX_SIZE_MB = 5;
const MAX_BYTES = MAX_SIZE_MB * 1024 * 1024;
const ALLOWED_TYPES = ["image/png", "image/jpeg", "image/webp"];

// Splits picked files into accepted ones and human-readable errors.
export function pickScreenshots(currentCount, files) {
  const accepted = [];
  const errors = [];

  for (const file of files) {
    if (currentCount + accepted.length >= MAX_SCREENSHOTS) {
      errors.push(`You can attach up to ${MAX_SCREENSHOTS} screenshots.`);
      break;
    }
    if (!ALLOWED_TYPES.includes(file.type)) {
      errors.push(`${file.name}: only PNG, JPG or WebP images.`);
    } else if (file.size > MAX_BYTES) {
      errors.push(`${file.name}: larger than ${MAX_SIZE_MB} MB.`);
    } else {
      accepted.push(file);
    }
  }

  return { accepted, errors };
}
