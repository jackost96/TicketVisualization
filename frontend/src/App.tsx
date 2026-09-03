import { Navigate, Route, Routes } from "react-router-dom";
import { LoginPage } from "@/auth/LoginPage";
import { ProtectedRoute } from "@/auth/ProtectedRoute";
import { AppShell } from "@/components/nav/AppShell";
import { DashboardPage } from "@/pages/DashboardPage";
import { ProjectsListPage } from "@/pages/ProjectsListPage";
import { ProjectDetailPage } from "@/pages/ProjectDetailPage";
import { IssuesSearchPage } from "@/pages/IssuesSearchPage";
import { IssuesRecentPage } from "@/pages/IssuesRecentPage";
import { IssuesMyOpenPage } from "@/pages/IssuesMyOpenPage";
import { IssuesReportedByMePage } from "@/pages/IssuesReportedByMePage";
import { IssuesFiltersPage } from "@/pages/IssuesFiltersPage";
import { IssueDetailPage } from "@/pages/IssueDetailPage";
import { BoardsListPage } from "@/pages/BoardsListPage";
import { StandaloneBoardPage } from "@/pages/StandaloneBoardPage";

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="dashboards/:id" element={<DashboardPage />} />

          <Route path="projects" element={<ProjectsListPage />} />
          <Route path="projects/:key" element={<ProjectDetailPage />} />
          <Route path="projects/:key/board" element={<ProjectDetailPage />} />
          <Route path="projects/:key/members" element={<ProjectDetailPage />} />
          <Route path="projects/:key/reports" element={<ProjectDetailPage />} />
          <Route path="projects/:key/releases" element={<ProjectDetailPage />} />

          <Route path="issues" element={<IssuesSearchPage />} />
          <Route path="issues/recent" element={<IssuesRecentPage />} />
          <Route path="issues/mine" element={<IssuesMyOpenPage />} />
          <Route path="issues/reported-by-me" element={<IssuesReportedByMePage />} />
          <Route path="issues/filters" element={<IssuesFiltersPage />} />
          <Route path="issues/:key" element={<IssueDetailPage />} />

          <Route path="boards" element={<BoardsListPage />} />
          <Route path="boards/:boardId" element={<StandaloneBoardPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
