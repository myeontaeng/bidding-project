import {
  fetchDashboardSummary,
  fetchMonthlyStats,
  fetchByOrg,
  fetchByCategory,
  fetchLossAnalysis,
} from "@/lib/api";
import DashboardClient from "./DashboardClient";

export default async function DashboardPage() {
  const [summary, monthly, byOrg, byCategory, lossRecords] = await Promise.all([
    fetchDashboardSummary(),
    fetchMonthlyStats(12),
    fetchByOrg(),
    fetchByCategory(),
    fetchLossAnalysis(),
  ]);

  return (
    <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">대시보드</h1>
          <p className="text-sm text-gray-500 mt-1">입찰 실적 분석</p>
        </div>
        <div className="flex gap-3">
          <a href="/" className="text-sm text-gray-500 hover:underline">공고 목록</a>
          <a href="/applications" className="text-sm text-gray-500 hover:underline">입찰 지원</a>
          <a href="/price" className="text-sm text-gray-500 hover:underline">가격 분석</a>
        </div>
      </div>

      <DashboardClient
        summary={summary}
        monthly={monthly}
        byOrg={byOrg}
        byCategory={byCategory}
        lossRecords={lossRecords}
      />
    </main>
  );
}
