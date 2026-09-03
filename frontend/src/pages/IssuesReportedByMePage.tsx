import { useQuery } from "@tanstack/react-query";
import { IssueTable } from "@/components/issues/IssueTable";
import { listIssues } from "@/api/issues";
import { useAuth } from "@/auth/AuthContext";

export function IssuesReportedByMePage() {
  const { user } = useAuth();

  const { data: issues, isLoading } = useQuery({
    queryKey: ["issues", "reported-by-me", user?.id],
    queryFn: () => listIssues({ reporter_id: user!.id, limit: 100 }),
    enabled: Boolean(user),
  });

  return (
    <div className="mx-auto max-w-5xl p-6">
      <h1 className="mb-4 text-xl font-semibold">Reported by me</h1>
      <div className="rounded-lg border bg-background">
        <IssueTable issues={issues} isLoading={isLoading} emptyMessage="You haven't reported any issues yet" />
      </div>
    </div>
  );
}
