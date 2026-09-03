import { useQuery } from "@tanstack/react-query";
import { IssueTable } from "@/components/issues/IssueTable";
import { getMyIssues } from "@/api/issues";

export function IssuesMyOpenPage() {
  const { data: issues, isLoading } = useQuery({
    queryKey: ["issues", "mine", "open"],
    queryFn: () => getMyIssues({ open_only: true, limit: 100 }),
  });

  return (
    <div className="mx-auto max-w-5xl p-6">
      <h1 className="mb-4 text-xl font-semibold">My open issues</h1>
      <div className="rounded-lg border bg-background">
        <IssueTable issues={issues} isLoading={isLoading} emptyMessage="Nothing assigned to you right now" />
      </div>
    </div>
  );
}
