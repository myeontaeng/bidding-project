import { Suspense } from "react";
import { fetchAnnouncements, fetchTodayOverview, fetchArchiveStats, fetchCuratedCollections, AnnouncementQuery } from "@/lib/api";
import AnnouncementCard from "@/components/AnnouncementCard";
import SearchBar from "@/components/SearchBar";
import Pagination from "@/components/Pagination";
import CuratedCollections from "@/components/CuratedCollections";

const PAGE_SIZE = 20;

interface PageProps {
  searchParams: Promise<AnnouncementQuery & { page?: string }>;
}

export default async function Home({ searchParams }: PageProps) {
  const query = await searchParams;
  const page = Math.max(1, parseInt(String(query.page ?? "1"), 10));

  const [{ data: announcements, total }, overview, archiveStats, collections] = await Promise.all([
    fetchAnnouncements({
      ...query,
      status: (query as Record<string, string>).status ?? "open",
      page,
      size: PAGE_SIZE,
    }),
    fetchTodayOverview().catch(() => null),
    fetchArchiveStats().catch(() => null),
    fetchCuratedCollections().catch(() => []),
  ]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">입찰 공고</h1>
        <p className="text-sm text-gray-500 mt-1">
          총 {total.toLocaleString()}건
          {totalPages > 1 && ` · ${page} / ${totalPages} 페이지`}
        </p>
      </div>

      {overview && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-blue-50 rounded-xl p-3 text-center">
            <p className="text-xl font-bold text-blue-700">{overview.total_open.toLocaleString()}</p>
            <p className="text-xs text-blue-500 mt-0.5">진행중 공고</p>
          </div>
          <div className={`rounded-xl p-3 text-center ${overview.closing_today > 0 ? "bg-red-50" : "bg-gray-50"}`}>
            <p className={`text-xl font-bold ${overview.closing_today > 0 ? "text-red-600" : "text-gray-400"}`}>
              {overview.closing_today}
            </p>
            <p className={`text-xs mt-0.5 ${overview.closing_today > 0 ? "text-red-400" : "text-gray-400"}`}>오늘 마감</p>
          </div>
          <div className={`rounded-xl p-3 text-center ${overview.closing_this_week > 0 ? "bg-amber-50" : "bg-gray-50"}`}>
            <p className={`text-xl font-bold ${overview.closing_this_week > 0 ? "text-amber-600" : "text-gray-400"}`}>
              {overview.closing_this_week}
            </p>
            <p className={`text-xs mt-0.5 ${overview.closing_this_week > 0 ? "text-amber-500" : "text-gray-400"}`}>이번 주 마감</p>
          </div>
          <div className={`rounded-xl p-3 text-center ${overview.pending_applications > 0 ? "bg-purple-50" : "bg-gray-50"}`}>
            <p className={`text-xl font-bold ${overview.pending_applications > 0 ? "text-purple-700" : "text-gray-400"}`}>
              {overview.pending_applications}
            </p>
            <p className={`text-xs mt-0.5 ${overview.pending_applications > 0 ? "text-purple-500" : "text-gray-400"}`}>결과 대기중</p>
          </div>
        </div>
      )}

      {/* 아카이브 지표 */}
      {archiveStats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 py-3 border-y border-gray-100">
          <div className="text-center">
            <p className="text-xl font-bold text-gray-900">{archiveStats.total_announcements.toLocaleString()}</p>
            <p className="text-xs text-gray-400 mt-0.5">수집 공고</p>
          </div>
          <div className="text-center">
            <p className="text-xl font-bold text-gray-900">{archiveStats.total_award_records.toLocaleString()}</p>
            <p className="text-xs text-gray-400 mt-0.5">낙찰 이력</p>
          </div>
          <div className="text-center">
            <p className="text-xl font-bold text-gray-900">
              {archiveStats.avg_award_rate != null ? `${archiveStats.avg_award_rate}%` : "-"}
            </p>
            <p className="text-xs text-gray-400 mt-0.5">평균 낙찰률</p>
          </div>
          <div className="text-center">
            <p className="text-xl font-bold text-gray-900">
              {archiveStats.our_win_rate != null ? `${archiveStats.our_win_rate}%` : "-"}
            </p>
            <p className="text-xs text-gray-400 mt-0.5">우리 낙찰률</p>
          </div>
        </div>
      )}

      {/* 큐레이션 컬렉션 */}
      {collections.length > 0 && <CuratedCollections collections={collections} />}

      <Suspense>
        <SearchBar />
      </Suspense>

      {announcements.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          조건에 맞는 공고가 없습니다.
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {announcements.map((ann) => (
              <AnnouncementCard key={ann.id} ann={ann} />
            ))}
          </div>
          {totalPages > 1 && (
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              query={query as Record<string, string | number | undefined>}
            />
          )}
        </>
      )}
    </main>
  );
}
