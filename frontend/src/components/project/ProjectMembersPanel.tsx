import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { X } from "lucide-react";
import { addRoleMember, getMyPermissions, listRoleMembers, removeRoleMember } from "@/api/projects";
import { listProjectRoles } from "@/api/metadata";
import { listUsers } from "@/api/users";

interface ProjectMembersPanelProps {
  projectKey: string;
}

export function ProjectMembersPanel({ projectKey }: ProjectMembersPanelProps) {
  const queryClient = useQueryClient();
  const [pendingUserByRole, setPendingUserByRole] = useState<Record<number, string>>({});

  const { data: permissions } = useQuery({
    queryKey: ["permissions", projectKey],
    queryFn: () => getMyPermissions(projectKey),
  });
  const isAdmin = permissions?.permissions.includes("project.admin") ?? false;

  const { data: roles } = useQuery({ queryKey: ["project-roles"], queryFn: listProjectRoles });
  const { data: users } = useQuery({ queryKey: ["users"], queryFn: listUsers });

  const { data: membersByRole } = useQuery({
    queryKey: ["project-role-members", projectKey, roles?.map((r) => r.id)],
    queryFn: async () => {
      const entries = await Promise.all(
        (roles ?? []).map(async (role) => [role.id, await listRoleMembers(projectKey, role.id)] as const),
      );
      return Object.fromEntries(entries);
    },
    enabled: Boolean(roles?.length),
  });

  const invalidateMembers = () =>
    queryClient.invalidateQueries({ queryKey: ["project-role-members", projectKey] });

  const addMutation = useMutation({
    mutationFn: ({ roleId, userId }: { roleId: number; userId: number }) =>
      addRoleMember(projectKey, roleId, userId),
    onSuccess: invalidateMembers,
  });

  const removeMutation = useMutation({
    mutationFn: ({ roleId, userId }: { roleId: number; userId: number }) =>
      removeRoleMember(projectKey, roleId, userId),
    onSuccess: invalidateMembers,
  });

  const userName = (id: number) => users?.find((u) => u.id === id)?.display_name ?? `User #${id}`;

  return (
    <div className="mx-auto max-w-3xl p-6">
      <h2 className="mb-1 text-lg font-semibold">Members</h2>
      <p className="mb-4 text-sm text-muted-foreground">
        {isAdmin
          ? "Add or remove people from this project's roles. Each role's permissions are defined project-wide."
          : "Only project administrators can add or remove members."}
      </p>

      <div className="flex flex-col gap-4">
        {roles?.map((role) => {
          const members = membersByRole?.[role.id] ?? [];
          const memberUserIds = new Set(members.map((m) => m.user_id));
          const availableUsers = (users ?? []).filter((u) => !memberUserIds.has(u.id));
          const pendingUserId = pendingUserByRole[role.id] ?? "";

          return (
            <Card key={role.id}>
              <CardHeader>
                <CardTitle className="text-base">{role.name}</CardTitle>
                {role.description && <p className="text-sm text-muted-foreground">{role.description}</p>}
              </CardHeader>
              <CardContent>
                <ul className="mb-3 flex flex-col gap-1.5">
                  {members.map((member) => (
                    <li key={member.user_id} className="flex items-center justify-between text-sm">
                      <span>{userName(member.user_id)}</span>
                      {isAdmin && (
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          aria-label={`Remove ${userName(member.user_id)} from ${role.name}`}
                          onClick={() => removeMutation.mutate({ roleId: role.id, userId: member.user_id })}
                        >
                          <X className="size-3.5" />
                        </Button>
                      )}
                    </li>
                  ))}
                  {members.length === 0 && (
                    <li className="text-sm text-muted-foreground">No members yet</li>
                  )}
                </ul>

                {isAdmin && (
                  <div className="flex gap-2">
                    <Select
                      items={Object.fromEntries(availableUsers.map((u) => [String(u.id), u.display_name]))}
                      value={pendingUserId}
                      onValueChange={(v) =>
                        setPendingUserByRole((prev) => ({ ...prev, [role.id]: v ?? "" }))
                      }
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Add a member…" />
                      </SelectTrigger>
                      <SelectContent>
                        {availableUsers.map((user) => (
                          <SelectItem key={user.id} value={String(user.id)}>
                            {user.display_name} ({user.email})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Button
                      disabled={!pendingUserId || addMutation.isPending}
                      onClick={() => {
                        addMutation.mutate({ roleId: role.id, userId: Number(pendingUserId) });
                        setPendingUserByRole((prev) => ({ ...prev, [role.id]: "" }));
                      }}
                    >
                      Add
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
