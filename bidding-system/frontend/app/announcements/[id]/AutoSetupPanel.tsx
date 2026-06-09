"use client";

import { useState } from "react";
import { fetchAutoSetup, type AutoSetup } from "@/lib/api";

const DOC_LABELS: Record<string, string> = {
  bid_application: "입찰참가신청서",
  proposal: "제안서",
  price_breakdown: "가격산출내역서",
  company_profile: "회사소개서",
  cert_capability: "역량확인서",
};

function fmtPrice(v: number) {
  if (v >= 1_0000_0000) return `${(v / 1_0000_0000).toFixed(1)}억원`;
  if (v >= 1_0000) return `${(v / 1_0000).toFixed(0)}만원`;
  return v.toLocaleString() + "원";
}

export default function AutoSetupPanel({ annId }: { annId: number }) {
  const [data, setData] = useState<AutoSetup | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchAutoSetup(annId);
      setData(result);
    } catch {
      setError("로그인 후 이용 가능합니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-blue-900">원클릭 자동 분석</h2>
          <p className="text-xs text-blue-600 mt-0.5">요약 · 가격 추천 · 필요 서류 · 입찰 판단 한 번에</p>
        </div>
        {!data && (
          <button
            onClick={run}
            disabled={loading}
            className="bg-blue-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? "분석 중..." : "⚡ 자동 분석 시작"}
          </button>
        )}
        {data && (
          <button
            onClick={run}
            disabled={loading}
            className="text-xs text-blue-500 hover:underline"
          >
            {loading ? "..." : "다시 분석"}
          </button>
        )}
      </div>

      {error && <p className="text-xs text-red-500">{error}</p>}

      {data && (
        <div className="space-y-4">
          {/* 전문가 검토 플래그 */}
          {data.bid_score.needs_expert_review && (
            <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-lg p-3">
              <span className="text-amber-500 shrink-0">⚠️</span>
              <div>
                <p className="text-xs font-semibold text-amber-800">전문가 검토 권장</p>
                <p className="text-xs text-amber-700 mt-0.5">{data.bid_score.expert_review_reason}</p>
              </div>
            </div>
          )}

          {/* 요약 */}
          {data.summary && (
            <div>
              <p className="text-xs font-semibold text-gray-600 mb-1">AI 요약</p>
              <p className="text-sm text-gray-700 leading-relaxed bg-white rounded-lg p-3 border border-gray-100">
                {data.summary}
              </p>
            </div>
          )}

          {/* 입찰 판단 */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-white rounded-lg p-3 border border-gray-100">
              <p className="text-xs text-gray-400">입찰 판단</p>
              <p className={`text-sm font-bold mt-0.5 ${
                data.bid_score.recommendation === "bid" ? "text-green-600"
                : data.bid_score.recommendation === "caution" ? "text-amber-600"
                : "text-red-500"
              }`}>
                {data.bid_score.recommendation_label}
              </p>
              <p className="text-xs text-gray-400 mt-0.5">{data.bid_score.overall}/100점</p>
            </div>

            {/* 가격 추천 */}
            {data.price_recommendation && (
              <div className="bg-white rounded-lg p-3 border border-gray-100">
                <p className="text-xs text-gray-400">추천 투찰가</p>
                <p className="text-sm font-bold text-gray-800 mt-0.5">
                  {fmtPrice(data.price_recommendation.recommended_price_low)}
                  <span className="text-xs font-normal text-gray-400"> ~</span>
                </p>
                <p className="text-xs text-gray-500">
                  {fmtPrice(data.price_recommendation.recommended_price_high)}
                </p>
              </div>
            )}
          </div>

          {/* 필요 서류 */}
          {data.required_docs.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-600 mb-1.5">필요 서류 ({data.required_docs.length}종)</p>
              <div className="flex flex-wrap gap-1.5">
                {data.required_docs.map((doc) => (
                  <span
                    key={doc}
                    className="text-xs bg-white border border-gray-200 text-gray-700 px-2.5 py-1 rounded-full"
                  >
                    {DOC_LABELS[doc] ?? doc}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 이유 */}
          {data.bid_score.reasoning.length > 0 && (
            <ul className="space-y-1">
              {data.bid_score.reasoning.map((r, i) => (
                <li key={i} className="text-xs text-gray-500 flex gap-1.5">
                  <span className="text-gray-300">•</span>{r}
                </li>
              ))}
            </ul>
          )}

          <a
            href="/applications"
            className="block w-full text-center bg-blue-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            입찰 지원 시작 →
          </a>
        </div>
      )}
    </div>
  );
}
