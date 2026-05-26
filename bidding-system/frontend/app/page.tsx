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
      <div>
        <h1 className="text-2xl font-bold text-gray-900">입찰 공고</h1>
        <p className="text-sm text-gray-500 mt-1">총 {total}건</p>
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
