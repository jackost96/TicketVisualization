import { useParams } from "react-router-dom";
import { BoardView } from "@/components/board/BoardView";

export function StandaloneBoardPage() {
  const { boardId } = useParams<{ boardId: string }>();
  if (!boardId) return null;
  return (
    <div className="h-full">
      <BoardView boardId={Number(boardId)} />
    </div>
  );
}
