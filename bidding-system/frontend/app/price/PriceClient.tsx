"use client";

import { useState } from "react";
import {
  AwardStats, RecommendResult, SimulationResult, MarginResult,
  fetchRecommend, fetchSimulation, fetchMargin,
} from "@/lib/api";

const CATEGORIES = ["IT서비스", "소프트웨어", "건설", "용역", "물품구매", "시설공사"];
const REGIONS = ["서울", "경기", "부산", "인천", "대구", "광주", "대전", "울산", "세종"];

function fmt(v: number) {
  if (v >= 100_000_000) return `${(v / 100_000_000).toFixed(1)}억`;
  if (v >= 10_000) return `${(v / 10_000).toFixed(0)}만`;
  return v.toLocaleString();
}

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className="text-xl font-bold text-gray-900">{value}</div>
      {sub && <div className="text-xs text-gray-400 mt-0.5">{sub}</div>}
    </div>
  );
}

function WinProbBar({ prob }: { prob: number }) {
  const pct = Math.round(prob * 100);
  const color = pct >= 60 ? "bg-green-500" : pct >= 40 ? "bg-yellow-400" : "bg-red-400";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-100 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-600 w-10 text-right">{pct}%</span>
    </div>
  );
}

export default function PriceClient({ initialStats }: { initialStats: AwardStats }) {
  const stats = initialStats;

  // 입력 폼
  const [basePrice, setBasePrice] = useState("");
  const [category, setCategory] = useState("");
  const [region, setRegion] = useState("");
  const [bidCount, setBidCount] = useState("8");
  const [cost, setCost] = useState("");
  const [bidPrice, setBidPrice] = useState("");
  const [overheadRate, setOverheadRate] = useState("10");

  // 결과
  const [recommend, setRecommend] = useState<RecommendResult | null>(null);
  const [simulation, setSimulation] = useState<SimulationResult | null>(null);
  const [margin, setMargin] = useState<MarginResult | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    const bp = Number(basePrice.replace(/,/g, ""));
    if (!bp) return;
    setLoading(true);
    try {
      const [rec, sim] = await Promise.all([
        fetchRecommend({ base_price: bp, category: category || undefined, region: region || undefined, bid_count: Number(bidCount) }),
        fetchSimulation({ base_price: bp, category: category || undefined, cost: cost ? Number(cost.replace(/,/g, "")) : undefined }),
      ]);
      setRecommend(rec);
      setSimulation(sim);
      setBidPrice(String(rec.recommended_price_low));
    } finally {
      setLoading(false);
    }
  };

  const runMargin = async () => {
    const bp = Number(basePrice.replace(/,/g, ""));
    const bid = Number(bidPrice.replace(/,/g, ""));
    const c = Number(cost.replace(/,/g, ""));
    if (!bp || !bid || !c) return;
    const result = await fetchMargin({ base_price: bp, bid_price: bid, cost: c, overhead_rate: Number(overheadRate) / 100 });
    setMargin(result);
  };

  return (
    <div className="space-y-6">
      {/* 낙찰 통계 요약 */}
      {stats.count > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard label="평균 낙찰률" value={`${(stats.mean * 100).toFixed(1)}%`} sub="전체" />
          <StatCard label="중앙값" value={`${(stats.median * 100).toFixed(1)}%`} />
          <StatCard label="하위 25%" value={`${(stats.p25 * 100).toFixed(1)}%`} sub="낮은 투찰가" />
          <StatCard label="상위 75%" value={`${(stats.p75 * 100).toFixed(1)}%`} sub="높은 투찰가" />
        </div>
      )}

      {/* 입력 폼 */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
        <h2 className="font-semibold text-gray-900">투찰가 분석</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="text-sm text-gray-600 mb-1 block">예정가격 (원) *</label>
            <input
              value={basePrice}
              onChange={(e) => setBasePrice(e.target.value)}
              placeholder="예: 100000000"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="text-sm text-gray-600 mb-1 block">업종</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">전체</option>
              {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-600 mb-1 block">지역</label>
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">전체</option>
              {REGIONS.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-600 mb-1 block">예상 투찰 업체 수</label>
            <input
              type="number"
              value={bidCount}
              onChange={(e) => setBidCount(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="text-sm text-gray-600 mb-1 block">직접 원가 (선택)</label>
            <input
              value={cost}
              onChange={(e) => setCost(e.target.value)}
              placeholder="마진 계산용"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={run}
              disabled={!basePrice || loading}
              className="w-full bg-blue-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "분석 중..." : "투찰가 분석"}
            </button>
          </div>
        </div>
      </div>

      {/* 추천 결과 */}
      {recommend && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
          <h3 className="font-semibold text-blue-900 mb-3">ML 투찰가 추천</h3>
          <div className="grid grid-cols-3 gap-4">
            <StatCard
              label="예측 낙찰률"
              value={`${(recommend.predicted_rate * 100).toFixed(1)}%`}
              sub={`MAE ±${recommend.model_mae ? (recommend.model_mae * 100).toFixed(1) : "-"}%`}
            />
            <StatCard
              label="추천 하한가"
              value={fmt(recommend.recommended_price_low)}
              sub={`${(recommend.recommended_range.low * 100).toFixed(1)}%`}
            />
            <StatCard
              label="추천 상한가"
              value={fmt(recommend.recommended_price_high)}
              sub={`${(recommend.recommended_range.high * 100).toFixed(1)}%`}
            />
          </div>
          <p className="text-xs text-blue-600 mt-2">모델: {recommend.model_version}</p>
        </div>
      )}

      {/* 시뮬레이션 테이블 */}
      {simulation && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="p-4 border-b border-gray-100 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">시나리오 시뮬레이션</h3>
            <span className="text-xs text-gray-500">데이터 {simulation.data_count}건 기반</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-xs">
                  <th className="px-4 py-2 text-left">투찰율</th>
                  <th className="px-4 py-2 text-right">투찰가</th>
                  <th className="px-4 py-2 text-left w-40">낙찰 확률</th>
                  {simulation.scenarios[0]?.margin_rate !== null && (
                    <th className="px-4 py-2 text-right">마진율</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {simulation.scenarios
                  .filter((_, i) => i % 2 === 0) // 1% 단위로만 표시
                  .map((s) => {
                    const isOptimal = s.rate === simulation.optimal.rate;
                    return (
                      <tr
                        key={s.rate}
                        className={`border-t border-gray-50 ${isOptimal ? "bg-yellow-50 font-medium" : "hover:bg-gray-50"}`}
                      >
                        <td className="px-4 py-2">
                          {s.rate_pct}
                          {isOptimal && <span className="ml-2 text-xs text-yellow-600">★ 최적</span>}
                        </td>
                        <td className="px-4 py-2 text-right">{fmt(s.bid_price)}원</td>
                        <td className="px-4 py-2 w-40">
                          <WinProbBar prob={s.win_prob} />
                        </td>
                        {s.margin_rate !== null && (
                          <td className={`px-4 py-2 text-right ${s.margin_rate < 0 ? "text-red-500" : "text-green-600"}`}>
                            {s.margin_rate?.toFixed(1)}%
                          </td>
                        )}
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 마진 계산기 */}
      {recommend && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
          <h3 className="font-semibold text-gray-900">마진율 계산기</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <label className="text-sm text-gray-600 mb-1 block">투찰가</label>
              <input
                value={bidPrice}
                onChange={(e) => setBidPrice(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="text-sm text-gray-600 mb-1 block">직접 원가</label>
              <input
                value={cost}
                onChange={(e) => setCost(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="text-sm text-gray-600 mb-1 block">간접비율 (%)</label>
              <input
                type="number"
                value={overheadRate}
                onChange={(e) => setOverheadRate(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={runMargin}
                disabled={!bidPrice || !cost}
                className="w-full bg-gray-800 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-gray-900 disabled:opacity-50"
              >
                계산
              </button>
            </div>
          </div>

          {margin && (
            <div className={`rounded-lg p-4 ${margin.is_profitable ? "bg-green-50 border border-green-200" : "bg-red-50 border border-red-200"}`}>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div>
                  <div className="text-gray-500">투찰가</div>
                  <div className="font-semibold">{fmt(margin.bid_price)}원</div>
                </div>
                <div>
                  <div className="text-gray-500">총 원가</div>
                  <div className="font-semibold">{fmt(margin.total_cost)}원</div>
                </div>
                <div>
                  <div className="text-gray-500">마진</div>
                  <div className={`font-bold text-lg ${margin.is_profitable ? "text-green-700" : "text-red-600"}`}>
                    {fmt(margin.margin)}원
                  </div>
                </div>
                <div>
                  <div className="text-gray-500">마진율</div>
                  <div className={`font-bold text-lg ${margin.is_profitable ? "text-green-700" : "text-red-600"}`}>
                    {margin.margin_rate.toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
