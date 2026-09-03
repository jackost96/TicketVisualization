import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ChevronDown, LayoutDashboard, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/auth/AuthContext";
import { DashboardsDropdown } from "./DashboardsDropdown";
import { ProjectsDropdown } from "./ProjectsDropdown";
import { GlobalSearchBox } from "./GlobalSearchBox";
import { CreateIssueDialog } from "@/components/issues/CreateIssueDialog";

const ISSUES_LINKS = [
  { to: "/issues", label: "Search" },
  { to: "/issues/recent", label: "Recent issues" },
  { to: "/issues/mine", label: "My open issues" },
  { to: "/issues/reported-by-me", label: "Reported by me" },
  { to: "/issues/filters", label: "Custom filters" },
];

export function TopNav() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [createOpen, setCreateOpen] = useState(false);

  const initials = user?.display_name
    ?.split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <header className="sticky top-0 z-40 flex h-14 items-center gap-3 border-b bg-background px-4">
      <Link to="/" className="flex items-center gap-2 font-semibold">
        <LayoutDashboard className="size-5" />
        <span className="hidden sm:inline">Ticket System</span>
      </Link>

      <nav className="flex items-center gap-1">
        <DashboardsDropdown />
        <ProjectsDropdown />

        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <Button variant="ghost" size="sm" className="gap-1">
                Issues <ChevronDown className="size-3.5" />
              </Button>
            }
          />
          <DropdownMenuContent align="start" className="w-56">
            <DropdownMenuGroup>
              <DropdownMenuLabel>Issues</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {ISSUES_LINKS.map((link) => (
                <DropdownMenuItem key={link.to} render={<Link to={link.to}>{link.label}</Link>} />
              ))}
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>

        <Button
          variant="ghost"
          size="sm"
          nativeButton={false}
          render={<Link to="/boards">Boards</Link>}
        />
      </nav>

      <div className="flex flex-1 justify-center px-4">
        <GlobalSearchBox />
      </div>

      <Button size="sm" onClick={() => setCreateOpen(true)} className="gap-1">
        <Plus className="size-4" /> Create issue
      </Button>

      <DropdownMenu>
        <DropdownMenuTrigger
          render={
            <button
              type="button"
              className="rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Avatar className="size-8">
                <AvatarFallback>{initials}</AvatarFallback>
              </Avatar>
            </button>
          }
        />
        <DropdownMenuContent align="end" className="w-48">
          <DropdownMenuGroup>
            <DropdownMenuLabel className="truncate">{user?.display_name}</DropdownMenuLabel>
          </DropdownMenuGroup>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onSelect={() => {
              logout();
              navigate("/login");
            }}
          >
            Log out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <CreateIssueDialog open={createOpen} onOpenChange={setCreateOpen} />
    </header>
  );
}
