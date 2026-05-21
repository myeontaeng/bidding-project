import { Announcement } from "@/lib/api";
import DdayBadge from "./DdayBadge";

interface Props {
  ann: Announcement;
}

function fmtBudget(v: number | null) {
  if (!v) return "-";
  if (v >= 100_000_000) return `${(v / 100_000_000).toFixed(1)}억원`;
  if (v >= 10_000) return `${(v / 10_000).toFixed(0)}만원`;
  return `${v.toLocaleString()}원`;
}

function fmtDate(s: string | null) {
  if (!s) return "-";
  return new Date(s).toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

export default function AnnouncementCard({ ann }: Props) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            {ann.category && (
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                {ann.category}
              </span>
            )}
            {ann.region && (
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                {ann.region}
              </span>
            )}
          </div>
          <h3 className="font-semibold text-gray-900 truncate">
            {ann.source_url ? (
              <a
                href={ann.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-blue-600"
              >
                {ann.title}
              </a>
            ) : (
              ann.title
            )}
          </h3>
          <p className="text-sm text-gray-500 mt-0.5">{ann.organization}</p>
        </div>
        <DdayBadge dday={ann.dday} />
      </div>

      <div className="mt-3 flex items-center gap-4 text-sm text-gray-600">
        <span>
          <span className="text-gray-400">예산 </span>
          <span className="font-medium">{fmtBudget(ann.budget)}</span>
        </span>
        <span>
          <span className="text-gray-400">마감 </span>
          <span className="font-medium">{fmtDate(ann.deadline)}</span>
        </span>
        <span className="text-xs text-gray-400 ml-auto">
          공고번호: {ann.bid_number}
        </span>
      </div>
    </div>
  );
}
