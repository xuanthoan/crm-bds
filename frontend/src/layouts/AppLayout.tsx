import type { ReactNode } from 'react';

import { logout } from '../features/auth/api';
import { can, clearSession, getCurrentUser, getRefreshToken } from '../features/auth/authStore';
import { navigateTo } from '../routes/AppRoutes';
import { LEAD_VIEW_PERMISSIONS } from '../features/leads/constants';

type AppLayoutProps = {
  children?: ReactNode;
  currentPath: string;
};

const adminItems = [
  { label: 'Người dùng', path: '/admin/users', permission: 'users.view' },
  { label: 'Vai trò', path: '/admin/roles', permission: 'roles.view' },
  { label: 'Quyền', path: '/admin/permissions', permission: 'permissions.view' },
  { label: 'Phòng ban', path: '/admin/departments', permission: 'settings.manage_master_data' },
  { label: 'Nhóm sale', path: '/admin/teams', permission: 'settings.manage_master_data' },
  { label: 'Phân bổ nhân sự', path: '/admin/memberships', permission: 'users.update' },
];

export function AppLayout({ children, currentPath }: AppLayoutProps) {
  const user = getCurrentUser();
  const visibleAdminItems = adminItems.filter((item) => can(item.permission));
  const canViewLeads = LEAD_VIEW_PERMISSIONS.some(can);
  const canViewTasks = ['lead_tasks.view.own', 'lead_tasks.view.team', 'lead_tasks.view.all'].some(can);
  const canViewAppointments = ['lead_appointments.view.own', 'lead_appointments.view.team', 'lead_appointments.view.all'].some(can);
  const canViewMyDashboard = ['dashboard.view.own', 'dashboard.view.team', 'dashboard.view.all'].some(can);
  const canViewTeamDashboard = ['dashboard.view.team', 'dashboard.view.all'].some(can);

  async function handleLogout() {
    const refreshToken = getRefreshToken();
    try {
      await logout(refreshToken);
    } catch {
      // Session is cleared locally even if the server-side revoke request fails.
    } finally {
      clearSession();
      navigateTo('/login');
    }
  }

  function renderLink(label: string, path: string) {
    return (
      <a
        href={path}
        className={currentPath === path || (path === '/leads' && /^\/leads\/[^/]+$/.test(currentPath)) ? 'active' : ''}
        onClick={(event: any) => {
          event.preventDefault();
          navigateTo(path);
        }}
      >
        {label}
      </a>
    );
  }

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="brand">CRM BDS</div>
        <nav>
          {(canViewMyDashboard || canViewTeamDashboard) && <div className="nav-section"><span>Dashboard</span>{canViewMyDashboard && <div>{renderLink('Tổng quan của tôi', '/dashboard/my-work')}</div>}{canViewTeamDashboard && <div>{renderLink('Tổng quan team', '/dashboard/team-work')}</div>}</div>}
          {canViewLeads && (
            <div className="nav-section">
              <span>CRM</span>
              <div>{renderLink('Khách tiềm năng', '/leads')}</div>
              <div>{renderLink('Lead quá hạn', '/leads/overdue')}</div>
              {canViewTasks && <><div>{renderLink('Công việc', '/tasks')}</div><div>{renderLink('Việc hôm nay', '/tasks/today')}</div><div>{renderLink('Việc quá hạn', '/tasks/overdue')}</div></>}
              {canViewAppointments && <><div>{renderLink('Lịch hẹn', '/appointments')}</div><div>{renderLink('Lịch hẹn hôm nay', '/appointments/today')}</div></>}
            </div>
          )}
          {visibleAdminItems.length > 0 && (
            <div className="nav-section">
              <span>Quản trị hệ thống</span>
              {visibleAdminItems.map((item) => <div key={item.path}>{renderLink(item.label, item.path)}</div>)}
            </div>
          )}
        </nav>
      </aside>
      <div className="content-shell">
        <header className="topbar">
          <div>
            <strong>{user?.full_name ?? 'Authenticated User'}</strong>
            <span>{user?.roles.join(', ')}</span>
          </div>
          <button type="button" onClick={handleLogout} className="secondary-button">
            Logout
          </button>
        </header>
        <main className="content-area">{children}</main>
      </div>
    </div>
  );
}
