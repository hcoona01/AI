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
import { FacultyDirectoryPage } from '../features/admin/faculty/FacultyDirectoryPage';
import { CoursesCatalogPage } from '../features/admin/courses/CoursesCatalogPage';
import { ScenariosPage } from '../features/admin/scenarios/ScenariosPage';
import { MyLoadPage } from '../features/faculty/myload/MyLoadPage';
import { AvailabilityPage } from '../features/faculty/availability/AvailabilityPage';
import { RequestsPage } from '../features/faculty/requests/RequestsPage';
import { ExpertiseFitPage } from '../features/faculty/expertise/ExpertiseFitPage';
import { FacultyCourseSectionsPage } from '../features/faculty/courses/FacultyCourseSectionsPage';
import { LandingPage } from '../features/home/LandingPage';
import { ProtectedRoute } from '../components/layout/ProtectedRoute';
import { AdminLayout } from '../components/layout/AdminLayout';
import { FacultyLayout } from '../components/layout/FacultyLayout';
import { ForbiddenPage } from '../components/layout/ForbiddenPage';
import { NotFoundPage } from '../components/layout/NotFoundPage';

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
        element: <FacultyDirectoryPage />,
      },
      {
        path: 'courses',
        element: <CoursesCatalogPage />,
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
        element: <ScenariosPage />,
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
        element: <ExpertiseFitPage />,
      },
      {
        path: 'courses',
        element: <FacultyCourseSectionsPage />,
      },
    ],
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
]);
