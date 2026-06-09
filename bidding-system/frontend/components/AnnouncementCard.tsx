"use client";

import { Announcement } from "@/lib/api";
import DdayBadge from "./DdayBadge";
import BookmarkButton from "./BookmarkButton";

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

// 제목에서 도메인 키워드 추출 (DB 변경 없이 작동)
const KEYWORD_DICT: [string, string][] = [
  // IT/SW
  ["AI", "AI"], ["인공지능", "AI"], ["머신러닝", "ML"], ["딥러닝", "딥러닝"],
  ["빅데이터", "빅데이터"], ["데이터", "데이터"], ["클라우드", "클라우드"],
  ["IoT", "IoT"], ["블록체인", "블록체인"], ["메타버스", "메타버스"],
  ["디지털트윈", "디지털트윈"], ["사이버보안", "보안"], ["정보보안", "보안"],
  ["소프트웨어", "SW"], ["시스템", "시스템"], ["플랫폼", "플랫폼"],
  ["앱", "앱"], ["모바일", "모바일"], ["웹", "웹"], ["API", "API"],
  // 기술 분야
  ["반도체", "반도체"], ["배터리", "배터리"], ["이차전지", "이차전지"],
  ["수소", "수소"], ["드론", "드론"], ["로봇", "로봇"], ["자율주행", "자율주행"],
  ["우주", "우주"], ["바이오", "바이오"], ["의료", "의료"], ["헬스케어", "헬스케어"],
  ["양자", "양자컴퓨팅"], ["5G", "5G"], ["6G", "6G"],
  // 사업 유형
  ["R&D", "R&D"], ["연구개발", "R&D"], ["실증", "실증"], ["실용화", "실용화"],
  ["스마트", "스마트"], ["그린", "그린"], ["탄소중립", "탄소중립"],
  ["ESG", "ESG"], ["창업", "창업"], ["스타트업", "스타트업"],
  // 인프라
  ["네트워크", "네트워크"], ["통신", "통신"], ["위성", "위성"],
  ["전력", "전력"], ["에너지", "에너지"], ["재생에너지", "재생에너지"],
];

function extractKeywords(title: string): string[] {
  const found: string[] = [];
  for (const [term, label] of KEYWORD_DICT) {
    if (title.includes(term) && !found.includes(label)) {
      found.push(label);
    }
    if (found.length >= 4) break;
  }
  return found;
}

const TAG_COLORS = [
  "bg-blue-50 text-blue-700",
  "bg-purple-50 text-purple-700",
  "bg-teal-50 text-teal-700",
  "bg-orange-50 text-orange-700",
];

function calcProgress(startStr: string | null, deadlineStr: string | null): number | null {
  if (!startStr || !deadlineStr) return null;
  const start = new Date(startStr).getTime();
  const end = new Date(deadlineStr).getTime();
  const now = Date.now();
  if (end <= start) return null;
  return Math.min(100, Math.max(0, ((now - start) / (end - start)) * 100));
}

function progressBarColor(pct: number): string {
  if (pct >= 80) return "bg-red-400";
  if (pct >= 50) return "bg-yellow-400";
  return "bg-blue-400";
}

export default function AnnouncementCard({ ann }: Props) {
  const keywords = extractKeywords(ann.title);
  const startStr = ann.published_at ?? ann.created_at;
  const progress = calcProgress(startStr, ann.deadline);

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
            <a href={`/announcements/${ann.id}`} className="hover:text-blue-600">
              {ann.title}
            </a>
          </h3>
          <p className="text-sm text-gray-500 mt-0.5">{ann.organization}</p>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {ann.fit_score !== null && ann.fit_score !== undefined && ann.fit_score >= 60 && (
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
              ann.fit_score >= 80
                ? "bg-green-100 text-green-700"
                : "bg-yellow-100 text-yellow-700"
            }`}>
              ★ {ann.fit_score}%
            </span>
          )}
          {ann.source_url && (
            <a
              href={ann.source_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              title="나라장터 원문"
              className="text-gray-300 hover:text-blue-500 p-1 rounded"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
          )}
          <BookmarkButton ann={ann} />
          <DdayBadge dday={ann.dday} />
        </div>
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

      {progress !== null && (
        <div className="mt-3">
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>{fmtDate(startStr)}</span>
            <span className={progress >= 80 ? "text-red-500 font-medium" : ""}>
              {progress.toFixed(0)}% 경과
            </span>
            <span>{fmtDate(ann.deadline)}</span>
          </div>
          <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${progressBarColor(progress)}`}
              style={{ width: `${progress}%` }}
              suppressHydrationWarning
            />
          </div>
        </div>
      )}

      {keywords.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {keywords.map((kw, i) => (
            <span
              key={kw}
              className={`text-xs px-2 py-0.5 rounded-full font-medium ${TAG_COLORS[i % TAG_COLORS.length]}`}
            >
              {kw}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
