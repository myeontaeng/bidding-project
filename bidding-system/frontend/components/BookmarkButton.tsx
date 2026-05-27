"use client";

import { useEffect, useState } from "react";
import type { Announcement } from "@/lib/api";
import { isBookmarked, toggleBookmark } from "@/lib/bookmarks";

interface Props {
  ann: Announcement;
}

export default function BookmarkButton({ ann }: Props) {
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setSaved(isBookmarked(ann.id));
  }, [ann.id]);

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const next = toggleBookmark(ann);
    setSaved(next);
    window.dispatchEvent(new Event("bookmarks-changed"));
  };

  return (
    <button
      onClick={handleClick}
      title={saved ? "북마크 해제" : "북마크 저장"}
      className={`shrink-0 p-1 rounded-md transition-colors ${
        saved
          ? "text-yellow-500 hover:text-yellow-600"
          : "text-gray-300 hover:text-gray-500"
      }`}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill={saved ? "currentColor" : "none"}
        stroke="currentColor"
        strokeWidth={2}
        className="w-4 h-4"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z"
        />
      </svg>
    </button>
  );
}
