import { fetchApplications, fetchCompanies, fetchAnnouncements } from "@/lib/api";
import { getServerToken } from "@/lib/server-auth";
import ApplicationsClient from "./ApplicationsClient";

export default async function ApplicationsPage() {
  const token = await getServerToken();
  const [applications, companies, { data: announcements }] = await Promise.all([
    fetchApplications(token),
    fetchCompanies(token),
    fetchAnnouncements({ status: "open", size: 100 }),
  ]);

  return (
    <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">입찰 지원 관리</h1>
          <p className="text-sm text-gray-500 mt-1">공고 선택 → 서류 자동 생성 → 검토·승인 → 제출</p>
        </div>
        <a href="/" className="text-sm text-blue-600 hover:underline">← 공고 목록</a>
      </div>
      <ApplicationsClient
        initialApplications={applications}
        companies={companies}
        announcements={announcements}
      />
    </main>
  );
}
