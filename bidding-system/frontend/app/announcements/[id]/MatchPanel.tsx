"use client";

import { useEffect, useState } from "react";
import { fetchCompanies, fetchMatchScore, type Company, type MatchResult } from "@/lib/api";

export default function MatchPanel({ annId }: { annId: number }) {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [companyId, setCompanyId] = useState<number | null>(null);
  const [result, setResult] = useState<MatchResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCompanies()
      .then((cs) => {
        if (!Array.isArray(cs)) return; // 미로그인 시 {detail: "..."} 반환 방어
        setCompanies(cs);
        if (cs.length === 1) setCompanyId(cs[0].id);
      })
      .catch(() => {});
  }, []);

  const run = async (cid: number) => {
    setLoading(true);
    setResult(null);
    try {
      const r = await fetchMatchScore(annId, cid);
      setResult(r);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (companyId) run(companyId);
  }, [companyId]);

  if (companies.length === 0) return null;

  const scoreCls =
    result == null ? "text-gray-400"
    : result.score >= 75 ? "text-green-600"
    : result.score >= 50 ? "text-yellow-600"
    : "text-red-500";

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-700">요건 충족도</h2>
        {companies.length > 1 && (
          <select
            value={companyId ?? ""}
            onChange={(e) => setCompanyId(Number(e.target.value))}
            className="text-xs border border-gray-300 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">회사 선택</option>
            {companies.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        )}
      </div>

      {loading && <p className="text-sm text-gray-400 text-center py-2">분석 중...</p>}

      {result && (
        <>
          <div className="flex items-center gap-3">
            <div className="relative w-16 h-16 shrink-0">
              <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                <circle cx="18" cy="18" r="14" fill="none" stroke="#e5e7eb" strokeWidth="4" />
                <circle
                  cx="18" cy="18" r="14" fill="none"
                  stroke={result.score >= 75 ? "#22c55e" : result.score >= 50 ? "#eab308" : "#ef4444"}
                  strokeWidth="4"
                  strokeDasharray={`${result.score * 0.879} 87.9`}
                  strokeLinecap="round"
                />
              </svg>
              <span className={`absolute inset-0 flex items-center justify-center text-sm font-bold ${scoreCls}`}>
                {result.score}%
              </span>
            </div>
            <div>
              <p className={`text-lg font-bold ${scoreCls}`}>{result.score}점</p>
              <p className="text-xs text-gray-500">{result.company_name} 기준</p>
            </div>
          </div>

          <div className="space-y-2">
            {result.checks.map((c) => (
              <div key={c.label} className="flex items-start gap-2.5">
                <span className={`shrink-0 mt-0.5 text-sm ${
                  c.unknown ? "text-gray-300" : c.pass ? "text-green-500" : "text-red-400"
                }`}>
                  {c.unknown ? "?" : c.pass ? "✓" : "✗"}
                </span>
                <div className="flex-1">
                  <span className="text-sm font-medium text-gray-700">{c.label}</span>
                  <span className="ml-2 text-xs text-gray-400">{c.detail}</span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {!loading && !result && companyId && (
        <p className="text-xs text-gray-400 text-center py-2">분석 결과를 불러오는 중...</p>
      )}
    </div>
  );
}
