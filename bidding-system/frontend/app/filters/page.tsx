import { fetchFilters } from "@/lib/api";
import { getServerToken } from "@/lib/server-auth";
import FiltersClient from "./FiltersClient";

export default async function FiltersPage() {
  const token = await getServerToken();
  const filters = await fetchFilters(token);
  return (
    <main className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">알림 필터 관리</h1>
          <p className="text-sm text-gray-500 mt-1">
            조건에 맞는 신규 공고 발생 시 슬랙/이메일 알림 발송
          </p>
        </div>
        <a href="/" className="text-sm text-blue-600 hover:underline">
          ← 공고 목록
        </a>
      </div>
      <FiltersClient initialFilters={filters} />
    </main>
  );
}
