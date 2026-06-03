import { useEffect, useMemo, useState } from 'react';

import { LoginPage } from '../features/auth/LoginPage';
import { isAuthenticated, subscribeAuth } from '../features/auth/authStore';
import { AppLayout } from '../layouts/AppLayout';
import { DashboardPage } from '../pages/DashboardPage';
import { CustomersPage } from '../pages/CustomersPage';
import { DealsPage } from '../pages/DealsPage';
import { PropertiesPage } from '../pages/PropertiesPage';
import { ReportsPage } from '../pages/ReportsPage';

export function navigateTo(path: string): void {
  window.history.pushState({}, '', path);
  window.dispatchEvent(new PopStateEvent('popstate'));
}

const protectedPages: Record<string, unknown> = {
  '/dashboard': <DashboardPage />,
  '/customers': <CustomersPage />,
  '/properties': <PropertiesPage />,
  '/deals': <DealsPage />,
  '/reports': <ReportsPage />,
};

export function AppRoutes() {
  const [path, setPath] = useState(window.location.pathname);
  const [, setAuthVersion] = useState(0);

  useEffect(() => {
    const handlePopState = () => setPath(window.location.pathname);
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  useEffect(() => subscribeAuth(() => setAuthVersion((value) => value + 1)), []);

  const authenticated = isAuthenticated();
  const normalizedPath = path === '/' ? '/dashboard' : path;

  useEffect(() => {
    if (!authenticated && normalizedPath !== '/login') {
      window.history.replaceState({}, '', '/login');
      setPath('/login');
    }
    if (authenticated && normalizedPath === '/login') {
      window.history.replaceState({}, '', '/dashboard');
      setPath('/dashboard');
    }
  }, [authenticated, normalizedPath]);

  const page = useMemo(() => protectedPages[normalizedPath] ?? protectedPages['/dashboard'], [normalizedPath]);

  if (!authenticated) {
    return <LoginPage />;
  }

  return <AppLayout currentPath={normalizedPath}>{page}</AppLayout>;
}
