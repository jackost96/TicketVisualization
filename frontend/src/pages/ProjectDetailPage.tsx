import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { IssueTable } from "@/components/issues/IssueTable";
import { BoardView } from "@/components/board/BoardView";
import { ProjectMembersPanel } from "@/components/project/ProjectMembersPanel";
import { getProject } from "@/api/projects";
import { listProjectBoards } from "@/api/boards";
import { listIssues } from "@/api/issues";

function tabFromPath(pathname: string): "issues" | "board" | "members" | "reports" | "releases" {
  if (pathname.endsWith("/board")) return "board";
  if (pathname.endsWith("/members")) return "members";
  if (pathname.endsWith("/reports")) return "reports";
  if (pathname.endsWith("/releases")) return "releases";
  return "issues";
}

function ComingSoon({ label }: { label: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-1 text-muted-foreground">
      <p className="text-lg font-medium">{label}</p>
      <p className="text-sm">Coming soon</p>
    </div>
  );
}

export function ProjectDetailPage() {
  const { key } = useParams<{ key: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const activeTab = tabFromPath(location.pathname);

  const { data: project } = useQuery({
    queryKey: ["project", key],
    queryFn: () => getProject(key!),
    enabled: Boolean(key),
  });
  const { data: boards } = useQuery({
    queryKey: ["project-boards", key],
    queryFn: () => listProjectBoards(key!),
    enabled: Boolean(key),
  });
  const { data: issues, isLoading: issuesLoading } = useQuery({
    queryKey: ["issues", "project", key],
    queryFn: () => listIssues({ project: key!, limit: 100 }),
    enabled: Boolean(key) && activeTab === "issues",
  });

  const defaultBoard = boards?.[0];

  function handleTabChange(value: string) {
    if (!key) return;
    navigate(value === "issues" ? `/projects/${key}` : `/projects/${key}/${value}`);
  }

  if (!project) {
    return <div className="p-6 text-sm text-muted-foreground">Loading project…</div>;
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b bg-background px-6 pt-4">
        <div className="mb-3 flex items-center gap-2">
          <span className="rounded bg-muted px-2 py-1 font-mono text-xs">{project.key}</span>
          <h1 className="text-lg font-semibold">{project.name}</h1>
        </div>
        <Tabs value={activeTab} onValueChange={handleTabChange}>
          <TabsList>
            <TabsTrigger value="issues">Issues</TabsTrigger>
            <TabsTrigger value="board">Board</TabsTrigger>
            <TabsTrigger value="members">Members</TabsTrigger>
            <TabsTrigger value="reports">Reports</TabsTrigger>
            <TabsTrigger value="releases">Releases</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="flex-1 overflow-hidden">
        {activeTab === "issues" && (
          <div className="h-full overflow-y-auto p-6">
            <div className="rounded-lg border bg-background">
              <IssueTable issues={issues} isLoading={issuesLoading} />
            </div>
          </div>
        )}
        {activeTab === "board" &&
          (defaultBoard ? (
            <BoardView boardId={defaultBoard.id} />
          ) : (
            <p className="p-6 text-sm text-muted-foreground">No board configured for this project</p>
          ))}
        {activeTab === "members" && (
          <div className="h-full overflow-y-auto">
            <ProjectMembersPanel projectKey={key!} />
          </div>
        )}
        {activeTab === "reports" && <ComingSoon label="Reports" />}
        {activeTab === "releases" && <ComingSoon label="Releases" />}
      </div>
    </div>
  );
}
