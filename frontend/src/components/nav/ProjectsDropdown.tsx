import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { listProjects } from "@/api/projects";
import { CreateProjectDialog } from "./CreateProjectDialog";

export function ProjectsDropdown() {
  const [createOpen, setCreateOpen] = useState(false);
  const { data: projects } = useQuery({ queryKey: ["projects"], queryFn: listProjects });

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger
          render={
            <Button variant="ghost" size="sm" className="gap-1">
              Projects <ChevronDown className="size-3.5" />
            </Button>
          }
        />
        <DropdownMenuContent align="start" className="w-56">
          <DropdownMenuGroup>
            <DropdownMenuLabel>Projects</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {projects?.length ? (
              projects.map((project) => (
                <DropdownMenuItem
                  key={project.id}
                  render={
                    <Link to={`/projects/${project.key}`}>
                      <span className="font-mono text-xs text-muted-foreground">{project.key}</span>
                      <span className="ml-2 truncate">{project.name}</span>
                    </Link>
                  }
                />
              ))
            ) : (
              <div className="px-2 py-1.5 text-sm text-muted-foreground">No projects yet</div>
            )}
          </DropdownMenuGroup>
          <DropdownMenuSeparator />
          <DropdownMenuItem render={<Link to="/projects">View all projects</Link>} />
          <DropdownMenuItem onSelect={() => setCreateOpen(true)}>
            <Plus className="size-4" /> New project
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <CreateProjectDialog open={createOpen} onOpenChange={setCreateOpen} />
    </>
  );
}
