import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { IssueTable } from "@/components/issues/IssueTable";
import { listIssues } from "@/api/issues";
import { listProjects } from "@/api/projects";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";

export function IssuesSearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [term, setTerm] = useState(searchParams.get("q") ?? "");
  const [projectKey, setProjectKey] = useState(searchParams.get("project") ?? "");
  const debouncedTerm = useDebouncedValue(term, 300);

  const { data: projects } = useQuery({ queryKey: ["projects"], queryFn: listProjects });
  const { data: issues, isLoading } = useQuery({
    queryKey: ["issues", "search", debouncedTerm, projectKey],
    queryFn: () => listIssues({ q: debouncedTerm || undefined, project: projectKey || undefined, limit: 100 }),
  });

  function handleTermChange(value: string) {
    setTerm(value);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) next.set("q", value);
      else next.delete("q");
      return next;
    });
  }

  return (
    <div className="mx-auto max-w-5xl p-6">
      <h1 className="mb-4 text-xl font-semibold">Search issues</h1>
      <div className="mb-4 flex gap-3">
        <Input
          placeholder="Search by summary or description…"
          value={term}
          onChange={(e) => handleTermChange(e.target.value)}
          className="max-w-sm"
        />
        <Select
          items={{
            __all__: "All projects",
            ...Object.fromEntries((projects ?? []).map((p) => [p.key, `${p.key} — ${p.name}`])),
          }}
          value={projectKey || "__all__"}
          onValueChange={(v) => setProjectKey(!v || v === "__all__" ? "" : v)}
        >
          <SelectTrigger className="w-48">
            <SelectValue placeholder="All projects" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">All projects</SelectItem>
            {projects?.map((project) => (
              <SelectItem key={project.id} value={project.key}>
                {project.key} — {project.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="rounded-lg border bg-background">
        <IssueTable issues={issues} isLoading={isLoading} />
      </div>
    </div>
  );
}
