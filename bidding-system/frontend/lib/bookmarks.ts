import type { Announcement } from "./api";

const KEY = "bm_announcements";

export function getBookmarks(): Announcement[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? "[]");
  } catch {
    return [];
  }
}

export function isBookmarked(id: number): boolean {
  return getBookmarks().some((a) => a.id === id);
}

export function toggleBookmark(ann: Announcement): boolean {
  const current = getBookmarks();
  const exists = current.some((a) => a.id === ann.id);
  if (exists) {
    localStorage.setItem(KEY, JSON.stringify(current.filter((a) => a.id !== ann.id)));
    return false;
  } else {
    localStorage.setItem(KEY, JSON.stringify([ann, ...current]));
    return true;
  }
}

export function getBookmarkCount(): number {
  return getBookmarks().length;
}
