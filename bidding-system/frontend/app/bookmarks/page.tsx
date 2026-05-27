"use client";

import { useEffect, useState } from "react";
import type { Announcement } from "@/lib/api";
import { getBookmarks } from "@/lib/bookmarks";
import AnnouncementCard from "@/components/AnnouncementCard";

export default function BookmarksPage() {
  const [bookmarks, setBookmarks] = useState<Announcement[]>([]);
  const [mounted, setMounted] = useState(false);

  const load = () => setBookmarks(getBookmarks());

  useEffect(() => {
    setMounted(true);
    load();
    window.addEventListener("bookmarks-changed", load);
    return () => window.removeEventListener("bookmarks-changed", load);
  }, []);

  if (!mounted) return null;

  return (
    <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">북마크</h1>
        <p className="text-sm text-gray-500 mt-1">저장된 공고 {bookmarks.length}건</p>
      </div>

      {bookmarks.length === 0 ? (
        <div className="text-center py-20 text-gray-400 space-y-2">
          <p className="text-4xl">🔖</p>
          <p>저장된 공고 없음</p>
          <p className="text-sm">
            공고 목록에서 ★ 버튼으로 저장하세요.{" "}
            <a href="/" className="text-blue-500 hover:underline">공고 보기</a>
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {bookmarks.map((ann) => (
            <AnnouncementCard key={ann.id} ann={ann} />
          ))}
        </div>
      )}
    </main>
  );
}
