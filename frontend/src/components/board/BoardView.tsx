import { useState } from "react";
import { DndContext, PointerSensor, useSensor, useSensors, type DragEndEvent } from "@dnd-kit/core";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getBoard, getBoardIssues } from "@/api/boards";
import { doTransition, getTransitions } from "@/api/issues";
import { listIssueTypes } from "@/api/metadata";
import { listUsers } from "@/api/users";
import { BoardColumn } from "./BoardColumn";
import type { Issue } from "@/types/api";

interface BoardViewProps {
  boardId: number;
}

export function BoardView({ boardId }: BoardViewProps) {
  const queryClient = useQueryClient();
  const [dropError, setDropError] = useState<string | null>(null);
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }));

  const { data: board } = useQuery({ queryKey: ["board", boardId], queryFn: () => getBoard(boardId) });
  const issuesQueryKey = ["board-issues", boardId];
  const { data: issues, isLoading } = useQuery({
    queryKey: issuesQueryKey,
    queryFn: () => getBoardIssues(boardId),
  });
  const { data: issueTypes } = useQuery({ queryKey: ["issue-types"], queryFn: listIssueTypes });
  const { data: users } = useQuery({ queryKey: ["users"], queryFn: listUsers });

  const issueTypeById = new Map((issueTypes ?? []).map((t) => [t.id, t]));
  const assigneeNameById = new Map((users ?? []).map((u) => [u.id, u.display_name]));

  const transitionMutation = useMutation({
    mutationFn: async ({ issue, targetStatusId }: { issue: Issue; targetStatusId: number }) => {
      const transitions = await getTransitions(issue.key);
      const match = transitions.find((t) => t.to_status_id === targetStatusId);
      if (!match) throw new Error("That move isn't allowed by this issue's workflow");
      return doTransition(issue.key, match.id);
    },
    onMutate: async ({ issue, targetStatusId }) => {
      await queryClient.cancelQueries({ queryKey: issuesQueryKey });
      const previous = queryClient.getQueryData<Issue[]>(issuesQueryKey);
      queryClient.setQueryData<Issue[]>(issuesQueryKey, (old) =>
        old?.map((i) => (i.id === issue.id ? { ...i, status_id: targetStatusId } : i)),
      );
      return { previous };
    },
    onError: (err, _vars, context) => {
      if (context?.previous) queryClient.setQueryData(issuesQueryKey, context.previous);
      setDropError(err instanceof Error ? err.message : "Failed to move issue");
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: issuesQueryKey });
    },
  });

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over) return;
    const issue = active.data.current?.issue as Issue | undefined;
    const targetStatusId = Number(over.id);
    if (!issue || issue.status_id === targetStatusId) return;
    setDropError(null);
    transitionMutation.mutate({ issue, targetStatusId });
  }

  if (!board) {
    return <div className="p-6 text-sm text-muted-foreground">Loading board…</div>;
  }

  return (
    <div className="flex h-full flex-col">
      {dropError && (
        <div className="mx-4 mt-3 rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {dropError}
        </div>
      )}
      <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
        <div className="flex flex-1 gap-3 overflow-x-auto p-4">
          {board.columns.map((column) => (
            <BoardColumn
              key={column.status_id}
              column={column}
              issues={(issues ?? []).filter((i) => i.status_id === column.status_id)}
              issueTypeById={issueTypeById}
              assigneeNameById={assigneeNameById}
            />
          ))}
        </div>
      </DndContext>
      {isLoading && <p className="px-4 pb-4 text-sm text-muted-foreground">Loading issues…</p>}
    </div>
  );
}
