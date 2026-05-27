"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

const CATEGORIES = ["전자입찰", "전자시담", "직찰", "용역", "물품", "공사", "건설공사", "IT서비스", "시설관리"];
const REGIONS = ["서울", "경기", "부산", "인천", "대전", "광주", "울산", "세종", "강원", "충북", "충남", "경남", "경북", "전남", "전북", "제주", "전국"];

function addDays(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

export default function SearchBar() {
  const router = useRouter();
  const params = useSearchParams();
  const [keyword, setKeyword] = useState(params.get("keyword") ?? "");
  const [category, setCategory] = useState(params.get("category") ?? "");
  const [region, setRegion] = useState(params.get("region") ?? "");
  const [org, setOrg] = useState(params.get("organization") ?? "");
  const [budgetMin, setBudgetMin] = useState(params.get("budget_min") ?? "");
  const [budgetMax, setBudgetMax] = useState(params.get("budget_max") ?? "");
  const [status, setStatus] = useState(params.get("status") ?? "open");
  const [ddayWithin, setDdayWithin] = useState(params.get("dday_within") ?? "");
  const [sortBy, setSortBy] = useState(params.get("sort_by") ?? "deadline");

  const search = () => {
    const p = new URLSearchParams();
    if (keyword) p.set("keyword", keyword);
    if (category) p.set("category", category);
    if (region) p.set("region", region);
    if (org) p.set("organization", org);
    if (budgetMin) p.set("budget_min", budgetMin);
    if (budgetMax) p.set("budget_max", budgetMax);
    if (status) p.set("status", status);
    if (ddayWithin) {
      p.set("deadline_before", addDays(parseInt(ddayWithin)));
      p.set("dday_within", ddayWithin);
    }
    if (sortBy && sortBy !== "deadline") p.set("sort_by", sortBy);
    router.push(`/?${p}`);
  };

  const reset = () => {
    setKeyword(""); setCategory(""); setRegion(""); setOrg("");
    setBudgetMin(""); setBudgetMax(""); setStatus("open"); setDdayWithin(""); setSortBy("deadline");
    router.push("/");
  };

  const selectCls = "border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500";
  const inputCls = "border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500";

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
      {/* 키워드 + 정렬 + 버튼 */}
      <div className="flex gap-2">
        <input
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
          placeholder="키워드 검색 (제목, 발주처)"
          className={`flex-1 ${inputCls}`}
        />
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className={selectCls}
        >
          <option value="deadline">마감 임박순</option>
          <option value="published_at">최신 등록순</option>
          <option value="budget_desc">예산 큰순</option>
          <option value="budget_asc">예산 작은순</option>
        </select>
        <button
          onClick={search}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          검색
        </button>
        <button
          onClick={reset}
          className="border border-gray-300 text-gray-600 px-3 py-2 rounded-lg text-sm hover:bg-gray-50"
        >
          초기화
        </button>
      </div>

      {/* 필터 행 1: 상태 / 업종 / 지역 / 발주처 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <select value={status} onChange={(e) => setStatus(e.target.value)} className={selectCls}>
          <option value="open">진행중 (마감일 유효)</option>
          <option value="imminent">마감임박 (D-7 이내)</option>
          <option value="no_deadline">기간정보없음</option>
          <option value="expired">마감됨</option>
          <option value="closed">종료 (공식)</option>
          <option value="">전체</option>
        </select>

        <select value={category} onChange={(e) => setCategory(e.target.value)} className={selectCls}>
          <option value="">업종 전체</option>
          {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>

        <select value={region} onChange={(e) => setRegion(e.target.value)} className={selectCls}>
          <option value="">지역 전체</option>
          {REGIONS.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>

        <input
          value={org}
          onChange={(e) => setOrg(e.target.value)}
          placeholder="발주처"
          className={inputCls}
        />
      </div>

      {/* 필터 행 2: 마감 D-day / 예산 범위 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <select value={ddayWithin} onChange={(e) => setDdayWithin(e.target.value)} className={selectCls}>
          <option value="">마감 기한 전체</option>
          <option value="0">오늘 마감 (D-0)</option>
          <option value="3">3일 이내 (D-3)</option>
          <option value="7">7일 이내 (D-7)</option>
          <option value="30">30일 이내 (D-30)</option>
        </select>

        <div className="col-span-1 md:col-span-2 flex gap-1 items-center">
          <input
            value={budgetMin}
            onChange={(e) => setBudgetMin(e.target.value)}
            placeholder="예산 최소 (원)"
            type="number"
            className={`flex-1 ${inputCls}`}
          />
          <span className="text-gray-400 text-sm shrink-0">~</span>
          <input
            value={budgetMax}
            onChange={(e) => setBudgetMax(e.target.value)}
            placeholder="최대"
            type="number"
            className={`flex-1 ${inputCls}`}
          />
        </div>

        <div className="hidden md:block" />
      </div>
    </div>
  );
}
