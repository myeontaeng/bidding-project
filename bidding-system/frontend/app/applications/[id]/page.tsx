import { fetchApplication, fetchCompanies, fetchAnnouncements } from "@/lib/api";
import { getServerToken } from "@/lib/server-auth";
import ApplicationDetailClient from "./ApplicationDetailClient";

export default async function ApplicationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const token = await getServerToken();
  const [app, companies, { data: announcements }] = await Promise.all([
    fetchApplication(Number(id), token),
    fetchCompanies(token),
    fetchAnnouncements({ size: 100 }),
  ]);

  const ann = announcements.find((a) => a.id === app.announcement_id);
  const company = companies.find((c) => c.id === app.company_id);

  return (
    <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 truncate max-w-xl">
            {ann?.title ?? `지원 #${app.id}`}
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {company?.name} · {ann?.organization}
          </p>
        </div>
        <a href="/applications" className="text-sm text-blue-600 hover:underline">
          ← 목록
        </a>
      </div>
      <ApplicationDetailClient app={app} />
    </main>
  );
}
