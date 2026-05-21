import { Suspense } from "react";
import { fetchAnnouncements, AnnouncementQuery } from "@/lib/api";
import AnnouncementCard from "@/components/AnnouncementCard";
import SearchBar from "@/components/SearchBar";

interface PageProps {
  searchParams: Promise<AnnouncementQuery>;
}

export default async function Home({ searchParams }: PageProps) {
  const query = await searchParams;
  const { data: announcements, total } = await fetchAnnouncements({
    ...query,
    status: (query as Record<string, string>).status ?? "open",
    size: 20,
  });

  return (
    <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">입찰 공고</h1>
          <p className="text-sm text-gray-500 mt-1">총 {total}건</p>
        </div>
        <div className="flex gap-3">
          <a href="/applications" className="text-sm text-blue-600 hover:underline">입찰 지원 →</a>
          <a href="/dashboard" className="text-sm text-gray-500 hover:underline">대시보드</a>
          <a href="/price" className="text-sm text-gray-500 hover:underline">가격 분석</a>
          <a href="/companies" className="text-sm text-gray-500 hover:underline">회사 정보</a>
          <a href="/filters" className="text-sm text-gray-500 hover:underline">알림 필터</a>
        </div>
      </div>

      <Suspense>
        <SearchBar />
      </Suspense>

      {announcements.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          조건에 맞는 공고가 없습니다.
        </div>
      ) : (
        <div className="space-y-3">
          {announcements.map((ann) => (
            <AnnouncementCard key={ann.id} ann={ann} />
          ))}
        </div>
      )}
    </main>
  );
}
