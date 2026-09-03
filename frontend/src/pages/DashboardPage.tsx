import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Check, Pencil, Star, Trash2, X } from "lucide-react";
import { deleteDashboard, favoriteDashboard, getDashboard, getHomeDashboard, renameDashboard } from "@/api/dashboards";
import { DashboardPanels } from "@/components/dashboard/DashboardPanels";

export function DashboardPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isEditingName, setIsEditingName] = useState(false);
  const [nameDraft, setNameDraft] = useState("");

  const { data: dashboard, isLoading } = useQuery({
    queryKey: id ? ["dashboard", id] : ["dashboard", "home"],
    queryFn: () => (id ? getDashboard(Number(id)) : getHomeDashboard()),
  });

  useEffect(() => {
    if (dashboard) setNameDraft(dashboard.name);
  }, [dashboard]);

  const renameMutation = useMutation({
    mutationFn: (name: string) => renameDashboard(dashboard!.id, name),
    onSuccess: async () => {
      setIsEditingName(false);
      await queryClient.invalidateQueries({ queryKey: ["dashboards"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const favoriteMutation = useMutation({
    mutationFn: () => favoriteDashboard(dashboard!.id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["dashboards"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteDashboard(dashboard!.id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["dashboards"] });
      navigate("/");
    },
  });

  if (isLoading || !dashboard) {
    return <div className="p-6 text-sm text-muted-foreground">Loading dashboard…</div>;
  }

  return (
    <div className="mx-auto max-w-6xl p-6">
      <div className="mb-6 flex items-center gap-2">
        {isEditingName ? (
          <form
            className="flex items-center gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              if (nameDraft.trim()) renameMutation.mutate(nameDraft.trim());
            }}
          >
            <Input value={nameDraft} onChange={(e) => setNameDraft(e.target.value)} className="h-8 w-64" autoFocus />
            <Button type="submit" size="icon" variant="ghost">
              <Check className="size-4" />
            </Button>
            <Button type="button" size="icon" variant="ghost" onClick={() => setIsEditingName(false)}>
              <X className="size-4" />
            </Button>
          </form>
        ) : (
          <>
            <h1 className="text-xl font-semibold">{dashboard.name}</h1>
            <Button size="icon" variant="ghost" onClick={() => setIsEditingName(true)} aria-label="Rename dashboard">
              <Pencil className="size-3.5" />
            </Button>
            <Button
              size="icon"
              variant="ghost"
              onClick={() => favoriteMutation.mutate()}
              aria-label="Set as favorite"
            >
              <Star className={dashboard.is_favorite ? "size-4 fill-current text-amber-500" : "size-4"} />
            </Button>
            <Button
              size="icon"
              variant="ghost"
              onClick={() => {
                if (confirm(`Delete dashboard "${dashboard.name}"?`)) deleteMutation.mutate();
              }}
              aria-label="Delete dashboard"
            >
              <Trash2 className="size-4" />
            </Button>
          </>
        )}
      </div>

      <DashboardPanels />
    </div>
  );
}
