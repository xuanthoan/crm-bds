import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { authStore } from './authStore';

export function ProtectedRoute() {
  const location = useLocation();
  const { accessToken, user } = authStore.getState();

  if (!accessToken || !user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
