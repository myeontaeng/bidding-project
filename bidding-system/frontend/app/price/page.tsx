import { fetchAwardStats } from "@/lib/api";
import PriceClient from "./PriceClient";

export default async function PricePage() {
  const stats = await fetchAwardStats();
  return (
    <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">가격 분석 · 투찰가 추천</h1>
          <p className="text-sm text-gray-500 mt-1">
            {stats.count > 0
              ? `낙찰 이력 ${stats.count.toLocaleString()}건 기반 LightGBM 모델`
              : "낙찰 이력 데이터 없음 — /price/collect 실행 필요"}
          </p>
        </div>
        <a href="/" className="text-sm text-blue-600 hover:underline">← 공고 목록</a>
      </div>
      <PriceClient initialStats={stats} />
    </main>
  );
}
