import { useEffect, useMemo, useState, type ReactNode } from 'react';

import { LoginPage } from '../features/auth/LoginPage';
import { can, isAuthenticated, subscribeAuth } from '../features/auth/authStore';
import { PermissionsPage } from '../features/admin/permissions/PermissionsPage';
import { RolesPage } from '../features/admin/roles/RolesPage';
import { UsersPage } from '../features/admin/users/UsersPage';
import { LeadDetailPage } from '../features/leads/LeadDetailPage';
import { LeadsPage } from '../features/leads/LeadsPage';
import { LEAD_VIEW_PERMISSIONS } from '../features/leads/constants';
import { AppLayout } from '../layouts/AppLayout';
import { CustomersPage } from '../pages/CustomersPage';
import { DashboardPage } from '../pages/DashboardPage';
import { DealsPage } from '../pages/DealsPage';
import { ForbiddenPage } from '../pages/ForbiddenPage';
import { PropertiesPage } from '../pages/PropertiesPage';
import { ReportsPage } from '../pages/ReportsPage';

export function navigateTo(path: string): void {
  window.history.pushState({}, '', path);
  window.dispatchEvent(new PopStateEvent('popstate'));
}

type ProtectedPage = {
  element: unknown;
  permission?: string | string[];
};

const protectedPages: Record<string, ProtectedPage> = {
  '/dashboard': { element: <DashboardPage /> },
  '/leads': { element: <LeadsPage />, permission: LEAD_VIEW_PERMISSIONS },
  '/admin/users': { element: <UsersPage />, permission: 'users.view' },
  '/admin/roles': { element: <RolesPage />, permission: 'roles.view' },
  '/admin/permissions': { element: <PermissionsPage />, permission: 'permissions.view' },
  '/customers': { element: <CustomersPage />, permission: 'customers.view.own' },
  '/properties': { element: <PropertiesPage />, permission: 'inventory.view.available' },
  '/deals': { element: <DealsPage />, permission: 'deals.view.own' },
  '/reports': { element: <ReportsPage />, permission: 'reports.view.own' },
};

export function PermissionRoute({ permission, children }: { permission?: string | string[]; children?: ReactNode }) {
  const allowed = !permission || (Array.isArray(permission) ? permission.some(can) : can(permission));
  if (!allowed) {
    return <ForbiddenPage />;
  }

  return <>{children}</>;
}

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

  const page = useMemo(() => {
    const leadDetailMatch = normalizedPath.match(/^\/leads\/([0-9a-f-]+)$/i);
    if (leadDetailMatch) return { element: <LeadDetailPage leadId={leadDetailMatch[1]} />, permission: LEAD_VIEW_PERMISSIONS };
    return protectedPages[normalizedPath] ?? protectedPages['/dashboard'];
  }, [normalizedPath]);

  if (!authenticated) {
    return <LoginPage />;
  }

  return (
    <AppLayout currentPath={normalizedPath}>
      <PermissionRoute permission={page.permission}>{page.element}</PermissionRoute>
    </AppLayout>
  );
}
