"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

const CATEGORIES = [
  "IT서비스", "IT장비",
  "시설공사", "건축공사", "토목공사", "전기·통신공사", "건설공사",
  "물품구매",
  "용역", "연구용역", "교육·컨설팅", "시설관리",
];

const BID_METHODS = ["전자입찰", "직찰", "전자시담", "수의계약"];

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
  const [supportType, setSupportType] = useState(params.get("support_type") ?? "");
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
    if (supportType) p.set("support_type", supportType);
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
    setKeyword(""); setCategory(""); setSupportType(""); setRegion(""); setOrg("");
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

      {/* 필터 행 1: 상태 / 업종 / 입찰방법 / 지역 */}
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
          <optgroup label="IT / SW">
            <option value="IT서비스">IT서비스</option>
          </optgroup>
          <optgroup label="공사">
            <option value="시설공사">시설공사</option>
            <option value="건축공사">건축공사</option>
            <option value="토목공사">토목공사</option>
            <option value="전기·통신공사">전기·통신공사</option>
            <option value="건설공사">건설공사</option>
          </optgroup>
          <optgroup label="물품">
            <option value="IT장비">IT장비</option>
            <option value="의료기기">의료기기</option>
            <option value="차량·장비">차량·장비</option>
            <option value="식품·식자재">식품·식자재</option>
            <option value="가구·비품">가구·비품</option>
            <option value="소방·안전장비">소방·안전장비</option>
            <option value="사무용품">사무용품</option>
            <option value="물품구매">기타 물품구매</option>
          </optgroup>
          <optgroup label="용역">
            <option value="용역">용역</option>
            <option value="연구용역">연구용역</option>
            <option value="교육·컨설팅">교육·컨설팅</option>
            <option value="시설관리">시설관리</option>
          </optgroup>
        </select>

        <select value={supportType} onChange={(e) => setSupportType(e.target.value)} className={selectCls}>
          <option value="">입찰방법 전체</option>
          {BID_METHODS.map((m) => <option key={m} value={m}>{m}</option>)}
        </select>

        <select value={region} onChange={(e) => setRegion(e.target.value)} className={selectCls}>
          <option value="">지역 전체</option>
          {REGIONS.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
      </div>

      {/* 필터 행 2: 발주처 / 마감 / 예산 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <input
          value={org}
          onChange={(e) => setOrg(e.target.value)}
          placeholder="발주처"
          className={inputCls}
        />

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
      </div>
    </div>
  );
}
