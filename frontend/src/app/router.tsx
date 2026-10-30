import { createBrowserRouter, Navigate } from 'react-router-dom';
import { LoginPage } from '../features/auth/LoginPage';
import { AdminOverviewPage } from '../features/admin/overview/AdminOverviewPage';
import { MyLoadPage } from '../features/faculty/myload/MyLoadPage';
import { LandingPage } from '../features/home/LandingPage';

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
    path: '/admin',
    element: <AdminOverviewPage />,
  },
  {
    path: '/faculty',
    element: <MyLoadPage />,
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);
