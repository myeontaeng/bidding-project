import { fetchCompanies } from "@/lib/api";
import { getServerToken } from "@/lib/server-auth";
import CompaniesClient from "./CompaniesClient";

export default async function CompaniesPage() {
  const token = await getServerToken();
  const companies = await fetchCompanies(token);
  return (
    <main className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">회사 정보 관리</h1>
          <p className="text-sm text-gray-500 mt-1">사업자번호·인증서 정보는 암호화 저장됩니다</p>
        </div>
        <a href="/" className="text-sm text-blue-600 hover:underline">← 공고 목록</a>
      </div>
      <CompaniesClient initialCompanies={companies} />
    </main>
  );
}
