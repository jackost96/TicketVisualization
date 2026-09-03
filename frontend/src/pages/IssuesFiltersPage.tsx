import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Trash2 } from "lucide-react";
import { createSavedFilter, deleteSavedFilter, listSavedFilters } from "@/api/savedFilters";
import type { FilterQuery } from "@/types/api";

function queryToSearchParams(query: FilterQuery): string {
  const params = new URLSearchParams();
  if (query.project) params.set("project", query.project);
  if (query.q) params.set("q", query.q);
  return params.toString();
}

export function IssuesFiltersPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [project, setProject] = useState("");
  const [q, setQ] = useState("");

  const { data: filters, isLoading } = useQuery({ queryKey: ["saved-filters"], queryFn: listSavedFilters });

  const createMutation = useMutation({
    mutationFn: () => createSavedFilter(name, { project: project || undefined, q: q || undefined }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["saved-filters"] });
      setName("");
      setProject("");
      setQ("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteSavedFilter(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["saved-filters"] }),
  });

  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="mb-4 text-xl font-semibold">Custom filters</h1>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">New filter</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createMutation.mutate();
            }}
            className="grid grid-cols-1 gap-3 sm:grid-cols-4 sm:items-end"
          >
            <div className="flex flex-col gap-1.5 sm:col-span-2">
              <Label htmlFor="filter-name">Name</Label>
              <Input id="filter-name" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="filter-project">Project key</Label>
              <Input
                id="filter-project"
                placeholder="e.g. ENG"
                value={project}
                onChange={(e) => setProject(e.target.value.toUpperCase())}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="filter-q">Search text</Label>
              <Input id="filter-q" value={q} onChange={(e) => setQ(e.target.value)} />
            </div>
            <Button type="submit" disabled={createMutation.isPending || !name} className="sm:col-span-4">
              Save filter
            </Button>
          </form>
        </CardContent>
      </Card>

      {isLoading && <p className="text-sm text-muted-foreground">Loading filters…</p>}
      {!isLoading && !filters?.length && (
        <p className="text-sm text-muted-foreground">You haven't saved any filters yet.</p>
      )}

      <ul className="flex flex-col gap-2">
        {filters?.map((filter) => (
          <li key={filter.id} className="flex items-center justify-between rounded-lg border bg-background p-3">
            <button
              type="button"
              className="text-left hover:underline"
              onClick={() => navigate(`/issues?${queryToSearchParams(filter.query)}`)}
            >
              <div className="font-medium">{filter.name}</div>
              <div className="text-xs text-muted-foreground">
                {filter.query.project ? `project: ${filter.query.project} ` : ""}
                {filter.query.q ? `q: "${filter.query.q}"` : ""}
              </div>
            </button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => deleteMutation.mutate(filter.id)}
              aria-label="Delete filter"
            >
              <Trash2 className="size-4" />
            </Button>
          </li>
        ))}
      </ul>
    </div>
  );
}
