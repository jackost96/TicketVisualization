import { useDroppable } from "@dnd-kit/core";
import { cn } from "@/lib/utils";
import { BoardCard } from "./BoardCard";
import type { BoardColumn as BoardColumnType, Issue, IssueType } from "@/types/api";

interface BoardColumnProps {
  column: BoardColumnType;
  issues: Issue[];
  issueTypeById: Map<number, IssueType>;
  assigneeNameById: Map<number, string>;
}

export function BoardColumn({ column, issues, issueTypeById, assigneeNameById }: BoardColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id: column.status_id });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "flex w-72 shrink-0 flex-col rounded-lg border bg-muted/30 transition-colors",
        isOver && "bg-accent/60",
      )}
    >
      <div className="flex items-center justify-between border-b px-3 py-2">
        <span className="text-sm font-medium">{column.name}</span>
        <span className="text-xs text-muted-foreground">{issues.length}</span>
      </div>
      <div className="flex flex-1 flex-col gap-2 overflow-y-auto p-2">
        {issues.map((issue) => (
          <BoardCard
            key={issue.id}
            issue={issue}
            issueType={issueTypeById.get(issue.issue_type_id)}
            assigneeName={issue.assignee_id ? assigneeNameById.get(issue.assignee_id) : null}
          />
        ))}
        {issues.length === 0 && (
          <p className="px-1 py-2 text-center text-xs text-muted-foreground">No issues</p>
        )}
      </div>
    </div>
  );
}
