import { useEffect, useState, type ReactNode } from 'react';

import { logout } from '../features/auth/api';
import { can, clearSession, getCurrentUser, getRefreshToken } from '../features/auth/authStore';
import { navigateTo } from '../routes/AppRoutes';
import { LEAD_VIEW_PERMISSIONS } from '../features/leads/constants';
import { CUSTOMER_VIEW_PERMISSIONS } from '../features/customers/constants';
import { DEAL_VIEW_PERMISSIONS } from '../features/deals/constants';
import { PROJECT_VIEW_PERMISSIONS } from '../features/projects/constants';
import { PROPERTY_VIEW_PERMISSIONS } from '../features/properties/constants';
import { BOOKING_VIEW_PERMISSIONS } from '../features/bookings/constants';
import { CONTRACT_VIEW_PERMISSIONS } from '../features/contracts/constants';
import { unreadCount } from '../features/notifications/api';

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
  const [notificationCount, setNotificationCount] = useState(0);
  useEffect(() => { if (can('notifications.view')) void unreadCount().then((r) => setNotificationCount(r.data.unread_count)).catch(() => setNotificationCount(0)); }, []);
  const visibleAdminItems = adminItems.filter((item) => can(item.permission));
  const canViewLeads = LEAD_VIEW_PERMISSIONS.some(can);
  const canViewCustomers = CUSTOMER_VIEW_PERMISSIONS.some(can);
  const canViewDeals = DEAL_VIEW_PERMISSIONS.some(can);
  const canViewProjects = PROJECT_VIEW_PERMISSIONS.some(can);
  const canViewProperties = PROPERTY_VIEW_PERMISSIONS.some(can);
  const canViewBookings = BOOKING_VIEW_PERMISSIONS.some(can);
  const canViewContracts = CONTRACT_VIEW_PERMISSIONS.some(can);

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
        className={currentPath === path || (path === '/customers' && /^\/customers\/[^/]+$/.test(currentPath)) || (path === '/leads' && /^\/leads\/[^/]+$/.test(currentPath)) || (path === '/deals' && /^\/deals\/[^/]+$/.test(currentPath)) || (path === '/projects' && /^\/projects\/[^/]+$/.test(currentPath)) || (path === '/properties' && /^\/properties\/[^/]+$/.test(currentPath)) || (path === '/bookings' && /^\/bookings\/[^/]+$/.test(currentPath)) || (path === '/contracts' && /^\/contracts\/[^/]+$/.test(currentPath)) ? 'active' : ''}
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
          <div className="nav-section"><span>Dashboard</span>{can('dashboard.view.own') || can('dashboard.view.team') || can('dashboard.view.all') ? <div>{renderLink('Tổng quan của tôi', '/dashboard/my-work')}</div> : null}{can('dashboard.view.team') || can('dashboard.view.all') ? <div>{renderLink('Tổng quan team', '/dashboard/team-work')}</div> : null}</div>
          {(canViewLeads || canViewCustomers || canViewDeals || canViewBookings || canViewContracts || can('tasks.view') || can('tasks.view_all')) && (
            <div className="nav-section">
              <span>Giao dịch CRM</span>
              {canViewLeads && <><div>{renderLink('Khách tiềm năng', '/leads')}</div><div>{renderLink('Lead quá hạn', '/leads/overdue')}</div></>}
              {canViewCustomers && <div>{renderLink('Khách hàng', '/customers')}</div>}
              {canViewDeals && <div>{renderLink('Giao dịch', '/deals')}</div>}
              {canViewBookings && <div>{renderLink('Booking / Giữ chỗ', '/bookings')}</div>}
              {canViewContracts && <div>{renderLink('Hợp đồng', '/contracts')}</div>}
              {(can('tasks.view') || can('tasks.view_all')) && <><div>{renderLink('Công việc', '/tasks')}</div><div>{renderLink('Việc hôm nay', '/tasks/today')}</div><div>{renderLink('Việc quá hạn', '/tasks/overdue')}</div></>}
              {(can('lead_appointments.view.own') || can('lead_appointments.view.team') || can('lead_appointments.view.all')) && <><div>{renderLink('Lịch hẹn', '/appointments')}</div><div>{renderLink('Lịch hẹn hôm nay', '/appointments/today')}</div></>}
            </div>
          )}
          {(canViewProjects || canViewProperties) && (
            <div className="nav-section">
              <span>Kho hàng</span>
              {canViewProjects && <div>{renderLink('Dự án', '/projects')}</div>}
              {canViewProperties && <div>{renderLink('Bất động sản', '/properties')}</div>}
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
          <button type="button" onClick={() => navigateTo('/notifications')} className="secondary-button">Thông báo {notificationCount > 0 ? `(${notificationCount})` : ''}</button>
          <button type="button" onClick={handleLogout} className="secondary-button">
            Logout
          </button>
        </header>
        <main className="content-area">{children}</main>
      </div>
    </div>
  );
}
