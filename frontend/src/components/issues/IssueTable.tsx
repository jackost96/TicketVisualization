import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { listIssueTypes, listStatuses } from "@/api/metadata";
import { listUsers } from "@/api/users";
import type { Issue } from "@/types/api";

interface IssueTableProps {
  issues: Issue[] | undefined;
  isLoading?: boolean;
  emptyMessage?: string;
}

export function IssueTable({ issues, isLoading, emptyMessage = "No issues found" }: IssueTableProps) {
  const navigate = useNavigate();
  const { data: statuses } = useQuery({ queryKey: ["statuses"], queryFn: listStatuses });
  const { data: issueTypes } = useQuery({ queryKey: ["issue-types"], queryFn: listIssueTypes });
  const { data: users } = useQuery({ queryKey: ["users"], queryFn: listUsers });

  const statusName = (id: number) => statuses?.find((s) => s.id === id)?.name ?? `#${id}`;
  const typeName = (id: number) => issueTypes?.find((t) => t.id === id)?.name ?? `#${id}`;
  const userName = (id: number | null) => (id ? users?.find((u) => u.id === id)?.display_name : null);

  if (isLoading) {
    return <div className="p-6 text-sm text-muted-foreground">Loading issues…</div>;
  }
  if (!issues?.length) {
    return <div className="p-6 text-sm text-muted-foreground">{emptyMessage}</div>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-28">Key</TableHead>
          <TableHead>Summary</TableHead>
          <TableHead className="w-32">Type</TableHead>
          <TableHead className="w-40">Status</TableHead>
          <TableHead className="w-40">Assignee</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {issues.map((issue) => (
          <TableRow
            key={issue.id}
            className="cursor-pointer"
            onClick={() => navigate(`/issues/${issue.key}`)}
          >
            <TableCell className="font-mono text-xs text-muted-foreground">{issue.key}</TableCell>
            <TableCell className="max-w-md truncate">{issue.summary}</TableCell>
            <TableCell>
              <Badge variant="secondary">{typeName(issue.issue_type_id)}</Badge>
            </TableCell>
            <TableCell>{statusName(issue.status_id)}</TableCell>
            <TableCell className="text-muted-foreground">
              {userName(issue.assignee_id) ?? "Unassigned"}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
