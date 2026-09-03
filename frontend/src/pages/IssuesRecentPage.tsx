import { useQuery } from "@tanstack/react-query";
import { IssueTable } from "@/components/issues/IssueTable";
import { getIssue } from "@/api/issues";
import { useRecentlyViewed } from "@/hooks/useRecentlyViewed";
import type { Issue } from "@/types/api";

export function IssuesRecentPage() {
  const { recentKeys } = useRecentlyViewed();

  const { data: issues, isLoading } = useQuery({
    queryKey: ["issues", "recent", recentKeys],
    queryFn: async () => {
      const results = await Promise.allSettled(recentKeys.map((key) => getIssue(key)));
      return results
        .filter((r): r is PromiseFulfilledResult<Issue> => r.status === "fulfilled")
        .map((r) => r.value);
    },
    enabled: recentKeys.length > 0,
  });

  return (
    <div className="mx-auto max-w-5xl p-6">
      <h1 className="mb-4 text-xl font-semibold">Recently viewed</h1>
      <div className="rounded-lg border bg-background">
        <IssueTable
          issues={recentKeys.length ? issues : []}
          isLoading={isLoading}
          emptyMessage="You haven't viewed any issues yet"
        />
      </div>
    </div>
  );
}
