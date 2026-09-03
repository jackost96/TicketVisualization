import { apiFetch } from "./client";
import type { Board, BoardSummary, Issue } from "@/types/api";

export function listProjectBoards(projectKey: string): Promise<BoardSummary[]> {
  return apiFetch<BoardSummary[]>(`/projects/${projectKey}/boards`);
}

export function getBoard(boardId: number): Promise<Board> {
  return apiFetch<Board>(`/boards/${boardId}`);
}

export function getBoardIssues(boardId: number): Promise<Issue[]> {
  return apiFetch<Issue[]>(`/boards/${boardId}/issues`);
}
