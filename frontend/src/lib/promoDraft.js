// The promo form a guest filled in is kept for the trip to the Discord login and back, so they do not
// type it again. It lives in sessionStorage (gone with the tab), is read once when the page opens and
// deleted right away, and is ignored when older than MAX_AGE_MS.
const KEY = "owlin:promo-draft";
const MAX_AGE_MS = 15 * 60 * 1000;

export function saveDraft(draft) {
  try {
    sessionStorage.setItem(KEY, JSON.stringify({ ...draft, savedAt: Date.now() }));
  } catch {
    // Without storage the form is simply empty after logging in.
  }
}

export function readDraft() {
  try {
    const draft = JSON.parse(sessionStorage.getItem(KEY));
    return draft && Date.now() - draft.savedAt < MAX_AGE_MS ? draft : null;
  } catch {
    return null;
  }
}

export function clearDraft() {
  try {
    sessionStorage.removeItem(KEY);
  } catch {
    // Nothing to remove.
  }
}
