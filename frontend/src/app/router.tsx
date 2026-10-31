import { createBrowserRouter } from 'react-router-dom';
import { LoginPage } from '../features/auth/LoginPage';
import { AdminOverviewPage } from '../features/admin/overview/AdminOverviewPage';
import { AssignmentsPage } from '../features/admin/assignments/AssignmentsPage';
import { ForecastPage } from '../features/admin/forecast/ForecastPage';
import { LoadBalancePage } from '../features/admin/load/LoadBalancePage';
import { ConflictsPage } from '../features/admin/conflicts/ConflictsPage';
import { RulesCatalogPage } from '../features/admin/rules/RulesCatalogPage';
import { AuditTrailPage } from '../features/admin/audit/AuditTrailPage';
import { OverridesPage } from '../features/admin/overrides/OverridesPage';
import { MyLoadPage } from '../features/faculty/myload/MyLoadPage';
import { AvailabilityPage } from '../features/faculty/availability/AvailabilityPage';
import { RequestsPage } from '../features/faculty/requests/RequestsPage';
import { LandingPage } from '../features/home/LandingPage';
import { ProtectedRoute } from '../components/layout/ProtectedRoute';
import { AdminLayout } from '../components/layout/AdminLayout';
import { FacultyLayout } from '../components/layout/FacultyLayout';
import { ForbiddenPage } from '../components/layout/ForbiddenPage';
import { NotFoundPage } from '../components/layout/NotFoundPage';
import { FeaturePlaceholderPage } from '../components/layout/FeaturePlaceholderPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <LandingPage />,
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/403',
    element: <ForbiddenPage />,
  },
  {
    path: '/admin',
    element: (
      <ProtectedRoute allowedRoles={['admin']}>
        <AdminLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <AdminOverviewPage />,
      },
      {
        path: 'assignments',
        element: <AssignmentsPage />,
      },
      {
        path: 'forecasts',
        element: <ForecastPage />,
      },
      {
        path: 'load',
        element: <LoadBalancePage />,
      },
      {
        path: 'faculty',
        element: (
          <FeaturePlaceholderPage
            title="Faculty Directory"
            category="Personnel"
            description="Faculty profiles, expertise proficiencies, ranks, and maximum load capacities."
            backLink="/admin"
          />
        ),
      },
      {
        path: 'courses',
        element: (
          <FeaturePlaceholderPage
            title="Course Catalog & Syllabi"
            category="Academic Offerings"
            description="Curriculum requirements, contact hours, required expertise tags, and labs."
            backLink="/admin"
          />
        ),
      },
      {
        path: 'conflicts',
        element: <ConflictsPage />,
      },
      {
        path: 'constraints',
        element: <RulesCatalogPage />,
      },
      {
        path: 'overrides',
        element: <OverridesPage />,
      },
      {
        path: 'scenarios',
        element: (
          <FeaturePlaceholderPage
            title="Benchmark Scenarios"
            category="Evaluation"
            description="Load reproducible benchmark fixtures (e.g., infeasible expertise, tight capacity)."
            backLink="/admin"
          />
        ),
      },
      {
        path: 'audit',
        element: <AuditTrailPage />,
      },
    ],
  },
  {
    path: '/faculty',
    element: (
      <ProtectedRoute allowedRoles={['faculty']}>
        <FacultyLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <MyLoadPage />,
      },
      {
        path: 'preferences',
        element: <AvailabilityPage />,
      },
      {
        path: 'requests',
        element: <RequestsPage />,
      },
      {
        path: 'expertise',
        element: (
          <FeaturePlaceholderPage
            title="Expertise & Syllabi Fit"
            category="Teaching Profile"
            description="Update research tags, self-evaluated proficiencies, and syllabus matches."
            backLink="/faculty"
          />
        ),
      },
      {
        path: 'courses',
        element: (
          <FeaturePlaceholderPage
            title="Department Course Sections"
            category="Offerings"
            description="Browse active sections, scheduled timeslots, and assigned classrooms."
            backLink="/faculty"
          />
        ),
      },
    ],
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
]);
