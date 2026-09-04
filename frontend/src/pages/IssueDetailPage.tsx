import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  createComment,
  createLink,
  doTransition,
  getHistory,
  getIssue,
  getTransitions,
  listComments,
  listLinks,
} from "@/api/issues";
import { listIssueLinkTypes, listIssueTypes, listPriorities, listStatuses } from "@/api/metadata";
import { listUsers } from "@/api/users";
import { useRecentlyViewed } from "@/hooks/useRecentlyViewed";
import { getErrorMessage } from "@/api/client";

export function IssueDetailPage() {
  const { key } = useParams<{ key: string }>();
  const queryClient = useQueryClient();
  const { markViewed } = useRecentlyViewed();
  const [commentBody, setCommentBody] = useState("");
  const [transitionError, setTransitionError] = useState<string | null>(null);
  const [linkTypeId, setLinkTypeId] = useState("");
  const [targetKey, setTargetKey] = useState("");

  useEffect(() => {
    if (key) markViewed(key);
  }, [key, markViewed]);

  const { data: issue } = useQuery({ queryKey: ["issue", key], queryFn: () => getIssue(key!), enabled: Boolean(key) });
  const { data: transitions } = useQuery({
    queryKey: ["issue-transitions", key],
    queryFn: () => getTransitions(key!),
    enabled: Boolean(key),
  });
  const { data: history } = useQuery({ queryKey: ["issue-history", key], queryFn: () => getHistory(key!), enabled: Boolean(key) });
  const { data: comments } = useQuery({ queryKey: ["issue-comments", key], queryFn: () => listComments(key!), enabled: Boolean(key) });
  const { data: links } = useQuery({ queryKey: ["issue-links", key], queryFn: () => listLinks(key!), enabled: Boolean(key) });
  const { data: statuses } = useQuery({ queryKey: ["statuses"], queryFn: listStatuses });
  const { data: issueTypes } = useQuery({ queryKey: ["issue-types"], queryFn: listIssueTypes });
  const { data: users } = useQuery({ queryKey: ["users"], queryFn: listUsers });
  const { data: priorities } = useQuery({ queryKey: ["priorities"], queryFn: listPriorities });
  const { data: linkTypes } = useQuery({ queryKey: ["issue-link-types"], queryFn: listIssueLinkTypes });

  const transitionMutation = useMutation({
    mutationFn: (transitionId: number) => doTransition(key!, transitionId),
    onSuccess: async () => {
      setTransitionError(null);
      await queryClient.invalidateQueries({ queryKey: ["issue", key] });
      await queryClient.invalidateQueries({ queryKey: ["issue-transitions", key] });
      await queryClient.invalidateQueries({ queryKey: ["issue-history", key] });
    },
    onError: (err) => setTransitionError(getErrorMessage(err, "Transition failed")),
  });

  const commentMutation = useMutation({
    mutationFn: () => createComment(key!, commentBody),
    onSuccess: async () => {
      setCommentBody("");
      await queryClient.invalidateQueries({ queryKey: ["issue-comments", key] });
    },
  });

  const linkMutation = useMutation({
    mutationFn: () =>
      createLink(key!, { link_type_id: Number(linkTypeId), target_key: targetKey, direction: "outward" }),
    onSuccess: async () => {
      setLinkTypeId("");
      setTargetKey("");
      await queryClient.invalidateQueries({ queryKey: ["issue-links", key] });
    },
  });

  if (!issue) {
    return <div className="p-6 text-sm text-muted-foreground">Loading issue…</div>;
  }

  const statusName = statuses?.find((s) => s.id === issue.status_id)?.name ?? `#${issue.status_id}`;
  const typeName = issueTypes?.find((t) => t.id === issue.issue_type_id)?.name ?? `#${issue.issue_type_id}`;
  const assigneeName = users?.find((u) => u.id === issue.assignee_id)?.display_name;
  const reporterName = users?.find((u) => u.id === issue.reporter_id)?.display_name;
  const priorityName = priorities?.find((p) => p.id === issue.priority_id)?.name;

  return (
    <div className="mx-auto max-w-3xl p-6">
      <div className="mb-1 flex items-center gap-2 text-sm text-muted-foreground">
        <span className="font-mono">{issue.key}</span>
        <Badge variant="secondary">{typeName}</Badge>
        <Badge>{statusName}</Badge>
      </div>
      <h1 className="mb-4 text-xl font-semibold">{issue.summary}</h1>

      <div className="mb-6 flex flex-wrap items-center gap-2">
        {transitions?.map((t) => (
          <Button key={t.id} size="sm" variant="outline" onClick={() => transitionMutation.mutate(t.id)}>
            {t.name}
          </Button>
        ))}
      </div>
      {transitionError && <p className="mb-4 text-sm text-destructive">{transitionError}</p>}

      {issue.description && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-base">Description</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm whitespace-pre-wrap">{issue.description}</p>
          </CardContent>
        </Card>
      )}

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">Details</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-muted-foreground">Assignee: </span>
            {assigneeName ?? "Unassigned"}
          </div>
          <div>
            <span className="text-muted-foreground">Reporter: </span>
            {reporterName ?? "—"}
          </div>
          <div>
            <span className="text-muted-foreground">Priority: </span>
            {priorityName ?? "None"}
          </div>
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">Links</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="mb-3 flex flex-col gap-1 text-sm">
            {links?.map((link) => (
              <li key={link.id} className="text-muted-foreground">
                {link.label}{" "}
                <span className="font-mono text-foreground">
                  {link.source_issue_id === issue.id
                    ? `issue #${link.target_issue_id}`
                    : `issue #${link.source_issue_id}`}
                </span>
              </li>
            ))}
            {!links?.length && <li className="text-muted-foreground">No links yet</li>}
          </ul>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              linkMutation.mutate();
            }}
            className="flex gap-2"
          >
            <Select
              items={Object.fromEntries((linkTypes ?? []).map((lt) => [String(lt.id), lt.outward_name]))}
              value={linkTypeId}
              onValueChange={(v) => setLinkTypeId(v ?? "")}
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Link type" />
              </SelectTrigger>
              <SelectContent>
                {linkTypes?.map((lt) => (
                  <SelectItem key={lt.id} value={String(lt.id)}>
                    {lt.outward_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Input
              placeholder="Target key, e.g. ENG-2"
              value={targetKey}
              onChange={(e) => setTargetKey(e.target.value.toUpperCase())}
              className="flex-1"
            />
            <Button type="submit" disabled={!linkTypeId || !targetKey || linkMutation.isPending}>
              Link
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">Comments</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="mb-3 flex flex-col gap-3">
            {comments?.map((comment) => (
              <li key={comment.id} className="text-sm">
                <span className="font-medium">{users?.find((u) => u.id === comment.author_id)?.display_name ?? "Unknown"}</span>
                <p className="whitespace-pre-wrap text-muted-foreground">{comment.body}</p>
              </li>
            ))}
            {!comments?.length && <li className="text-sm text-muted-foreground">No comments yet</li>}
          </ul>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (commentBody.trim()) commentMutation.mutate();
            }}
            className="flex flex-col gap-2"
          >
            <Textarea
              placeholder="Add a comment…"
              value={commentBody}
              onChange={(e) => setCommentBody(e.target.value)}
              rows={2}
            />
            <Button type="submit" disabled={!commentBody.trim() || commentMutation.isPending} className="self-end">
              Comment
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">History</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="flex flex-col gap-1 text-sm text-muted-foreground">
            {history?.map((entry) => {
              const displayValue = (raw: string | null) => {
                if (raw === null) return "—";
                if (entry.field_name === "status") {
                  return statuses?.find((s) => String(s.id) === raw)?.name ?? raw;
                }
                return raw;
              };
              return (
                <li key={entry.id}>
                  Changed <span className="font-medium text-foreground">{entry.field_name}</span> from{" "}
                  {displayValue(entry.old_value)} to {displayValue(entry.new_value)}
                </li>
              );
            })}
            {!history?.length && <li>No history yet</li>}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
