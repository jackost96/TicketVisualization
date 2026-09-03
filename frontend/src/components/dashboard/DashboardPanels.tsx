import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getMyIssues } from "@/api/issues";
import { getStatusCounts } from "@/api/dashboards";
import { useRecentlyViewed } from "@/hooks/useRecentlyViewed";
import { getIssue } from "@/api/issues";
import type { Issue } from "@/types/api";

function CompactIssueList({ issues, emptyMessage }: { issues: Issue[] | undefined; emptyMessage: string }) {
  if (!issues?.length) {
    return <p className="text-sm text-muted-foreground">{emptyMessage}</p>;
  }
  return (
    <ul className="flex flex-col gap-2">
      {issues.map((issue) => (
        <li key={issue.id}>
          <Link
            to={`/issues/${issue.key}`}
            className="flex items-center gap-2 rounded px-1.5 py-1 text-sm hover:bg-accent"
          >
            <span className="font-mono text-xs text-muted-foreground">{issue.key}</span>
            <span className="truncate">{issue.summary}</span>
          </Link>
        </li>
      ))}
    </ul>
  );
}

function statusColor(category: string): string {
  if (category === "done") return "bg-emerald-500";
  if (category === "in_progress") return "bg-blue-500";
  return "bg-zinc-400";
}

export function DashboardPanels() {
  const { recentKeys } = useRecentlyViewed();

  const { data: myOpenIssues, isLoading: myOpenLoading } = useQuery({
    queryKey: ["issues", "mine", "open"],
    queryFn: () => getMyIssues({ open_only: true, limit: 10 }),
  });

  const { data: recentIssues, isLoading: recentLoading } = useQuery({
    queryKey: ["issues", "recent", recentKeys.slice(0, 10)],
    queryFn: async () => {
      const results = await Promise.allSettled(recentKeys.slice(0, 10).map((key) => getIssue(key)));
      return results
        .filter((r): r is PromiseFulfilledResult<Issue> => r.status === "fulfilled")
        .map((r) => r.value);
    },
    enabled: recentKeys.length > 0,
  });

  const { data: statusCounts, isLoading: countsLoading } = useQuery({
    queryKey: ["dashboard", "status-counts"],
    queryFn: getStatusCounts,
  });

  const maxCount = Math.max(1, ...(statusCounts ?? []).map((s) => s.count));

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Assigned to me (open)</CardTitle>
        </CardHeader>
        <CardContent>
          {myOpenLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : (
            <CompactIssueList issues={myOpenIssues} emptyMessage="Nothing assigned to you right now" />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recently viewed</CardTitle>
        </CardHeader>
        <CardContent>
          {recentLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : (
            <CompactIssueList
              issues={recentKeys.length ? recentIssues : []}
              emptyMessage="You haven't viewed any issues yet"
            />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Issues by status</CardTitle>
        </CardHeader>
        <CardContent>
          {countsLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : !statusCounts?.length ? (
            <p className="text-sm text-muted-foreground">No issues in your projects yet</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {statusCounts.map((row) => (
                <li key={row.status_id} className="flex items-center gap-2 text-sm">
                  <span className="w-32 truncate">{row.status_name}</span>
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                    <div
                      className={`h-full ${statusColor(row.category)}`}
                      style={{ width: `${(row.count / maxCount) * 100}%` }}
                    />
                  </div>
                  <span className="w-6 text-right text-muted-foreground">{row.count}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
