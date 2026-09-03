import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Plus } from "lucide-react";
import { listProjects } from "@/api/projects";
import { CreateProjectDialog } from "@/components/nav/CreateProjectDialog";

export function ProjectsListPage() {
  const [createOpen, setCreateOpen] = useState(false);
  const { data: projects, isLoading } = useQuery({ queryKey: ["projects"], queryFn: listProjects });

  return (
    <div className="mx-auto max-w-3xl p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Projects</h1>
        <Button size="sm" className="gap-1" onClick={() => setCreateOpen(true)}>
          <Plus className="size-4" /> New project
        </Button>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading projects…</p>}
      {!isLoading && !projects?.length && (
        <p className="text-sm text-muted-foreground">No projects yet — create one to get started.</p>
      )}

      <div className="flex flex-col gap-2">
        {projects?.map((project) => (
          <Link key={project.id} to={`/projects/${project.key}`}>
            <Card className="transition-colors hover:bg-accent/50">
              <CardContent className="flex items-center gap-3 py-3">
                <span className="rounded bg-muted px-2 py-1 font-mono text-xs">{project.key}</span>
                <span className="font-medium">{project.name}</span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <CreateProjectDialog open={createOpen} onOpenChange={setCreateOpen} />
    </div>
  );
}
