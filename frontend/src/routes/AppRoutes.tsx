import { useEffect, useMemo, useState, type ReactNode } from 'react';

import { LoginPage } from '../features/auth/LoginPage';
import { can, isAuthenticated, subscribeAuth } from '../features/auth/authStore';
import { PermissionsPage } from '../features/admin/permissions/PermissionsPage';
import { RolesPage } from '../features/admin/roles/RolesPage';
import { UsersPage } from '../features/admin/users/UsersPage';
import { LeadDetailPage } from '../features/leads/LeadDetailPage';
import { LeadsPage } from '../features/leads/LeadsPage';
import { OverdueLeadsPage } from '../features/leads/OverdueLeadsPage';
import { DepartmentsPage } from '../features/organization/DepartmentsPage';
import { TeamsPage } from '../features/organization/TeamsPage';
import { MembershipsPage } from '../features/organization/MembershipsPage';
import { LEAD_VIEW_PERMISSIONS } from '../features/leads/constants';
import { TasksPage } from '../features/tasks/TasksPage';
import { TodayTasksPage } from '../features/tasks/TodayTasksPage';
import { OverdueTasksPage } from '../features/tasks/OverdueTasksPage';
import { AppointmentsPage } from '../features/appointments/AppointmentsPage';
import { TodayAppointmentsPage } from '../features/appointments/TodayAppointmentsPage';
import { MyWorkDashboard } from '../features/dashboard/MyWorkDashboard';
import { TeamWorkDashboard } from '../features/dashboard/TeamWorkDashboard';
import { AppLayout } from '../layouts/AppLayout';
import { CustomersPage } from '../features/customers/CustomersPage';
import { CustomerDetailPage } from '../features/customers/CustomerDetailPage';
import { CUSTOMER_VIEW_PERMISSIONS } from '../features/customers/constants';
import { DealsPage } from '../features/deals/DealsPage';
import { DealDetailPage } from '../features/deals/DealDetailPage';
import { DEAL_VIEW_PERMISSIONS } from '../features/deals/constants';
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
  '/dashboard': { element: <MyWorkDashboard />, permission: ['dashboard.view.own', 'dashboard.view.team', 'dashboard.view.all'] },
  '/dashboard/my-work': { element: <MyWorkDashboard />, permission: ['dashboard.view.own', 'dashboard.view.team', 'dashboard.view.all'] },
  '/dashboard/team-work': { element: <TeamWorkDashboard />, permission: ['dashboard.view.team', 'dashboard.view.all'] },
  '/tasks': { element: <TasksPage />, permission: ['lead_tasks.view.own', 'lead_tasks.view.team', 'lead_tasks.view.all'] },
  '/tasks/today': { element: <TodayTasksPage />, permission: ['lead_tasks.view.own', 'lead_tasks.view.team', 'lead_tasks.view.all'] },
  '/tasks/overdue': { element: <OverdueTasksPage />, permission: ['lead_tasks.view.own', 'lead_tasks.view.team', 'lead_tasks.view.all'] },
  '/appointments': { element: <AppointmentsPage />, permission: ['lead_appointments.view.own', 'lead_appointments.view.team', 'lead_appointments.view.all'] },
  '/appointments/today': { element: <TodayAppointmentsPage />, permission: ['lead_appointments.view.own', 'lead_appointments.view.team', 'lead_appointments.view.all'] },
  '/leads': { element: <LeadsPage />, permission: LEAD_VIEW_PERMISSIONS },
  '/leads/overdue': { element: <OverdueLeadsPage />, permission: LEAD_VIEW_PERMISSIONS },
  '/admin/users': { element: <UsersPage />, permission: 'users.view' },
  '/admin/roles': { element: <RolesPage />, permission: 'roles.view' },
  '/admin/permissions': { element: <PermissionsPage />, permission: 'permissions.view' },
  '/admin/departments': { element: <DepartmentsPage />, permission: 'settings.manage_master_data' },
  '/admin/teams': { element: <TeamsPage />, permission: 'settings.manage_master_data' },
  '/admin/memberships': { element: <MembershipsPage />, permission: 'users.update' },
  '/customers': { element: <CustomersPage />, permission: CUSTOMER_VIEW_PERMISSIONS },
  '/properties': { element: <PropertiesPage />, permission: 'inventory.view.available' },
  '/deals': { element: <DealsPage />, permission: DEAL_VIEW_PERMISSIONS },
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
    const dealDetailMatch = normalizedPath.match(/^\/deals\/([0-9a-f-]+)$/i);
    if (dealDetailMatch) return { element: <DealDetailPage dealId={dealDetailMatch[1]} />, permission: DEAL_VIEW_PERMISSIONS };
    const customerDetailMatch = normalizedPath.match(/^\/customers\/([0-9a-f-]+)$/i);
    if (customerDetailMatch) return { element: <CustomerDetailPage customerId={customerDetailMatch[1]} />, permission: CUSTOMER_VIEW_PERMISSIONS };
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
