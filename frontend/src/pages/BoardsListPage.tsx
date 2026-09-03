import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { listProjects } from "@/api/projects";
import { listProjectBoards } from "@/api/boards";

export function BoardsListPage() {
  const { data: projects } = useQuery({ queryKey: ["projects"], queryFn: listProjects });

  const { data: boards, isLoading } = useQuery({
    queryKey: ["all-boards", projects?.map((p) => p.key)],
    queryFn: async () => {
      const perProject = await Promise.all(
        (projects ?? []).map(async (project) => {
          const projectBoards = await listProjectBoards(project.key);
          return projectBoards.map((board) => ({ ...board, projectKey: project.key, projectName: project.name }));
        }),
      );
      return perProject.flat();
    },
    enabled: Boolean(projects),
  });

  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="mb-4 text-xl font-semibold">Boards</h1>

      {isLoading && <p className="text-sm text-muted-foreground">Loading boards…</p>}
      {!isLoading && !boards?.length && (
        <p className="text-sm text-muted-foreground">No boards yet — create a project to get one automatically.</p>
      )}

      <div className="flex flex-col gap-2">
        {boards?.map((board) => (
          <Link key={board.id} to={`/boards/${board.id}`}>
            <Card className="transition-colors hover:bg-accent/50">
              <CardContent className="flex items-center justify-between py-3">
                <div className="flex items-center gap-3">
                  <span className="rounded bg-muted px-2 py-1 font-mono text-xs">{board.projectKey}</span>
                  <span className="font-medium">{board.name}</span>
                </div>
                <span className="text-xs text-muted-foreground">{board.projectName}</span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
