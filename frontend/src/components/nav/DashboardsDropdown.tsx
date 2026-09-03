import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, Plus, Star } from "lucide-react";
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
import { createDashboard, listDashboards } from "@/api/dashboards";

export function DashboardsDropdown() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: dashboards } = useQuery({ queryKey: ["dashboards"], queryFn: listDashboards });

  const createMutation = useMutation({
    mutationFn: () => createDashboard("New Dashboard"),
    onSuccess: async (dashboard) => {
      await queryClient.invalidateQueries({ queryKey: ["dashboards"] });
      navigate(`/dashboards/${dashboard.id}`);
    },
  });

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button variant="ghost" size="sm" className="gap-1">
            Dashboards <ChevronDown className="size-3.5" />
          </Button>
        }
      />
      <DropdownMenuContent align="start" className="w-56">
        <DropdownMenuGroup>
          <DropdownMenuLabel>Dashboards</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {dashboards?.length ? (
            dashboards.map((dashboard) => (
              <DropdownMenuItem key={dashboard.id} onSelect={() => navigate(`/dashboards/${dashboard.id}`)}>
                {dashboard.is_favorite && <Star className="size-3.5 fill-current text-amber-500" />}
                <span className="truncate">{dashboard.name}</span>
              </DropdownMenuItem>
            ))
          ) : (
            <div className="px-2 py-1.5 text-sm text-muted-foreground">No dashboards yet</div>
          )}
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => createMutation.mutate()}>
          <Plus className="size-4" /> New dashboard
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
