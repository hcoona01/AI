import { createBrowserRouter } from 'react-router-dom';
import { LoginPage } from '../features/auth/LoginPage';
import { AdminOverviewPage } from '../features/admin/overview/AdminOverviewPage';
import { MyLoadPage } from '../features/faculty/myload/MyLoadPage';
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
        element: (
          <FeaturePlaceholderPage
            title="Course Assignments"
            category="Workload Optimization"
            description="CP-SAT optimizer recommendations, teaching loads, and section distributions."
            backLink="/admin"
          />
        ),
      },
      {
        path: 'forecasts',
        element: (
          <FeaturePlaceholderPage
            title="Demand Forecasts (ML Quantiles)"
            category="Machine Learning"
            description="P10, P50, and P90 section enrollment forecasts from LightGBM quantile regression."
            backLink="/admin"
          />
        ),
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
        path: 'constraints',
        element: (
          <FeaturePlaceholderPage
            title="Constraint Rules Engine"
            category="Solver Rules"
            description="Hard and soft constraint parameterization (HC-01 through SC-03) and weights."
            backLink="/admin"
          />
        ),
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
        element: (
          <FeaturePlaceholderPage
            title="Audit Trail"
            category="Compliance"
            description="Immutable record of administrative actions, overrides, and schedule modifications."
            backLink="/admin"
          />
        ),
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
        element: (
          <FeaturePlaceholderPage
            title="Availability & Blackout Preferences"
            category="Faculty Input"
            description="Submit unavailable timeslots, leave semesters, and preferred courses."
            backLink="/faculty"
          />
        ),
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
