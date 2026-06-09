"use client";

import { useRouter } from "next/navigation";

interface Props {
  currentPage: number;
  totalPages: number;
  query: Record<string, string | number | undefined>;
}

export default function Pagination({ currentPage, totalPages, query }: Props) {
  const router = useRouter();

  const go = (page: number) => {
    const p = new URLSearchParams();
    Object.entries(query).forEach(([k, v]) => {
      if (v !== undefined && v !== "" && k !== "page") p.set(k, String(v));
    });
    if (page > 1) p.set("page", String(page));
    router.push(`/?${p}`);
  };

  const pages = buildPageList(currentPage, totalPages);

  return (
    <div className="flex items-center justify-center gap-1">
      <button
        onClick={() => go(currentPage - 1)}
        disabled={currentPage <= 1}
        className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-30 hover:bg-gray-50 disabled:cursor-not-allowed"
      >
        ‹ 이전
      </button>

      {pages.map((p, i) =>
        p === "…" ? (
          <span key={`ellipsis-${i}`} className="px-2 text-gray-400 text-sm select-none">…</span>
        ) : (
          <button
            key={p}
            onClick={() => go(p as number)}
            className={`w-9 h-9 text-sm rounded-lg border transition-colors ${
              p === currentPage
                ? "bg-blue-600 text-white border-blue-600 font-semibold"
                : "border-gray-300 hover:bg-gray-50 text-gray-700"
            }`}
          >
            {p}
          </button>
        )
      )}

      <button
        onClick={() => go(currentPage + 1)}
        disabled={currentPage >= totalPages}
        className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-30 hover:bg-gray-50 disabled:cursor-not-allowed"
      >
        다음 ›
      </button>
    </div>
  );
}

function buildPageList(current: number, total: number): (number | "…")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages: (number | "…")[] = [];
  const add = (n: number) => { if (!pages.includes(n)) pages.push(n); };

  const windowStart = Math.max(2, current - 1);
  const windowEnd = Math.min(total - 1, current + 1);

  add(1);
  // "…" 대신 단 1페이지만 숨겨지는 경우엔 직접 표시
  if (windowStart === 3) add(2);
  else if (windowStart > 3) pages.push("…");
  for (let i = windowStart; i <= windowEnd; i++) add(i);
  if (windowEnd === total - 2) add(total - 1);
  else if (windowEnd < total - 2) pages.push("…");
  add(total);
  return pages;
}
