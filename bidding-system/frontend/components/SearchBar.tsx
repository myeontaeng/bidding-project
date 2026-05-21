"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

export default function SearchBar() {
  const router = useRouter();
  const params = useSearchParams();
  const [keyword, setKeyword] = useState(params.get("keyword") ?? "");
  const [category, setCategory] = useState(params.get("category") ?? "");
  const [region, setRegion] = useState(params.get("region") ?? "");
  const [org, setOrg] = useState(params.get("organization") ?? "");
  const [budgetMin, setBudgetMin] = useState(params.get("budget_min") ?? "");
  const [budgetMax, setBudgetMax] = useState(params.get("budget_max") ?? "");

  const search = () => {
    const p = new URLSearchParams();
    if (keyword) p.set("keyword", keyword);
    if (category) p.set("category", category);
    if (region) p.set("region", region);
    if (org) p.set("organization", org);
    if (budgetMin) p.set("budget_min", budgetMin);
    if (budgetMax) p.set("budget_max", budgetMax);
    router.push(`/?${p}`);
  };

  const reset = () => {
    setKeyword(""); setCategory(""); setRegion(""); setOrg("");
    setBudgetMin(""); setBudgetMax("");
    router.push("/");
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
      <div className="flex gap-2">
        <input
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
          placeholder="키워드 검색 (제목, 발주처)"
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
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

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <input
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          placeholder="업종"
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          value={region}
          onChange={(e) => setRegion(e.target.value)}
          placeholder="지역"
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          value={org}
          onChange={(e) => setOrg(e.target.value)}
          placeholder="발주처"
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <div className="flex gap-1">
          <input
            value={budgetMin}
            onChange={(e) => setBudgetMin(e.target.value)}
            placeholder="예산 최소"
            type="number"
            className="w-1/2 border border-gray-300 rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            value={budgetMax}
            onChange={(e) => setBudgetMax(e.target.value)}
            placeholder="최대"
            type="number"
            className="w-1/2 border border-gray-300 rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
    </div>
  );
}
