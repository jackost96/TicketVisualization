import { Outlet } from "react-router-dom";
import { TopNav } from "./TopNav";

export function AppShell() {
  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <TopNav />
      <main className="flex-1 overflow-y-auto bg-muted/20">
        <Outlet />
      </main>
    </div>
  );
}
