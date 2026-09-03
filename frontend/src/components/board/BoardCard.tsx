import { useDraggable } from "@dnd-kit/core";
import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Issue, IssueType } from "@/types/api";

interface BoardCardProps {
  issue: Issue;
  issueType?: IssueType;
  assigneeName?: string | null;
}

export function BoardCard({ issue, issueType, assigneeName }: BoardCardProps) {
  const navigate = useNavigate();
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: issue.id,
    data: { issue },
  });

  const style = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` }
    : undefined;

  return (
    <Card
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      onClick={(e) => {
        // dnd-kit intercepts pointerdown; a plain click (no drag) still fires, so only
        // navigate when the card wasn't actually dragged.
        if (!isDragging) navigate(`/issues/${issue.key}`);
        e.stopPropagation();
      }}
      className="cursor-grab touch-none py-3 shadow-sm active:cursor-grabbing"
    >
      <CardContent className="flex flex-col gap-2 px-3">
        <div className="flex items-center justify-between gap-2">
          <span className="font-mono text-xs text-muted-foreground">{issue.key}</span>
          {issueType && <Badge variant="secondary" className="text-[10px]">{issueType.name}</Badge>}
        </div>
        <p className="text-sm leading-snug">{issue.summary}</p>
        {assigneeName && <p className="text-xs text-muted-foreground">{assigneeName}</p>}
      </CardContent>
    </Card>
  );
}
