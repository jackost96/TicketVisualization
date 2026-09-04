import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { listProjects } from "@/api/projects";
import { listIssueTypes, listPriorities } from "@/api/metadata";
import { listUsers } from "@/api/users";
import { createIssue } from "@/api/issues";
import { getErrorMessage } from "@/api/client";

interface CreateIssueDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultProjectKey?: string;
}

export function CreateIssueDialog({ open, onOpenChange, defaultProjectKey }: CreateIssueDialogProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [projectKey, setProjectKey] = useState(defaultProjectKey ?? "");
  const [issueTypeId, setIssueTypeId] = useState("");
  const [summary, setSummary] = useState("");
  const [description, setDescription] = useState("");
  const [assigneeId, setAssigneeId] = useState<string>("");
  const [priorityId, setPriorityId] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const { data: projects } = useQuery({ queryKey: ["projects"], queryFn: listProjects, enabled: open });
  const { data: issueTypes } = useQuery({ queryKey: ["issue-types"], queryFn: listIssueTypes, enabled: open });
  const { data: users } = useQuery({ queryKey: ["users"], queryFn: listUsers, enabled: open });
  const { data: priorities } = useQuery({ queryKey: ["priorities"], queryFn: listPriorities, enabled: open });

  const mutation = useMutation({
    mutationFn: () =>
      createIssue({
        project_key: projectKey,
        issue_type_id: Number(issueTypeId),
        summary,
        description: description || undefined,
        assignee_id: assigneeId ? Number(assigneeId) : undefined,
        priority_id: priorityId ? Number(priorityId) : undefined,
      }),
    onSuccess: async (issue) => {
      await queryClient.invalidateQueries({ queryKey: ["issues"] });
      await queryClient.invalidateQueries({ queryKey: ["board-issues"] });
      resetForm();
      onOpenChange(false);
      navigate(`/issues/${issue.key}`);
    },
    onError: (err) => setError(getErrorMessage(err, "Failed to create issue")),
  });

  function resetForm() {
    setProjectKey(defaultProjectKey ?? "");
    setIssueTypeId("");
    setSummary("");
    setDescription("");
    setAssigneeId("");
    setPriorityId("");
    setError(null);
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) resetForm();
        onOpenChange(next);
      }}
    >
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Create issue</DialogTitle>
        </DialogHeader>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setError(null);
            mutation.mutate();
          }}
          className="flex flex-col gap-4"
        >
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <Label>Project</Label>
              <Select
                items={Object.fromEntries((projects ?? []).map((p) => [p.key, `${p.key} — ${p.name}`]))}
                value={projectKey}
                onValueChange={(v) => setProjectKey(v ?? "")}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select project" />
                </SelectTrigger>
                <SelectContent>
                  {projects?.map((project) => (
                    <SelectItem key={project.id} value={project.key}>
                      {project.key} — {project.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-2">
              <Label>Issue type</Label>
              <Select
                items={Object.fromEntries((issueTypes ?? []).map((t) => [String(t.id), t.name]))}
                value={issueTypeId}
                onValueChange={(v) => setIssueTypeId(v ?? "")}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  {issueTypes?.map((type) => (
                    <SelectItem key={type.id} value={String(type.id)}>
                      {type.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor="summary">Summary</Label>
            <Input id="summary" value={summary} onChange={(e) => setSummary(e.target.value)} required />
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <Label>Assignee</Label>
              <Select
                items={Object.fromEntries((users ?? []).map((u) => [String(u.id), u.display_name]))}
                value={assigneeId}
                onValueChange={(v) => setAssigneeId(v ?? "")}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Unassigned" />
                </SelectTrigger>
                <SelectContent>
                  {users?.map((user) => (
                    <SelectItem key={user.id} value={String(user.id)}>
                      {user.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-2">
              <Label>Priority</Label>
              <Select
                items={Object.fromEntries((priorities ?? []).map((p) => [String(p.id), p.name]))}
                value={priorityId}
                onValueChange={(v) => setPriorityId(v ?? "")}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="None" />
                </SelectTrigger>
                <SelectContent>
                  {priorities?.map((priority) => (
                    <SelectItem key={priority.id} value={String(priority.id)}>
                      {priority.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <DialogFooter>
            <Button type="submit" disabled={mutation.isPending || !projectKey || !issueTypeId || !summary}>
              Create issue
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
