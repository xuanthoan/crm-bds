import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from './authStore';

export function ProtectedRoute() {
  const location = useLocation();
  const { accessToken, user } = useAuth();

  if (!accessToken || !user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
