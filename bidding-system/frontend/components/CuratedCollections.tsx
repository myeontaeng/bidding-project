import Link from "next/link";
import type { CuratedCollection } from "@/lib/api";

function fmtBudget(v: number | null) {
  if (!v) return null;
  if (v >= 1_0000_0000) return `${(v / 1_0000_0000).toFixed(1)}억`;
  if (v >= 1_0000) return `${(v / 1_0000).toFixed(0)}만`;
  return v.toLocaleString();
}

function DdayBadge({ dday }: { dday: number | null }) {
  if (dday === null) return null;
  if (dday < 0) return <span className="text-xs text-gray-400">마감</span>;
  if (dday === 0) return <span className="text-xs font-bold text-red-600">D-Day</span>;
  const cls = dday <= 3 ? "text-red-600" : dday <= 7 ? "text-amber-600" : "text-blue-600";
  return <span className={`text-xs font-semibold ${cls}`}>D-{dday}</span>;
}

function CollectionCard({ col }: { col: CuratedCollection }) {
  if (col.items.length === 0) return null;
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-3">
      <div>
        <div className="flex items-center gap-2">
          <span className="text-lg">{col.icon}</span>
          <h3 className="text-sm font-semibold text-gray-800">{col.label}</h3>
        </div>
        <p className="text-xs text-gray-400 mt-0.5 ml-7">{col.description}</p>
      </div>
      <div className="space-y-2">
        {col.items.map((item) => (
          <Link
            key={item.id}
            href={`/announcements/${item.id}`}
            className="flex items-start justify-between gap-3 py-2 border-b border-gray-50 last:border-0 hover:bg-gray-50 -mx-2 px-2 rounded-lg transition-colors"
          >
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-800 truncate leading-snug">{item.title}</p>
              <p className="text-xs text-gray-400 truncate mt-0.5">{item.organization}</p>
            </div>
            <div className="shrink-0 text-right space-y-0.5">
              <DdayBadge dday={item.dday} />
              {item.budget && (
                <p className="text-xs text-gray-500 tabular-nums">{fmtBudget(item.budget)}원</p>
              )}
            </div>
          </Link>
        ))}
      </div>
      {col.key !== "imminent" && (
        <Link
          href={`/?status=open${col.key === "small_scale" ? "&budget_max=300000000" : ""}`}
          className="block text-xs text-blue-600 hover:underline text-right"
        >
          더보기 →
        </Link>
      )}
    </div>
  );
}

export default function CuratedCollections({ collections }: { collections: CuratedCollection[] }) {
  const visible = collections.filter((c) => c.items.length > 0);
  if (visible.length === 0) return null;

  return (
    <div>
      <h2 className="text-sm font-semibold text-gray-600 mb-3">큐레이션 컬렉션</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {visible.map((col) => (
          <CollectionCard key={col.key} col={col} />
        ))}
      </div>
    </div>
  );
}
