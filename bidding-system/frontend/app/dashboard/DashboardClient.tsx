"use client";

import {
  BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell,
} from "recharts";
import { downloadExport } from "@/lib/api";
import type {
  DashboardSummary, MonthlyStats, OrgStats, CategoryStats, LossRecord,
} from "@/lib/api";

const PIE_COLORS = ["#22c55e", "#ef4444", "#94a3b8"];

function KpiCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  );
}

function fmt(n: number | null | undefined) {
  if (n == null) return "-";
  if (n >= 1_0000_0000) return `${(n / 1_0000_0000).toFixed(1)}억`;
  if (n >= 1_0000) return `${(n / 1_0000).toFixed(0)}만`;
  return n.toLocaleString();
}

export default function DashboardClient({
  summary,
  monthly,
  byOrg,
  byCategory,
  lossRecords,
}: {
  summary: DashboardSummary;
  monthly: MonthlyStats[];
  byOrg: OrgStats[];
  byCategory: CategoryStats[];
  lossRecords: LossRecord[];
}) {
  if (!summary || (summary as { detail?: string }).detail) {
    return (
      <div className="text-center py-16 text-gray-400">
        데이터를 불러올 수 없습니다.{" "}
        <a href="/login" className="text-blue-500 underline">로그인</a>이 필요합니다.
      </div>
    );
  }

  const pieData = [
    { name: "낙찰", value: summary.won ?? 0 },
    { name: "유찰", value: summary.lost ?? 0 },
    { name: "진행중", value: summary.pending ?? Math.max(0, (summary.submitted ?? 0) - (summary.won ?? 0) - (summary.lost ?? 0)) },
  ];

  return (
    <div className="space-y-8">
      {/* KPI 카드 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard label="총 입찰 건수" value={`${summary.total_applications}건`} />
        <KpiCard
          label="낙찰률"
          value={`${(summary.win_rate ?? 0).toFixed(1)}%`}
          sub={`낙찰 ${summary.won} / 유찰 ${summary.lost}`}
        />
        <KpiCard
          label="총 투찰 금액"
          value={fmt(summary.bid_amount)}
          sub="원"
        />
        <KpiCard
          label="낙찰 총액"
          value={fmt(summary.award_amount)}
          sub="원"
        />
      </div>

      {/* 월별 추이 + 낙찰률 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">월별 입찰 현황</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={monthly.map(m => ({ ...m, applications: m.submitted }))} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="won" name="낙찰" fill="#22c55e" radius={[2, 2, 0, 0]} />
              <Bar dataKey="lost" name="유찰" fill="#ef4444" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">낙찰 / 유찰 / 진행</h2>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`} labelLine={false}>
                {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 낙찰률 라인 차트 */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">월별 낙찰률 추이</h2>
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={monthly.map(m => ({ ...m, win_rate_pct: +(m.win_rate ?? 0).toFixed(1) }))} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="month" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} unit="%" domain={[0, 100]} />
            <Tooltip formatter={(v) => [`${v}%`, "낙찰률"]} />
            <Line type="monotone" dataKey="win_rate_pct" name="낙찰률" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 발주처별 / 업종별 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">발주처별 현황 (상위 10)</h2>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {byOrg.slice(0, 10).map((o) => (
              <div key={o.organization} className="flex items-center justify-between text-sm">
                <span className="text-gray-700 truncate flex-1 mr-2">{o.organization || "기타"}</span>
                <span className="text-gray-400 mr-3 shrink-0">{o.submitted}건</span>
                <span className={`shrink-0 font-medium ${(o.win_rate ?? 0) >= 50 ? "text-green-600" : "text-gray-500"}`}>
                  {(o.win_rate ?? 0).toFixed(0)}%
                </span>
              </div>
            ))}
            {byOrg.length === 0 && <p className="text-gray-400 text-sm">데이터 없음</p>}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">업종별 현황</h2>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {byCategory.map((c) => (
              <div key={c.category} className="flex items-center justify-between text-sm">
                <span className="text-gray-700 truncate flex-1 mr-2">{c.category || "기타"}</span>
                <span className="text-gray-400 mr-3 shrink-0">{c.submitted}건</span>
                <span className={`shrink-0 font-medium ${(c.win_rate ?? 0) >= 50 ? "text-green-600" : "text-gray-500"}`}>
                  {(c.win_rate ?? 0).toFixed(0)}%
                </span>
              </div>
            ))}
            {byCategory.length === 0 && <p className="text-gray-400 text-sm">데이터 없음</p>}
          </div>
        </div>
      </div>

      {/* 유찰 분석 */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">유찰 원인 분석</h2>
        {lossRecords.length === 0 ? (
          <p className="text-gray-400 text-sm">유찰 기록 없음</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-100">
                  <th className="pb-2 pr-4 font-medium">공고명</th>
                  <th className="pb-2 pr-4 font-medium">발주처</th>
                  <th className="pb-2 pr-4 font-medium text-right">투찰가</th>
                  <th className="pb-2 pr-4 font-medium text-right">낙찰가</th>
                  <th className="pb-2 pr-4 font-medium text-right">가격 차이</th>
                  <th className="pb-2 font-medium">순위</th>
                </tr>
              </thead>
              <tbody>
                {lossRecords.map((r) => (
                  <tr key={r.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2 pr-4 truncate max-w-[200px]" title={r.title}>{r.title}</td>
                    <td className="py-2 pr-4 text-gray-500 truncate max-w-[120px]">{r.organization}</td>
                    <td className="py-2 pr-4 text-right tabular-nums">
                      {r.our_bid_price ? `${r.our_bid_price.toLocaleString()}원` : "-"}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums">
                      {r.winner_price ? `${r.winner_price.toLocaleString()}원` : "-"}
                    </td>
                    <td className="py-2 pr-4 text-right tabular-nums">
                      {r.price_diff_pct != null ? (
                        <span className={r.price_diff_pct > 0 ? "text-red-500" : "text-blue-500"}>
                          {r.price_diff_pct > 0 ? "+" : ""}{r.price_diff_pct.toFixed(1)}%
                        </span>
                      ) : "-"}
                    </td>
                    <td className="py-2 text-gray-500">
                      {r.our_rank && r.total_bidders ? `${r.our_rank}/${r.total_bidders}위` : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 내보내기 */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">데이터 내보내기</h2>
        <div className="flex gap-3">
          <button
            onClick={() => downloadExport("csv")}
            className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700"
          >
            CSV 다운로드
          </button>
          <button
            onClick={() => downloadExport("excel")}
            className="px-4 py-2 bg-blue-700 text-white rounded-lg text-sm font-medium hover:bg-blue-800"
          >
            엑셀 다운로드
          </button>
        </div>
      </div>
    </div>
  );
}
